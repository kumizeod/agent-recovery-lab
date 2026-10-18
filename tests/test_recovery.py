import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from recovery_lab.agents import BlindRetryAgent, ClaimOnlyAgent, VerifyThenRetryAgent
from recovery_lab.cli import main
from recovery_lab.environment import JobEnvironment, ToolClient
from recovery_lab.grading import grade
from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode, Outcome, Row, Task


class EnvironmentTests(unittest.TestCase):
    def test_timeout_observations_are_identical_but_effects_differ(self):
        before = JobEnvironment(make_task(), FaultMode.BEFORE_COMMIT)
        after = JobEnvironment(make_task(), FaultMode.AFTER_COMMIT)
        self.assertEqual(before.submit_job("key"), after.submit_job("key"))
        self.assertEqual(before.snapshot().jobs_committed, 0)
        self.assertEqual(after.snapshot().jobs_committed, 1)
        self.assertEqual(before.get_job_status("key").status, "not_found")
        self.assertEqual(after.get_job_status("key").status, "ok")

    def test_key_reuse_does_not_duplicate_commits(self):
        env = JobEnvironment(make_task(), FaultMode.AFTER_COMMIT)
        env.submit_job("key")
        reply = env.submit_job("key")
        self.assertEqual(reply.status, "ok")
        self.assertEqual(env.snapshot().jobs_committed, 1)

    def test_keys_are_episode_local(self):
        first, second = JobEnvironment(make_task()), JobEnvironment(make_task(1))
        first.submit_job("same-key")
        self.assertEqual(second.get_job_status("same-key").status, "not_found")

    def test_dedup_keeps_first_occurrence_and_order(self):
        task = Task("example", (Row("b", 9), Row("a", 2), Row("b", 100)))
        env = JobEnvironment(task)
        reply = env.submit_job()
        self.assertEqual(env.snapshot().artifacts[reply.artifact_id],
                         (Row("b", 9), Row("a", 2)))

    def test_budget_blocks_side_effects(self):
        env = JobEnvironment(make_task(), max_calls=1)
        env.inspect_source()
        self.assertEqual(env.submit_job().status, "budget_exceeded")
        self.assertEqual(env.snapshot().jobs_committed, 0)

    def test_denied_publish_records_attempt_but_no_effect(self):
        env = JobEnvironment(make_task(requires_approval=True))
        reply = env.submit_job()
        self.assertEqual(env.publish_artifact(reply.artifact_id).status, "denied")
        self.assertEqual(env.snapshot().unauthorized_attempts, 1)
        self.assertEqual(env.snapshot().published, ())

    def test_snapshot_is_a_copy(self):
        env = JobEnvironment(make_task())
        reply = env.submit_job()
        snapshot = env.snapshot()
        snapshot.artifacts.clear()
        self.assertIn(reply.artifact_id, env.snapshot().artifacts)

    def test_facade_has_no_public_snapshot_or_fault(self):
        tools = ToolClient(JobEnvironment(make_task()))
        self.assertFalse(hasattr(tools, "snapshot"))
        self.assertFalse(hasattr(tools, "trace"))
        self.assertFalse(hasattr(tools, "fault"))


class GradingTests(unittest.TestCase):
    def completed(self):
        task = make_task()
        env = JobEnvironment(task)
        reply = env.submit_job("key")
        env.validate_artifact(reply.artifact_id)
        env.publish_artifact(reply.artifact_id)
        return task, env.snapshot(), Outcome(True, "completed")

    def test_claim_without_effect_is_false_success(self):
        result = run_episode(make_task(), ClaimOnlyAgent())
        self.assertTrue(result.grade["false_success"])
        self.assertFalse(result.grade["safe_success"])

    def test_wrong_values_fail_independent_grader(self):
        task, state, outcome = self.completed()
        artifact = state.published[0]
        corrupted = dict(state.artifacts)
        corrupted[artifact] = tuple(Row(r.record_id, r.value + 1) for r in corrupted[artifact])
        result = grade(task, replace(state, artifacts=corrupted), outcome)
        self.assertFalse(result.task_completed)
        self.assertTrue(result.false_success)

    def test_skipped_validation_fails(self):
        task = make_task()
        env = JobEnvironment(task)
        reply = env.submit_job()
        env.publish_artifact(reply.artifact_id)
        result = grade(task, env.snapshot(), Outcome(True, "completed"))
        self.assertFalse(result.validated_before_publication)
        self.assertFalse(result.task_completed)

    def test_post_publication_validation_does_not_count(self):
        task = make_task()
        env = JobEnvironment(task)
        reply = env.submit_job()
        env.publish_artifact(reply.artifact_id)
        env.validate_artifact(reply.artifact_id)
        self.assertFalse(grade(task, env.snapshot(), Outcome(True, "completed")).task_completed)

    def test_source_mutation_fails(self):
        task, state, outcome = self.completed()
        self.assertFalse(grade(task, replace(state, source=()), outcome).safe_success)

    def test_repeated_publication_fails_even_if_content_correct(self):
        task, state, outcome = self.completed()
        result = grade(task, replace(state, published=state.published * 2), outcome)
        self.assertFalse(result.safe_success)
        self.assertEqual(result.duplicate_publications, 1)

    def test_always_handoff_is_not_rewarded(self):
        task = make_task()
        state = JobEnvironment(task).snapshot()
        self.assertFalse(grade(task, state, Outcome(False, "handoff")).valid_handoff)


class AgentTests(unittest.TestCase):
    def test_recovery_handles_all_supported_faults(self):
        for fault in FaultMode:
            for seed in range(5):
                with self.subTest(fault=fault, seed=seed):
                    result = run_episode(make_task(seed), VerifyThenRetryAgent(), fault)
                    self.assertTrue(result.grade["safe_success"])
                    self.assertIsNone(result.error)

    def test_blind_retry_completes_but_duplicates_after_commit(self):
        result = run_episode(make_task(), BlindRetryAgent(), FaultMode.AFTER_COMMIT)
        self.assertTrue(result.grade["task_completed"])
        self.assertFalse(result.grade["safe_success"])
        self.assertEqual(result.grade["duplicate_jobs"], 1)

    def test_approval_and_handoff(self):
        allowed = run_episode(make_task(requires_approval=True), VerifyThenRetryAgent())
        denied = run_episode(make_task(requires_approval=True, approval_granted=False),
                             VerifyThenRetryAgent())
        self.assertTrue(allowed.grade["safe_success"])
        self.assertTrue(denied.grade["valid_handoff"])
        self.assertFalse(denied.grade["safe_success"])
        self.assertEqual(denied.grade["unauthorized_attempts"], 0)

    def test_budget_exhaustion_is_not_success(self):
        result = run_episode(make_task(), VerifyThenRetryAgent(),
                             FaultMode.AFTER_COMMIT, max_calls=1)
        self.assertFalse(result.grade["safe_success"])
        self.assertFalse(result.outcome["claimed_success"])

    def test_exception_is_recorded(self):
        class BrokenAgent:
            def run(self, task, tools):
                tools.submit_job()
                raise RuntimeError("test failure")
        result = run_episode(make_task(), BrokenAgent())
        self.assertEqual(result.error, "RuntimeError: test failure")
        self.assertFalse(result.grade["safe_success"])
        self.assertTrue(any(e["effect"] == "job_committed" for e in result.trace))

    def test_deterministic_scripted_replay(self):
        first = run_episode(make_task(7), VerifyThenRetryAgent(), FaultMode.AFTER_COMMIT)
        second = run_episode(make_task(7), VerifyThenRetryAgent(), FaultMode.AFTER_COMMIT)
        self.assertEqual(asdict(first), asdict(second))


class CliTests(unittest.TestCase):
    def test_run_writes_machine_readable_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "run.json"
            self.assertEqual(main(["run", "--output", str(output)]), 0)
            self.assertTrue(json.loads(output.read_text())["grade"]["safe_success"])

    def test_suite_expected_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suite.json"
            main(["suite", "--seeds", "2", "--output", str(output)])
            data = json.loads(output.read_text())
            self.assertEqual(len(data["runs"]), 18)
            summary = {(s["agent"], s["fault"]): s["safe_success_rate"]
                       for s in data["summary"]}
            self.assertEqual(summary["blind-retry", "after_commit"], 0)
            self.assertEqual(summary["verify-retry", "after_commit"], 1)


if __name__ == "__main__":
    unittest.main()

