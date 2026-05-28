from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "validate-evidence-payload.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence_payload", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_accepts_schema_valid_yaml_payload() -> None:
    validator = load_validator()
    schema = validator.load_schema()
    payload = {
        "verdict": "PASS",
        "scope_reviewed": [".claude/rules/evidence-schema.yml"],
        "source_of_truth": {
            "files": [".claude/rules/evidence-schema.yml"],
            "runtime_state": [],
        },
        "commands_run": [
            {
                "command": "python .claude/hooks/validate-evidence-payload.py fixture.yml",
                "result": "PASS",
                "reason": "unit fixture",
            }
        ],
        "findings": {"critical": [], "important": [], "suggestions": []},
        "edge_cases": [{"name": "empty finding lists", "covered_by": "test"}],
        "handoffs": [],
        "memory_update": {"needed": False, "path": ""},
    }

    assert validator.validate_payload(payload, schema) == []


def test_rejects_missing_source_files_and_unowned_needs_info() -> None:
    validator = load_validator()
    schema = validator.load_schema()
    payload = {
        "verdict": "NEEDS_INFO",
        "scope_reviewed": [".claude/rules/evidence-schema.yml"],
        "source_of_truth": {"files": [], "runtime_state": []},
        "findings": {"critical": [], "important": [], "suggestions": []},
    }

    errors = validator.validate_payload(payload, schema)

    assert "source_of_truth.files must be non-empty" in errors
    assert "NEEDS_INFO requires a concrete handoffs entry with agent and reason" in errors
