"""Scripted controls, not LLMs and not learned recovery policies."""

from recovery_lab.types import Outcome, TaskView, Tools


def _finish(task: TaskView, tools: Tools, artifact_id: str | None) -> Outcome:
    if artifact_id is None:
        return Outcome(False, "failed", "No confirmed artifact")
    validation = tools.validate_artifact(artifact_id)
    if validation.status != "ok" or validation.valid is not True:
        return Outcome(False, "failed", "Artifact not validated")
    if task.requires_approval:
        approval = tools.request_approval()
        if approval.status == "denied":
            return Outcome(False, "handoff", "Operator denied publication")
        if approval.status != "ok":
            return Outcome(False, "failed", "Approval unavailable")
    reply = tools.publish_artifact(artifact_id)
    return Outcome(reply.status == "ok", "completed" if reply.status == "ok" else "failed",
                   reply.message)


class BlindRetryAgent:
    """Retries a timed-out write without a stable idempotency key."""

    def run(self, task: TaskView, tools: Tools) -> Outcome:
        reply = tools.submit_job()
        if reply.status == "timeout":
            reply = tools.submit_job()
        return _finish(task, tools, reply.artifact_id if reply.status == "ok" else None)


class VerifyThenRetryAgent:
    """Uses the contract: inspect by key, and reuse that key if retrying."""

    def run(self, task: TaskView, tools: Tools) -> Outcome:
        request_key = f"{task.task_id}:deduplicate:v1"
        reply = tools.submit_job(request_key)
        if reply.status == "timeout":
            reply = tools.get_job_status(request_key)
            if reply.status == "not_found":
                reply = tools.submit_job(request_key)
        return _finish(task, tools, reply.artifact_id if reply.status == "ok" else None)


class ClaimOnlyAgent:
    """Negative control: claims completion without doing any work."""

    def run(self, task: TaskView, tools: Tools) -> Outcome:
        return Outcome(True, "completed", "Everything is done")


AGENTS = {"blind-retry": BlindRetryAgent, "verify-retry": VerifyThenRetryAgent,
          "claim-only": ClaimOnlyAgent}

