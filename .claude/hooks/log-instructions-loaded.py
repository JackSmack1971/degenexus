#!/usr/bin/env python3
"""Log redacted Claude Code InstructionsLoaded hook events."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LOCAL_DIR = ROOT / ".claude" / "local"
LOG_PATH = LOCAL_DIR / "instructions-loaded.jsonl"
MAX_LIST_ITEMS = 50

SENSITIVE_KEYS = {
    "content",
    "prompt",
    "text",
    "message",
    "messages",
    "transcript",
    "conversation",
    "api_key",
    "authorization",
    "token",
    "secret",
    "password",
}


def _safe_path(value: str) -> str:
    try:
        path = Path(value)
    except TypeError:
        return "<non-path>"
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return path.name
    return value


def _redact(value: Any, key: str = "") -> Any:
    lowered = key.lower()
    if any(marker in lowered for marker in SENSITIVE_KEYS):
        return "<redacted>"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items() if str(k).lower() not in SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_redact(item, key) for item in value[:MAX_LIST_ITEMS]]
    if isinstance(value, str):
        if "\n" in value or len(value) > 240:
            return f"<redacted-string:{len(value)} chars>"
        if any(marker in lowered for marker in ("file", "path", "source", "memory", "instruction")):
            return _safe_path(value)
    return value


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {"unparsed_event_bytes": len(raw)}
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "InstructionsLoaded",
        "cwd": _safe_path(os.getcwd()),
        "summary": _redact(event),
    }
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
