from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "log-subagent-event.py"


def load_logger():
    spec = importlib.util.spec_from_file_location("log_subagent_event", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_log_subagent_event_writes_jsonl(tmp_path: Path, monkeypatch) -> None:
    logger = load_logger()
    log_path = tmp_path / "subagent-events.jsonl"
    monkeypatch.setattr(logger, "ROOT", tmp_path)
    monkeypatch.setattr(logger, "LOG_PATH", log_path)
    monkeypatch.setattr(logger, "git_value", lambda *args: "abc123" if args == ("rev-parse", "HEAD") else "src/main.py")
    monkeypatch.setattr(logger.sys, "stdin", type("Stdin", (), {"read": staticmethod(lambda: json.dumps({"hook_event_name": "SubagentStart", "agent_type": "code-reviewer", "scope": "review"}))})())

    assert logger.main() == 0

    event = json.loads(log_path.read_text().strip())
    assert event["hook_event_name"] == "SubagentStart"
    assert event["agent_type"] == "code-reviewer"
    assert event["git_sha"] == "abc123"
    assert event["changed_files"] == ["src/main.py"]
    assert event["scope"] == "review"
