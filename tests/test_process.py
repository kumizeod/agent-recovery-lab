from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from recovery_lab.agents import BlindRetryAgent, VerifyThenRetryAgent
from recovery_lab.csv_io import read_csv
from recovery_lab.grading import grade
from recovery_lab.process_environment import ProcessEnvironment
from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode, Outcome, Row


class ProcessTests(unittest.TestCase):
    def test_real_workers_across_faults_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            for fault in FaultMode:
                directory = Path(temporary) / fault.value
                result = run_episode(make_task(7), VerifyThenRetryAgent(), fault, workdir=directory)
                self.assertIsNone(result.error)
                self.assertTrue(result.grade["safe_success"], result)
                self.assertEqual(read_csv(directory / "source.csv"), make_task(7).rows)
                self.assertTrue((directory / "published/publication-001.csv").is_file())
                self.assertIn("Completed", (directory / "logs/job-001.log").read_text())

    def test_blind_retry_creates_two_background_jobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "episode"
            result = run_episode(make_task(), BlindRetryAgent(), FaultMode.AFTER_COMMIT,
                                 workdir=directory)
            self.assertEqual(result.grade["duplicate_jobs"], 1)
            self.assertFalse(result.grade["safe_success"])
            self.assertEqual(len(list((directory / "logs").glob("*.log"))), 2)

    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileExistsError):
                ProcessEnvironment(make_task(), Path(temporary))

    def test_failure_logs_and_source_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = ProcessEnvironment(make_task(), Path(temporary) / "episode")
            try:
                env.source_path.write_text("wrong,header\na,b\n")
                reply = env.submit_job("key")
                reply = env.wait_job(reply.job_id, 3)
                self.assertEqual(reply.status, "failed")
                self.assertIn("Unexpected CSV schema", env.read_job_logs("job-001").message)
                self.assertFalse(grade(make_task(), env.snapshot(), Outcome(False, "failed")).source_preserved)
            finally:
                env.close()

    def test_published_file_tampering_fails_grader(self):
        with tempfile.TemporaryDirectory() as temporary:
            task = make_task()
            env = ProcessEnvironment(task, Path(temporary) / "episode")
            try:
                reply = env.submit_job("key")
                reply = env.wait_job(reply.job_id, 3)
                self.assertEqual(reply.status, "ok")
                env.validate_artifact(reply.artifact_id)
                env.publish_artifact(reply.artifact_id)
                (env.workdir / "published/publication-001.csv").write_text("record_id,value\nwrong,1\n")
                self.assertFalse(grade(task, env.snapshot(), Outcome(True, "completed")).safe_success)
            finally:
                env.close()

    def test_close_reaps_running_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = ProcessEnvironment(make_task(), Path(temporary) / "episode")
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
            env._processes["job-test"] = process
            env._streams["job-test"] = (env.workdir / "logs/test.log").open("wb")
            env._started["job-test"] = time.monotonic()
            env.close()
            self.assertIsNotNone(process.poll())

    def test_cooperative_timeout_terminates_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = ProcessEnvironment(make_task(), Path(temporary) / "episode", job_timeout=0.001)
            process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
            env._processes["job-001"] = process
            env._streams["job-001"] = (env.workdir / "logs/test.log").open("wb")
            env._started["job-001"] = time.monotonic() - 1
            env._jobs["job-001"] = "artifact-001"
            try:
                reply = env.wait_job("job-001", 1)
                self.assertEqual(reply.status, "failed")
                self.assertIn("timeout", reply.message)
                self.assertIsNotNone(process.poll())
            finally:
                env.close()

    def test_csv_schema_and_empty_input_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.csv"
            for content in ("a,b\n1,2\n", "record_id,value\n", "record_id,value\na,x\n",
                            "record_id,value\na,1,extra\n"):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    read_csv(path)

    def test_external_csv_cli_does_not_edit_original(self):
        from recovery_lab.cli import main
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            source.write_text("record_id,value\nb,9\na,2\nb,100\n")
            original = source.read_bytes()
            self.assertEqual(main(["run", "--backend", "process", "--csv", str(source),
                                   "--workdir", str(root / "episode"), "--output", str(root / "result.json")]), 0)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(read_csv(root / "episode/published/publication-001.csv"),
                             (Row("b", 9), Row("a", 2)))

