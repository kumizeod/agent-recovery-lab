"""Small JSON-producing CLI. All outputs are local; no API keys needed."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from recovery_lab.agents import AGENTS
from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one offline episode")
    run.add_argument("--agent", choices=AGENTS, default="verify-retry")
    run.add_argument("--fault", choices=[f.value for f in FaultMode], default="after_commit")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--max-calls", type=int, default=24)
    run.add_argument("--require-approval", action="store_true")
    run.add_argument("--deny-approval", action="store_true")
    run.add_argument("--output", type=Path)
    suite = sub.add_parser("suite", help="Compare scripted controls; not a model benchmark")
    suite.add_argument("--seeds", type=int, default=3)
    suite.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.max_calls < 1:
            parser.error("--max-calls must be positive")
        task = make_task(args.seed, args.require_approval or args.deny_approval,
                         not args.deny_approval)
        result = run_episode(task, AGENTS[args.agent](), FaultMode(args.fault), args.max_calls)
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

