"""Local CSV experiments with scripted agents or an explicit LLM endpoint."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from recovery_lab.agents import AGENTS
from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode, Task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one episode (LLM agent uses a remote/local API)")
    run.add_argument("--agent", choices=[*AGENTS, "llm"], default="verify-retry")
    run.add_argument("--fault", choices=[f.value for f in FaultMode], default="after_commit")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--max-calls", type=int, default=24)
    run.add_argument("--require-approval", action="store_true")
    run.add_argument("--deny-approval", action="store_true")
    run.add_argument("--output", type=Path)
    run.add_argument("--backend", choices=["memory", "process"], default="memory")
    run.add_argument("--csv", type=Path, help="Input CSV; requires --backend process")
    run.add_argument("--workdir", type=Path, help="New episode directory; must not exist")
    run.add_argument("--job-timeout", type=float, default=15.0)
    run.add_argument("--max-turns", type=int, default=16)
    suite = sub.add_parser("suite", help="Compare scripted controls; not a model benchmark")
    suite.add_argument("--seeds", type=int, default=3)
    suite.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.max_calls < 1:
            parser.error("--max-calls must be positive")
        task = make_task(args.seed, args.require_approval or args.deny_approval,
                         not args.deny_approval)
        if args.backend == "memory" and (args.csv or args.workdir):
            parser.error("--csv and --workdir require --backend process")
        try:
            if args.csv:
                from recovery_lab.csv_io import read_csv
                if args.output and args.output.resolve() == args.csv.resolve():
                    parser.error("--output must not overwrite input CSV")
                task = Task("csv-deduplicate", read_csv(args.csv), task.requires_approval,
                            task.approval_granted)
            if args.agent == "llm":
                from recovery_lab.llm_agent import LLMAgent, LLMConfig
                agent = LLMAgent(LLMConfig.from_env(max_turns=args.max_turns,
                                                  max_tool_calls=args.max_calls))
            else:
                agent = AGENTS[args.agent]()
            directory = None
            if args.backend == "process":
                directory = args.workdir or Path("outputs") / ("episode-" + uuid4().hex[:12])
            result = run_episode(task, agent, FaultMode(args.fault), args.max_calls,
                                 workdir=directory, job_timeout=args.job_timeout)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        payload = asdict(result)
    else:
        if args.seeds < 1:
            parser.error("--seeds must be positive")
        runs = [asdict(run_episode(make_task(seed), agent(), fault))
                for seed in range(args.seeds) for agent in AGENTS.values() for fault in FaultMode]
        payload = {"scope": "scripted controls, one task family", "runs": runs,
                   "summary": [{"agent": name, "fault": fault.value,
                                "episodes": args.seeds,
                                "safe_success_rate": sum(r["grade"]["safe_success"] for r in runs
                                    if r["agent"] == cls.__name__ and r["fault"] == fault.value) / args.seeds}
                               for name, cls in AGENTS.items() for fault in FaultMode]}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(args.output)
    else:
        print(rendered, end="")
    # CLI completion is distinct from task success; inspect grade in the JSON.
    return 0

