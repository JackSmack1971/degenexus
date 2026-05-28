#!/usr/bin/env python3
"""Warn when secret-bearing environment files change without reading them."""

from __future__ import annotations

import json
import re
import sys

ENV_PATTERN = re.compile(r"(^|/)(\.env|\.envrc)(\..*)?$")


def main() -> int:
    payload_text = sys.stdin.read().strip()
    payload = json.loads(payload_text) if payload_text else {}
    path = str(payload.get("file_path") or payload.get("path") or payload.get("file") or "")
    if not path or ENV_PATTERN.search(path):
        print("WARNING: environment file changed. Do not read or commit secrets; verify `.gitignore` and staged files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
