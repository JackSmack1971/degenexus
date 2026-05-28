#!/usr/bin/env python3
"""Append Claude Code subagent lifecycle events to a local JSONL audit log."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / ".claude" / "local" / "subagent-events.jsonl"


def git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    payload_text = sys.stdin.read().strip()
    payload = json.loads(payload_text) if payload_text else {}
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "hook_event_name": payload.get("hook_event_name") or os.environ.get("CLAUDE_HOOK_EVENT"),
        "agent_type": payload.get("agent_type") or payload.get("subagent_type"),
        "cwd": str(ROOT),
        "git_sha": git_value("rev-parse", "HEAD"),
        "changed_files": git_value("diff", "--name-only").splitlines(),
        "scope": payload.get("prompt") or payload.get("description") or payload.get("scope"),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
