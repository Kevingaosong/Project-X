#!/usr/bin/env python3
"""Run the Project X Agent from a source checkout without installing it."""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from project_x_agent.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--repo-root", str(REPOSITORY_ROOT), *sys.argv[1:]]))
