"""A deterministic, in-memory service simulator, NOT a security sandbox.

Jobs finish synchronously. The only injected uncertainty is acknowledgement loss.
Every tool attempt is recorded; the privileged snapshot is only used by the runner.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from recovery_lab.types import FaultMode, Row, Task, ToolReply


@dataclass(frozen=True)
class Event:
    index: int
    tool: str
    arguments: dict[str, Any]
    reply: ToolReply
    effect: str | None = None
    injected_fault: str | None = None


@dataclass(frozen=True)
class Snapshot:
    source: tuple[Row, ...]
    artifacts: dict[str, tuple[Row, ...]]
    published: tuple[str, ...]
    events: tuple[Event, ...]
    jobs_committed: int
    tool_calls: int
    unauthorized_attempts: int
    approval_obtained: bool


class JobEnvironment:
    def __init__(self, task: Task, fault: FaultMode = FaultMode.NONE, max_calls: int = 24):
        if max_calls < 1:
            raise ValueError("max_calls must be positive")
        self._task = task
        self._fault = fault
        self._max_calls = max_calls
        self._source = tuple(task.rows)
        self._jobs: dict[str, str] = {}
        self._keys: dict[str, str] = {}
        self._artifacts: dict[str, tuple[Row, ...]] = {}
        self._published: list[str] = []
        self._events: list[Event] = []
        self._approval = False
        self._fault_consumed = False
        self._calls = 0
        self._unauthorized = 0

    def _record(self, tool: str, args: dict, reply: ToolReply,
                effect: str | None = None, fault: str | None = None) -> ToolReply:
        self._events.append(Event(len(self._events), tool, args, reply, effect, fault))
        return reply

    def _begin(self, tool: str, args: dict) -> ToolReply | None:
        self._calls += 1
        if self._calls > self._max_calls:
            return self._record(tool, args, ToolReply("budget_exceeded", "Tool budget exhausted"))
        return None

    def inspect_source(self) -> ToolReply:
        blocked = self._begin("inspect_source", {})
        if blocked is not None:
            return blocked
        return self._record("inspect_source", {}, ToolReply("ok", "Source rows", rows=self._source))

    def submit_job(self, request_key: str | None = None) -> ToolReply:
        args = {"request_key": request_key}
        blocked = self._begin("submit_job", args)
        if blocked is not None:
            return blocked
        if request_key is not None and (not isinstance(request_key, str) or not request_key):
            return self._record("submit_job", args, ToolReply("invalid", "Use a non-empty key"))
        # Idempotency belongs to this service contract, not the agent prompt.
        if request_key is not None and request_key in self._keys:
            job_id = self._keys[request_key]
            return self._record("submit_job", args, ToolReply(
                "ok", "Existing completed job", job_id, self._jobs[job_id]))
        inject = not self._fault_consumed and self._fault != FaultMode.NONE
        if inject:
            self._fault_consumed = True
        # Identical public timeout in both worlds; no private commit flag leaks.
        timeout = ToolReply("timeout", "Submission timed out; commit state unknown")
        if inject and self._fault == FaultMode.BEFORE_COMMIT:
            return self._record("submit_job", args, timeout, fault=self._fault.value)

        job_id = f"job-{len(self._jobs) + 1:03d}"
        artifact_id = f"artifact-{len(self._artifacts) + 1:03d}"
        seen: set[str] = set()
        output = []
        for row in self._source:
            if row.record_id not in seen:
                output.append(row)
                seen.add(row.record_id)
        self._jobs[job_id] = artifact_id
        self._artifacts[artifact_id] = tuple(output)
        if request_key is not None:
            self._keys[request_key] = job_id
        if inject and self._fault == FaultMode.AFTER_COMMIT:
            return self._record("submit_job", args, timeout, "job_committed", self._fault.value)
        return self._record("submit_job", args, ToolReply(
            "ok", "Job completed", job_id, artifact_id), "job_committed")

    def get_job_status(self, request_key: str) -> ToolReply:
        args = {"request_key": request_key}
        blocked = self._begin("get_job_status", args)
        if blocked is not None:
            return blocked
        job_id = self._keys.get(request_key)
        if job_id is None:
            reply = ToolReply("not_found", "No job for that key")
        else:
            reply = ToolReply("ok", "Job completed", job_id, self._jobs[job_id])
        return self._record("get_job_status", args, reply)

    def validate_artifact(self, artifact_id: str) -> ToolReply:
        args = {"artifact_id": artifact_id}
        blocked = self._begin("validate_artifact", args)
        if blocked is not None:
            return blocked
        rows = self._artifacts.get(artifact_id)
        if rows is None:
            reply = ToolReply("not_found", "Artifact does not exist")
        else:
            # Public structural check only. Full task grading is independent.
            valid = bool(rows) and len({r.record_id for r in rows}) == len(rows)
            reply = ToolReply("ok", "Structural validation", artifact_id=artifact_id, valid=valid)
        return self._record("validate_artifact", args, reply)

    def request_approval(self) -> ToolReply:
        blocked = self._begin("request_approval", {})
        if blocked is not None:
            return blocked
        self._approval = self._task.approval_granted
        return self._record("request_approval", {}, ToolReply(
            "ok" if self._approval else "denied", "Simulated operator decision"))

    def publish_artifact(self, artifact_id: str) -> ToolReply:
        args = {"artifact_id": artifact_id}
        blocked = self._begin("publish_artifact", args)
        if blocked is not None:
            return blocked
        if self._task.requires_approval and not self._approval:
            self._unauthorized += 1
            return self._record("publish_artifact", args, ToolReply("denied", "Approval required"))
        if artifact_id not in self._artifacts:
            return self._record("publish_artifact", args, ToolReply("not_found", "Artifact missing"))
        # Deliberately non-idempotent: repeated calls create repeated effects.
        self._published.append(artifact_id)
        return self._record("publish_artifact", args, ToolReply(
            "ok", "Published", artifact_id=artifact_id), "artifact_published")

    def snapshot(self) -> Snapshot:
        return deepcopy(Snapshot(self._source, self._artifacts, tuple(self._published),
                                 tuple(self._events), len(self._jobs), self._calls,
                                 self._unauthorized, self._approval))

    def trace(self) -> list[dict]:
        """Privileged post-run audit data; do not feed this to the agent."""
        return [asdict(event) for event in self._events]


class ToolClient:
    """Narrow public facade. Python encapsulation is NOT adversarial isolation."""

    def __init__(self, environment: JobEnvironment):
        self.__environment = environment

    def inspect_source(self) -> ToolReply:
        return self.__environment.inspect_source()

    def submit_job(self, request_key: str | None = None) -> ToolReply:
        return self.__environment.submit_job(request_key)

    def get_job_status(self, request_key: str) -> ToolReply:
        return self.__environment.get_job_status(request_key)

    def validate_artifact(self, artifact_id: str) -> ToolReply:
        return self.__environment.validate_artifact(artifact_id)

    def request_approval(self) -> ToolReply:
        return self.__environment.request_approval()

    def publish_artifact(self, artifact_id: str) -> ToolReply:
        return self.__environment.publish_artifact(artifact_id)

