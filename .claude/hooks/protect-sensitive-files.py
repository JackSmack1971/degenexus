#!/usr/bin/env python3
"""Block Claude Code tool calls that target protected local files."""

from __future__ import annotations

import fnmatch
import json
import re
import shlex
import sys
from pathlib import PurePosixPath
from typing import Any

PROTECTED_PATTERNS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "secrets/**",
    "**/secrets/**",
    "*.pem",
    "**/*.pem",
    "*.key",
    "**/*.key",
    "*credential*.json",
    "**/*credential*.json",
    "*credentials*.json",
    "**/*credentials*.json",
    "*.db",
    "**/*.db",
    "*.db-wal",
    "**/*.db-wal",
    "*.db-shm",
    "**/*.db-shm",
)
BASH_FILE_FLAGS = {"cat", "cp", "mv", "rm", "touch", "chmod", "chown", "ln", "less", "more", "head", "tail", "sed", "awk"}
REDIRECT_RE = re.compile(r"(?:^|\s)(?:>|>>|<)\s*([^\s;&|]+)")


def normalize_path(value: str) -> str:
    path = value.strip().strip('"\'')
    while path.startswith("./"):
        path = path[2:]
    return PurePosixPath(path).as_posix()


def is_protected(path: str) -> bool:
    normalized = normalize_path(path)
    basename = PurePosixPath(normalized).name
    return any(
        fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(basename, pattern)
        for pattern in PROTECTED_PATTERNS
    )


def iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        found: list[str] = []
        for nested in value.values():
            found.extend(iter_strings(nested))
        return found
    if isinstance(value, list):
        found = []
        for nested in value:
            found.extend(iter_strings(nested))
        return found
    return []


def candidate_paths(tool_name: str, tool_input: dict[str, Any]) -> set[str]:
    candidates: set[str] = set()
    for key in ("file_path", "path", "filename", "target_file", "target_path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            candidates.add(value)
    if tool_name == "MultiEdit":
        for edit in tool_input.get("edits", []) or []:
            if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
                candidates.add(str(edit["file_path"]))
    if tool_name == "Bash":
        command = str(tool_input.get("command") or tool_input.get("cmd") or "")
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        for index, part in enumerate(parts):
            if part in BASH_FILE_FLAGS and index + 1 < len(parts):
                candidates.add(parts[index + 1])
            elif any(part.endswith(suffix) for suffix in (".pem", ".key", ".db", ".db-wal", ".db-shm")):
                candidates.add(part)
            elif PurePosixPath(part).name.startswith(".env") or "secrets/" in part:
                candidates.add(part)
        candidates.update(match.group(1) for match in REDIRECT_RE.finditer(command))
    return candidates


def block(reason: str, paths: list[str]) -> int:
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": reason,
                "protected_paths": paths,
                "remediation": "Do not read or edit secrets, credential material, or SQLite runtime state. Use redacted examples or documented settings instead.",
            }
        )
    )
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        return block(f"invalid hook input json: {exc}", [])

    tool_name = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    protected = sorted({path for path in candidate_paths(tool_name, tool_input) if is_protected(path)})
    if protected:
        return block("protected file access blocked before tool execution", protected)

    return 0


if __name__ == "__main__":
    sys.exit(main())
