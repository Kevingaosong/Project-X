from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .agent import ProjectXAgent
from .executor import MockCodexExecutor
from .publisher import MockGitPublisher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project X Agent Phase 3 mock control loop")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--watch", action="store_true", help="poll continuously; default is one scan")
    parser.add_argument("--interval", type=float, default=60.0, help="watch interval in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    agent = ProjectXAgent(
        tasks_dir=root / "tasks",
        results_dir=root / "results",
        executor=MockCodexExecutor(),
        publisher=MockGitPublisher(),
    )

    if args.watch:
        try:
            agent.watch(interval_seconds=args.interval)
        except KeyboardInterrupt:
            return 130
        return 0

    summary = agent.scan_once()
    print(json.dumps(asdict(summary), sort_keys=True))
    return 0
