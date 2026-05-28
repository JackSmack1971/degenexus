#!/usr/bin/env python3
"""Validate Claude Code project configuration."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
SKILLS_DIR = CLAUDE_DIR / "skills"
COMMANDS_DIR = CLAUDE_DIR / "commands"


def frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("frontmatter opener without closing delimiter")
    loaded = yaml.safe_load(parts[1])
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter must parse to a mapping")
    return loaded


def validate_frontmatter(errors: list[str]) -> None:
    for path in sorted(CLAUDE_DIR.rglob("*.md")):
        try:
            frontmatter(path.read_text(errors="replace"))
        except Exception as exc:  # noqa: BLE001 - config validator reports all parse failures.
            errors.append(f"invalid frontmatter: {path.relative_to(ROOT)}: {exc}")


def validate_skill_layout(errors: list[str]) -> set[str]:
    skills = {path.parent.name for path in SKILLS_DIR.glob("*/SKILL.md")}
    stray_files = [path for path in SKILLS_DIR.iterdir() if path.is_file()]
    for path in sorted(stray_files):
        errors.append(f"stray skill file should be a directory with SKILL.md: {path.relative_to(ROOT)}")
    return skills


def validate_agent_skills(skills: set[str], errors: list[str]) -> None:
    for agent in sorted(AGENTS_DIR.glob("*.md")):
        fm = frontmatter(agent.read_text(errors="replace"))
        for skill in fm.get("skills", []) or []:
            if skill not in skills:
                errors.append(f"missing skill reference: {agent.relative_to(ROOT)} -> {skill}")


def validate_commands(errors: list[str]) -> None:
    stale_pattern = re.compile(r"agent-skills:[A-Za-z0-9_.:-]+")
    for command in sorted(COMMANDS_DIR.glob("*.md")):
        text = command.read_text(errors="replace")
        for match in stale_pattern.findall(text):
            errors.append(f"stale plugin skill reference: {command.relative_to(ROOT)} -> {match}")
        if "browser" in text.lower() and "DevTools" in text:
            errors.append(f"browser DevTools workflow is not project-local: {command.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    skills = validate_skill_layout(errors)
    validate_agent_skills(skills, errors)
    validate_commands(errors)

    if errors:
        print("claude config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("claude config validation ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
