#!/usr/bin/env python3
"""Remind Claude Code sessions that project hook paths are CWD independent."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cwd = Path(os.getcwd())
    try:
        display = cwd.resolve().relative_to(ROOT)
    except ValueError:
        display = cwd
    print(
        "cwd changed to "
        f"{display}; project hooks should continue to use $CLAUDE_PROJECT_DIR/.claude/hooks/*.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
