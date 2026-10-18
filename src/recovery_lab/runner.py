from dataclasses import asdict, dataclass
from typing import Any

from recovery_lab.environment import JobEnvironment, ToolClient
from recovery_lab.grading import grade
from recovery_lab.types import Agent, FaultMode, Outcome, Task, TaskView


@dataclass(frozen=True)
class RunResult:
    task_id: str
    agent: str
    fault: str
    outcome: dict[str, Any]
    grade: dict[str, Any]
    trace: list[dict[str, Any]]
    error: str | None


def run_episode(task: Task, agent: Agent, fault: FaultMode = FaultMode.NONE,
                max_calls: int = 24) -> RunResult:
    env = JobEnvironment(task, fault, max_calls)
    view = TaskView(task.task_id, task.instruction, task.requires_approval)
    error = None
    try:
        outcome = agent.run(view, ToolClient(env))
        if not isinstance(outcome, Outcome):
            raise TypeError("Agent must return Outcome")
    except Exception as exc:
        # Infrastructure/agent exceptions are recorded, never silently dropped.
        error = f"{type(exc).__name__}: {exc}"
        outcome = Outcome(False, "failed", "Agent raised an exception")
    return RunResult(task.task_id, type(agent).__name__, fault.value, asdict(outcome),
                     asdict(grade(task, env.snapshot(), outcome)), env.trace(), error)

