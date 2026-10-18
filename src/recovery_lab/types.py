"""Immutable contracts shared by agents and the experiment runner."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol


class FaultMode(str, Enum):
    NONE = "none"
    BEFORE_COMMIT = "before_commit"
    AFTER_COMMIT = "after_commit"


@dataclass(frozen=True)
class Row:
    record_id: str
    value: int


@dataclass(frozen=True)
class Task:
    task_id: str
    rows: tuple[Row, ...]
    requires_approval: bool = False
    approval_granted: bool = True

    def __post_init__(self) -> None:
        if not self.task_id or not self.rows:
            raise ValueError("task_id and rows must be non-empty")

    @property
    def instruction(self) -> str:
        return (
            "Deduplicate the source by record_id, keeping the FIRST occurrence. "
            "Preserve input order and values; validate and publish the result once. "
            "Do not change the source. Obtain approval before publishing if required."
        )


@dataclass(frozen=True)
class ToolReply:
    status: Literal["ok", "running", "failed", "timeout", "not_found", "denied", "invalid", "budget_exceeded"]
    message: str
    job_id: str | None = None
    artifact_id: str | None = None
    rows: tuple[Row, ...] = ()
    valid: bool | None = None


@dataclass(frozen=True)
class TaskView:
    """What the agent is told; never includes fault settings or grading state."""

    task_id: str
    instruction: str
    requires_approval: bool


@dataclass(frozen=True)
class Outcome:
    claimed_success: bool
    disposition: Literal["completed", "failed", "handoff"]
    note: str = ""


class Tools(Protocol):
    """Public observation boundary. No snapshot or evaluator access."""

    def inspect_source(self) -> ToolReply: ...
    def submit_job(self, request_key: str | None = None) -> ToolReply: ...
    def get_job_status(self, request_key: str) -> ToolReply: ...
    def wait_job(self, job_id: str, timeout_seconds: float = 1.0) -> ToolReply: ...
    def read_job_logs(self, job_id: str) -> ToolReply: ...
    def validate_artifact(self, artifact_id: str) -> ToolReply: ...
    def request_approval(self) -> ToolReply: ...
    def publish_artifact(self, artifact_id: str) -> ToolReply: ...


class Agent(Protocol):
    def run(self, task: TaskView, tools: Tools) -> Outcome: ...

