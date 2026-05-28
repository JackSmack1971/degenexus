#!/usr/bin/env python3
"""Validate specialist/release evidence payloads against evidence-schema.yml."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / ".claude" / "rules" / "evidence-schema.yml"
YAML_FENCE = re.compile(r"```ya?ml\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def load_schema() -> dict[str, Any]:
    loaded = yaml.safe_load(SCHEMA_PATH.read_text())
    if not isinstance(loaded, dict):
        raise ValueError(f"schema must be a mapping: {SCHEMA_PATH}")
    return loaded


def parse_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("payload is empty")
    if stripped.startswith("{"):
        loaded = json.loads(stripped)
    elif stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) < 3:
            raise ValueError("frontmatter payload has no closing delimiter")
        loaded = yaml.safe_load(parts[1])
    else:
        match = YAML_FENCE.search(stripped)
        loaded = yaml.safe_load(match.group(1) if match else stripped)
    if not isinstance(loaded, dict):
        raise ValueError("evidence payload must parse to a mapping")
    return loaded


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def validate_scalar(name: str, value: Any, spec: dict[str, Any], errors: list[str]) -> None:
    allowed = spec.get("allowed")
    if allowed and value not in allowed:
        errors.append(f"{name} must be one of {allowed}, got {value!r}")
        return
    expected_type = spec.get("type")
    if expected_type == "list" and not isinstance(value, list):
        errors.append(f"{name} must be a list")
    elif expected_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{name} must be a boolean")


def validate_item_fields(name: str, values: Any, spec: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(values, list):
        return
    item_fields = spec.get("item_fields", {}) or {}
    if not item_fields:
        return
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            errors.append(f"{name}[{index}] must be a mapping")
            continue
        for field, field_spec in item_fields.items():
            if field not in item or _is_empty(item.get(field)):
                errors.append(f"{name}[{index}].{field} is required")
                continue
            if isinstance(field_spec, dict):
                validate_scalar(f"{name}[{index}].{field}", item[field], field_spec, errors)
            elif field_spec == "string" and not isinstance(item[field], str):
                errors.append(f"{name}[{index}].{field} must be a string")


def validate_payload(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = schema.get("required_fields", {}) or {}
    for field in schema.get("minimum_gate_fields", []) or []:
        if field not in payload or _is_empty(payload[field]):
            errors.append(f"missing or empty minimum gate field: {field}")
    for field, spec in fields.items():
        if field not in payload:
            continue
        if isinstance(spec, dict) and ("type" in spec or "allowed" in spec):
            validate_scalar(field, payload[field], spec, errors)
            validate_item_fields(field, payload[field], spec, errors)
        elif isinstance(spec, dict):
            if not isinstance(payload[field], dict):
                errors.append(f"{field} must be a mapping")
                continue
            for child, child_spec in spec.items():
                if child not in payload[field]:
                    errors.append(f"{field}.{child} is required")
                    continue
                if field == "source_of_truth" and child == "files" and _is_empty(payload[field][child]):
                    errors.append("source_of_truth.files must be non-empty")
                    continue
                if isinstance(child_spec, dict):
                    validate_scalar(f"{field}.{child}", payload[field][child], child_spec, errors)
                elif child_spec == "string" and not isinstance(payload[field][child], str):
                    errors.append(f"{field}.{child} must be a string")
                if field == "memory_update" and child == "path" and not payload[field].get("needed"):
                    continue
    verdict = payload.get("verdict")
    if verdict == "NEEDS_INFO":
        handoffs = payload.get("handoffs") or []
        has_owner = any(isinstance(item, dict) and item.get("agent") and item.get("reason") for item in handoffs)
        if not has_owner:
            errors.append("NEEDS_INFO requires a concrete handoffs entry with agent and reason")
    source = payload.get("source_of_truth") or {}
    if isinstance(source, dict) and _is_empty(source.get("files")) and "source_of_truth.files must be non-empty" not in errors:
        errors.append("source_of_truth.files must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a schema-checkable evidence payload.")
    parser.add_argument("payload", nargs="?", help="JSON/YAML/Markdown file to validate; stdin when omitted")
    args = parser.parse_args()
    text = Path(args.payload).read_text() if args.payload else sys.stdin.read()
    try:
        payload = parse_payload(text)
        errors = validate_payload(payload, load_schema())
    except Exception as exc:  # noqa: BLE001 - CLI should report parse and schema failures uniformly.
        errors = [str(exc)]
    if errors:
        print("evidence payload validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("evidence payload validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
