#!/usr/bin/env python3
"""Validate Claude Code project configuration."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
SKILLS_DIR = CLAUDE_DIR / "skills"
COMMANDS_DIR = CLAUDE_DIR / "commands"
MEMORY_DIR = CLAUDE_DIR / "agent-memory"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
README_PATH = CLAUDE_DIR / "README.md"

ALLOWED_HOOK_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "SubagentStart",
    "SubagentStop",
    "SubagentNotification",
    "UserPromptSubmit",
    "SessionStart",
    "SessionEnd",
    "ConfigChange",
    "FileChanged",
    "TaskCompleted",
}
MATCHER_IGNORED_EVENTS = {"Notification", "Stop", "UserPromptSubmit", "SessionStart", "SessionEnd", "TaskCompleted"}
MATCHER_EXPECTED_EVENTS = {"PreToolUse", "PostToolUse", "ConfigChange", "FileChanged"}
ALLOWED_SKILL_FIELDS = {
    "name",
    "description",
    "disable-model-invocation",
    "allowed-tools",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "when_to_use",
    "argument-hint",
}
FORBIDDEN_PERMISSION_MODES = {"bypassPermissions"}
KNOWN_WRITE_CAPABLE_AGENTS = {"test-engineer"}


def repo_path(path: Path, root: Path = ROOT) -> str:
    return str(path.relative_to(root))


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


def markdown_files(root: Path) -> list[Path]:
    return sorted((root / ".claude").rglob("*.md"))


def validate_frontmatter(root: Path, errors: list[str]) -> None:
    for path in markdown_files(root):
        try:
            frontmatter(path.read_text(errors="replace"))
        except Exception as exc:  # noqa: BLE001 - config validator reports all parse failures.
            errors.append(f"invalid frontmatter: {repo_path(path, root)}: {exc}")


def validate_skill_layout(root: Path, errors: list[str]) -> set[str]:
    skills_dir = root / ".claude" / "skills"
    skills = {path.parent.name for path in skills_dir.glob("*/SKILL.md")}
    for path in sorted(skills_dir.iterdir() if skills_dir.exists() else []):
        if path.is_file():
            errors.append(f"stray skill file should be a directory with SKILL.md: {repo_path(path, root)}")
    return skills


def validate_skill_frontmatter(root: Path, warnings: list[str]) -> None:
    for skill in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        fm = frontmatter(skill.read_text(errors="replace"))
        for field in fm:
            if field not in ALLOWED_SKILL_FIELDS:
                warnings.append(f"unknown skill frontmatter field: {repo_path(skill, root)} -> {field}")
        description = str(fm.get("description") or "")
        if len(description) > 500:
            warnings.append(f"long model-invocable skill description: {repo_path(skill, root)} ({len(description)} chars)")


def validate_agent_skills_and_memory(root: Path, skills: set[str], errors: list[str], warnings: list[str]) -> None:
    for agent in sorted((root / ".claude" / "agents").glob("*.md")):
        fm = frontmatter(agent.read_text(errors="replace"))
        name = str(fm.get("name") or agent.stem)
        for skill in fm.get("skills", []) or []:
            if skill not in skills:
                errors.append(f"missing skill reference: {repo_path(agent, root)} -> {skill}")
        if fm.get("memory") == "project":
            memory_file = root / ".claude" / "agent-memory" / name / "MEMORY.md"
            lowercase_file = root / ".claude" / "agent-memory" / name / "memory.md"
            if not memory_file.exists():
                errors.append(f"missing project memory file: {repo_path(memory_file, root)}")
            if lowercase_file.exists():
                errors.append(f"lowercase project memory will not auto-load: {repo_path(lowercase_file, root)}")
        permission_mode = str(fm.get("permissionMode") or "")
        if permission_mode in FORBIDDEN_PERMISSION_MODES:
            errors.append(f"forbidden permissionMode: {repo_path(agent, root)} -> {permission_mode}")
        if permission_mode == "acceptEdits" and name not in KNOWN_WRITE_CAPABLE_AGENTS:
            warnings.append(f"acceptEdits outside known write-capable agents: {repo_path(agent, root)}")
        tools = "\n".join(str(tool) for tool in fm.get("tools", []) or [])
        if "Agent(" in tools:
            readme = (root / ".claude" / "README.md").read_text(errors="replace") if (root / ".claude" / "README.md").exists() else ""
            command_text = "\n".join(p.read_text(errors="replace") for p in (root / ".claude" / "commands").glob("*.md"))
            if "main-session" not in readme.lower() and "main session" not in command_text.lower():
                warnings.append(f"agent has Agent(...) tools without documented main-session invocation: {repo_path(agent, root)}")


def validate_commands(root: Path, skills: set[str], errors: list[str], warnings: list[str]) -> None:
    stale_pattern = re.compile(r"agent-skills:[A-Za-z0-9_.:-]+")
    for command in sorted((root / ".claude" / "commands").glob("*.md")):
        text = command.read_text(errors="replace")
        for match in stale_pattern.findall(text):
            errors.append(f"stale plugin skill reference: {repo_path(command, root)} -> {match}")
        if "browser" in text.lower() and "DevTools" in text:
            errors.append(f"browser DevTools workflow is not project-local: {repo_path(command, root)}")
        if command.stem in skills:
            warnings.append(f"slash command name collides with skill name: {repo_path(command, root)} -> {command.stem}")


def validate_settings(root: Path, errors: list[str], warnings: list[str]) -> None:
    settings_path = root / ".claude" / "settings.json"
    if not settings_path.exists():
        errors.append("missing .claude/settings.json")
        return
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"invalid settings json: {exc}")
        return
    deny_rules = settings.get("permissions", {}).get("deny", [])
    for expected in ("Read(.env*)", "Bash(cat .env*)", "Bash(rm -rf *)"):
        if expected not in deny_rules:
            warnings.append(f"missing recommended deny rule: {expected}")
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        errors.append("settings hooks must be a mapping")
        return
    for event, entries in hooks.items():
        if event not in ALLOWED_HOOK_EVENTS:
            warnings.append(f"unknown hook event: {event}")
        if not isinstance(entries, list):
            errors.append(f"hook event entries must be a list: {event}")
            continue
        for index, entry in enumerate(entries):
            matcher = entry.get("matcher") if isinstance(entry, dict) else None
            if event in MATCHER_IGNORED_EVENTS and matcher:
                warnings.append(f"matcher is ignored for {event}: entry {index}")
            if event in MATCHER_EXPECTED_EVENTS and not matcher:
                warnings.append(f"matcher omitted for policy-sensitive event {event}: entry {index}")
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if command and command.startswith("python .claude/hooks/"):
                    script = root / command.split("python ", 1)[1].split()[0]
                    if not script.exists():
                        errors.append(f"hook command references missing script: {command}")


def validate_readme_inventory(root: Path, skills: set[str], errors: list[str]) -> None:
    readme_path = root / ".claude" / "README.md"
    if not readme_path.exists():
        errors.append("missing .claude/README.md")
        return
    readme = readme_path.read_text(errors="replace")
    inventories = [
        *(p.stem for p in (root / ".claude" / "agents").glob("*.md")),
        *skills,
        *(p.stem for p in (root / ".claude" / "commands").glob("*.md")),
        *(p.name for p in (root / ".claude" / "hooks").glob("*.py")),
    ]
    for item in sorted(set(inventories)):
        if item not in readme:
            errors.append(f"README inventory missing: {item}")


def validate(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    validate_frontmatter(root, errors)
    skills = validate_skill_layout(root, errors)
    validate_skill_frontmatter(root, warnings)
    validate_agent_skills_and_memory(root, skills, errors, warnings)
    validate_commands(root, skills, errors, warnings)
    validate_settings(root, errors, warnings)
    validate_readme_inventory(root, skills, errors)
    return errors, warnings


def main() -> int:
    errors, warnings = validate(ROOT)
    if errors:
        print("claude config validation failed:")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("warnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1
    print("claude config validation ok")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    model_invocable = []
    for skill in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        fm = frontmatter(skill.read_text(errors="replace"))
        if not fm.get("disable-model-invocation"):
            model_invocable.append(f"{skill.parent.name} ({len(str(fm.get('description') or ''))} chars)")
    print("model-invocable skills:")
    for skill in model_invocable:
        print(f"- {skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
