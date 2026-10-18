from dataclasses import asdict, dataclass
from typing import Any
from pathlib import Path

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
    backend: str = "memory"
    workdir: str | None = None
    agent_trace: dict[str, Any] | None = None


def run_episode(task: Task, agent: Agent, fault: FaultMode = FaultMode.NONE,
                max_calls: int = 24, *, workdir: Path | None = None,
                job_timeout: float = 15.0) -> RunResult:
    if workdir is None:
        env = JobEnvironment(task, fault, max_calls)
    else:
        from recovery_lab.process_environment import ProcessEnvironment
        env = ProcessEnvironment(task, workdir, fault, max_calls, job_timeout)
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
    finally:
        # Stop/reap on success, exceptions and KeyboardInterrupt.
        env.close()
    result = RunResult(task.task_id, type(agent).__name__, fault.value, asdict(outcome),
                       asdict(grade(task, env.snapshot(), outcome)), env.trace(), error,
                       "process" if workdir is not None else "memory",
                       str(workdir.resolve()) if workdir is not None else None,
                       agent.public_trace() if hasattr(agent, "public_trace") else None)
    return result

