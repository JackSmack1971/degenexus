#!/usr/bin/env python3
"""Print a short Claude Code session-start reminder for this repository."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    print(
        "DegenExus session reminder: run the turn-start GitHub scans when applicable, "
        "trust `.claude/rules/02-agent-synergy.md` for specialist routing, and keep "
        "verification evidence exact."
    )
    print(f"Repository: {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
