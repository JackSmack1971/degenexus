from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "protect-sensitive-files.py"


def run_hook(payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_blocks_direct_env_read() -> None:
    result = run_hook({"tool_name": "Read", "tool_input": {"file_path": ".env.local"}})

    assert result.returncode == 2
    body = json.loads(result.stdout)
    assert body["decision"] == "block"
    assert body["protected_paths"] == [".env.local"]


def test_blocks_bash_secret_path() -> None:
    result = run_hook({"tool_name": "Bash", "tool_input": {"command": "cat secrets/provider.json"}})

    assert result.returncode == 2
    body = json.loads(result.stdout)
    assert body["decision"] == "block"
    assert body["protected_paths"] == ["secrets/provider.json"]


def test_allows_normal_source_path() -> None:
    result = run_hook({"tool_name": "Read", "tool_input": {"file_path": "src/main.py"}})

    assert result.returncode == 0
    assert result.stdout == ""
