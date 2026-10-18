"""Run from the repository root after installation: python examples/custom_agent.py"""

from dataclasses import asdict
import json

from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode, Outcome, TaskView, Tools


class StopOnTimeoutAgent:
    """A deliberately conservative baseline: never retries a timed-out submission."""

    def run(self, task: TaskView, tools: Tools) -> Outcome:
        reply = tools.submit_job(f"{task.task_id}:example")
        if reply.status != "ok":
            return Outcome(False, "handoff", "Submission outcome needs investigation")
        # For a real implementation, inspect/validate, obtain approval if needed,
        # publish, and only claim success based on tool evidence.
        return Outcome(False, "failed", "Example deliberately stops before publication")


if __name__ == "__main__":
    print(json.dumps(asdict(run_episode(make_task(), StopOnTimeoutAgent(),
                                       FaultMode.AFTER_COMMIT)), indent=2))

