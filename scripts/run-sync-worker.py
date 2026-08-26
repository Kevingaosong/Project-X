#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one safe Project X Git/Codex sync cycle")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--codex-binary", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    sys.path.insert(0, str(root / "src"))
    from project_x_agent.worker import ProjectXWorker

    try:
        result = ProjectXWorker(repo_root=root, codex_binary=args.codex_binary).run_once()
    except Exception as exc:
        result = {"status": "failed", "error_type": type(exc).__name__}
        print(json.dumps(result, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
