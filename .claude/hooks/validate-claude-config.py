#!/usr/bin/env python3
"""Validate Claude Code project configuration."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
SKILLS_DIR = CLAUDE_DIR / "skills"
COMMANDS_DIR = CLAUDE_DIR / "commands"
MEMORY_DIR = CLAUDE_DIR / "agent-memory"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
README_PATH = CLAUDE_DIR / "README.md"
SYNERGY_CONTRACT_PATH = CLAUDE_DIR / "rules" / "synergy-contract.yml"
EVIDENCE_SCHEMA_PATH = CLAUDE_DIR / "rules" / "evidence-schema.yml"
SETTINGS_WAIVERS_PATH = CLAUDE_DIR / "rules" / "settings-policy-waivers.yml"

# Source: https://code.claude.com/docs/en/hooks, reviewed 2026-05-28.
HOOK_EVENT_SOURCE_DATE = "2026-05-28"
ALLOWED_HOOK_EVENTS = {
    "Setup",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PostToolBatch",
    "PermissionRequest",
    "PermissionDenied",
    "Notification",
    "Stop",
    "SubagentStart",
    "SubagentStop",
    "SubagentNotification",
    "SessionStart",
    "SessionEnd",
    "ConfigChange",
    "FileChanged",
    "TaskCreated",
    "TaskCompleted",
    "TeammateIdle",
    "PreCompact",
    "PostCompact",
    "WorktreeCreate",
    "WorktreeRemove",
    "InstructionsLoaded",
    "CwdChanged",
    "MessageDisplay",
}
HOOK_MATCHER_ALLOWED = {
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "ConfigChange",
    "FileChanged",
    "SubagentStart",
    "SubagentStop",
    "SubagentNotification",
}
HOOK_MATCHER_EXPECTED = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "ConfigChange", "FileChanged"}
HOOK_MATCHER_IGNORED = ALLOWED_HOOK_EVENTS - HOOK_MATCHER_ALLOWED
HOOK_DECISION_CAPABLE = {
    "UserPromptSubmit",
    "PreToolUse",
    "PermissionRequest",
    "PermissionDenied",
    "PostToolUseFailure",
    "Stop",
    "SubagentStop",
}
ALLOWED_SETTINGS_KEYS = {
    "permissions",
    "hooks",
    "env",
    "includeCoAuthoredBy",
    "model",
    "statusLine",
    "feedbackSurveyState",
    "cleanupPeriodDays",
    "enableAllProjectMcpServers",
    "enabledMcpjsonServers",
    "disabledMcpjsonServers",
    "forceLoginMethod",
    "agent",
    "sandbox",
    "network",
    "plugins",
    "attribution",
}
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
WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}
INVENTORY_START = "<!-- BEGIN GENERATED CLAUDE INVENTORY -->"
INVENTORY_END = "<!-- END GENERATED CLAUDE INVENTORY -->"
WORKFLOW_SKILL_SHIMS = {"ship", "audit", "review", "test", "build", "code-simplify", "plan", "spec"}
MODEL_INVOCABLE_DESCRIPTION_LIMIT = 300
PROTECTED_DENY_PATHS = (
    "./.env",
    "./.env.*",
    "./secrets/**",
    "./**/*.pem",
    "./**/*.key",
    "./**/*credential*.json",
    "./**/*.db",
    "./**/*.db-wal",
    "./**/*.db-shm",
)


def repo_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


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


def load_yaml(path: Path, errors: list[str], root: Path = ROOT, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            errors.append(f"missing {repo_path(path, root)}")
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(errors="replace"))
    except yaml.YAMLError as exc:
        errors.append(f"invalid yaml: {repo_path(path, root)}: {exc}")
        return {}
    if not isinstance(loaded, dict):
        errors.append(f"yaml must parse to a mapping: {repo_path(path, root)}")
        return {}
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
        if not fm.get("disable-model-invocation") and len(description) > MODEL_INVOCABLE_DESCRIPTION_LIMIT:
            warnings.append(
                f"long model-invocable skill description: {repo_path(skill, root)} ({len(description)} chars)"
            )


def validate_agent_skills_and_memory(root: Path, skills: set[str], errors: list[str], warnings: list[str]) -> set[str]:
    agents: set[str] = set()
    for agent in sorted((root / ".claude" / "agents").glob("*.md")):
        text = agent.read_text(errors="replace")
        fm = frontmatter(text)
        name = str(fm.get("name") or agent.stem)
        agents.add(name)
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
        raw_tools = [str(tool) for tool in fm.get("tools", []) or []]
        raw_disallowed = [str(tool) for tool in fm.get("disallowedTools", []) or []]
        granted_write_tools = {tool for tool in raw_tools if tool in WRITE_TOOLS}
        disallowed_write_tools = {tool for tool in raw_disallowed if tool in WRITE_TOOLS}
        if name not in KNOWN_WRITE_CAPABLE_AGENTS:
            if granted_write_tools:
                errors.append(
                    f"read-only agent grants write tools: {repo_path(agent, root)} -> {sorted(granted_write_tools)}"
                )
            missing_disallowed = WRITE_TOOLS - disallowed_write_tools
            if missing_disallowed and name != "ship":
                warnings.append(
                    f"read-only agent should explicitly disallow write tools: {repo_path(agent, root)} -> {sorted(missing_disallowed)}"
                )
        elif permission_mode != "acceptEdits":
            errors.append(f"write-capable agent must use permissionMode acceptEdits: {repo_path(agent, root)}")
        tools = "\n".join(raw_tools)
        if "Agent(" in tools:
            readme_path = root / ".claude" / "README.md"
            commands_dir = root / ".claude" / "commands"
            readme = readme_path.read_text(errors="replace") if readme_path.exists() else ""
            command_text = "\n".join(p.read_text(errors="replace") for p in commands_dir.glob("*.md"))
            if "main-session" not in readme.lower() and "main session" not in command_text.lower():
                warnings.append(f"agent has Agent(...) tools without documented main-session invocation: {repo_path(agent, root)}")
        if "test" in name and "test-writer" != name:
            agent_skills = set(fm.get("skills", []) or [])
            if not ({"test-regression", "edge-case-audit"} & agent_skills):
                warnings.append(f"test-named agent lacks test skill: {repo_path(agent, root)}")
        if name == "test-writer" and "deprecated" not in text.lower():
            warnings.append("test-writer must include explicit deprecated/read-only rationale")
    return agents


def validate_commands(root: Path, skills: set[str], errors: list[str], warnings: list[str]) -> None:
    stale_pattern = re.compile(r"agent-skills:[A-Za-z0-9_.:-]+")
    for command in sorted((root / ".claude" / "commands").glob("*.md")):
        text = command.read_text(errors="replace")
        for match in stale_pattern.findall(text):
            errors.append(f"stale plugin skill reference: {repo_path(command, root)} -> {match}")
        if "browser" in text.lower() and "DevTools" in text:
            errors.append(f"browser DevTools workflow is not project-local: {repo_path(command, root)}")
        if command.stem in WORKFLOW_SKILL_SHIMS:
            for required in (
                f".claude/skills/{command.stem}/SKILL.md",
                ".claude/rules/synergy-contract.yml",
                ".claude/rules/evidence-schema.yml",
            ):
                if required not in text:
                    errors.append(f"workflow command shim missing reference: {repo_path(command, root)} -> {required}")
        elif command.stem in skills:
            warnings.append(f"slash command name collides with skill name: {repo_path(command, root)} -> {command.stem}")


def referenced_hook_script(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    for part in parts[1:]:
        if ".claude/hooks/" in part and part.endswith(".py"):
            return Path(part.replace("$CLAUDE_PROJECT_DIR/", "")).name
    return None


def has_hook_script(settings: dict[str, Any], event: str, script_name: str) -> bool:
    for entry in settings.get("hooks", {}).get(event, []) or []:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []) or []:
            command = hook.get("command") if isinstance(hook, dict) else None
            if isinstance(command, str) and referenced_hook_script(command) == script_name:
                return True
    return False


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
    for key in settings:
        if key not in ALLOWED_SETTINGS_KEYS:
            warnings.append(f"unknown settings top-level key: {key}")
    deny_rules = settings.get("permissions", {}).get("deny", [])
    if not isinstance(deny_rules, list):
        errors.append("settings permissions.deny must be a list")
        deny_rules = []
    for expected in ("Read(.env*)", "Bash(cat .env*)", "Bash(rm -rf *)"):
        if expected not in deny_rules:
            warnings.append(f"missing recommended deny rule: {expected}")
    strict_protected_policy = (root / ".claude" / "hooks" / "protect-sensitive-files.py").exists() or any(
        "secrets/**" in str(rule) or "*.pem" in str(rule) for rule in deny_rules
    )
    if strict_protected_policy:
        for path in PROTECTED_DENY_PATHS:
            for tool in ("Read", "Edit", "Write"):
                expected = f"{tool}({path})"
                if expected not in deny_rules:
                    warnings.append(f"missing protected-file deny rule: {expected}")
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        errors.append("settings hooks must be a mapping")
        return
    if strict_protected_policy and not has_hook_script(settings, "PreToolUse", "protect-sensitive-files.py"):
        errors.append("missing PreToolUse protected-file hook registration")
    waivers_path = root / ".claude" / "rules" / "settings-policy-waivers.yml"
    if waivers_path.exists():
        if not ("sandbox" in settings or waivers_path.exists()):
            warnings.append("missing sandbox settings or documented waiver")
        if not ("network" in settings or waivers_path.exists()):
            warnings.append("missing network settings or documented waiver")
    for event, entries in hooks.items():
        if event not in ALLOWED_HOOK_EVENTS:
            warnings.append(f"unknown hook event: {event}")
        if not isinstance(entries, list):
            errors.append(f"hook event entries must be a list: {event}")
            continue
        for index, entry in enumerate(entries):
            matcher = entry.get("matcher") if isinstance(entry, dict) else None
            if event in HOOK_MATCHER_IGNORED and matcher:
                warnings.append(f"matcher is ignored for {event}: entry {index}")
            if event in HOOK_MATCHER_EXPECTED and not matcher:
                warnings.append(f"matcher omitted for policy-sensitive event {event}: entry {index}")
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if command:
                    script_name = referenced_hook_script(str(command))
                    if script_name:
                        script = root / ".claude" / "hooks" / script_name
                        if not script.exists():
                            errors.append(f"hook command references missing script: {command}")
                        if str(command).startswith("python .claude/hooks/"):
                            warnings.append(
                                f"hook command should use CLAUDE_PROJECT_DIR for CWD safety: {command}"
                            )


def validate_synergy_contract(
    root: Path,
    agents: set[str],
    skills: set[str],
    errors: list[str],
) -> None:
    contract_path = root / ".claude" / "rules" / "synergy-contract.yml"
    contract = load_yaml(contract_path, errors, root, required=contract_path.exists())
    if not contract:
        return
    surfaces = contract.get("risk_surfaces", {})
    if not isinstance(surfaces, dict):
        errors.append("synergy contract risk_surfaces must be a mapping")
        return
    for surface, config in surfaces.items():
        if not isinstance(config, dict):
            errors.append(f"synergy surface must be a mapping: {surface}")
            continue
        primary = str(config.get("primary_agent") or "")
        if primary not in agents:
            errors.append(f"synergy primary_agent missing: {surface} -> {primary}")
            continue
        agent_text = (root / ".claude" / "agents" / f"{primary}.md").read_text(errors="replace")
        if ".claude/rules/evidence-schema.yml" not in agent_text:
            errors.append(f"agent prompt missing evidence schema reference: {primary}")
        for skill in config.get("required_skills", []) or []:
            if skill not in skills:
                errors.append(f"synergy skill missing: {surface} -> {skill}")
        for evidence in config.get("required_evidence", []) or []:
            if str(evidence) not in agent_text:
                errors.append(f"agent prompt missing owned evidence field: {primary} -> {evidence}")
    for command_name in (contract.get("command_contract", {}) or {}).get("commands", []) or []:
        command_path = root / ".claude" / "commands" / f"{command_name}.md"
        if not command_path.exists():
            errors.append(f"synergy contract command missing: {command_name}")
            continue
        text = command_path.read_text(errors="replace")
        for required in (contract.get("command_contract", {}) or {}).get("must_reference", []) or []:
            if required not in text:
                errors.append(f"synergy command missing contract reference: {repo_path(command_path, root)} -> {required}")


def validate_evidence_schema(root: Path, errors: list[str]) -> None:
    schema_path = root / ".claude" / "rules" / "evidence-schema.yml"
    schema = load_yaml(schema_path, errors, root, required=schema_path.exists())
    if not schema:
        return
    required = schema.get("minimum_gate_fields", [])
    fields = schema.get("required_fields", {})
    for field in required:
        if field not in fields:
            errors.append(f"evidence schema minimum field missing definition: {field}")
    release_skill = root / ".claude" / "skills" / "release-evidence-pack" / "SKILL.md"
    if release_skill.exists() and ".claude/rules/evidence-schema.yml" not in release_skill.read_text(errors="replace"):
        errors.append("release-evidence-pack must reference evidence schema")
    evidence_validator = root / ".claude" / "hooks" / "validate-evidence-payload.py"
    if not evidence_validator.exists():
        errors.append("missing evidence payload validator: .claude/hooks/validate-evidence-payload.py")


def validate_memory_convention(root: Path, warnings: list[str]) -> None:
    for memory_file in sorted((root / ".claude" / "agent-memory").glob("*/MEMORY.md")):
        text = memory_file.read_text(errors="replace")
        if len(text.splitlines()) > 200 and "## Current operating assumptions" not in text:
            warnings.append(f"long memory lacks top summary section: {repo_path(memory_file, root)}")


def command_invocation_mode(skill_path: Path) -> str:
    fm = frontmatter(skill_path.read_text(errors="replace"))
    if fm.get("disable-model-invocation"):
        return "Manual-only"
    return "Model-invocable"


def generate_inventory(root: Path = ROOT) -> str:
    agents_dir = root / ".claude" / "agents"
    skills_dir = root / ".claude" / "skills"
    commands_dir = root / ".claude" / "commands"
    hooks_dir = root / ".claude" / "hooks"
    memory_dir = root / ".claude" / "agent-memory"
    settings = json.loads((root / ".claude" / "settings.json").read_text()) if (root / ".claude" / "settings.json").exists() else {}

    lines = [INVENTORY_START, "", "### Generated Claude Inventory", ""]
    lines += ["#### Agents", "", "| Agent | Permission mode | Write-capable | Preloaded skills | Memory |", "| --- | --- | --- | --- | --- |"]
    for path in sorted(agents_dir.glob("*.md")):
        fm = frontmatter(path.read_text(errors="replace"))
        name = str(fm.get("name") or path.stem)
        tools = {str(tool) for tool in fm.get("tools", []) or []}
        write_capable = "Yes" if tools & WRITE_TOOLS else "No"
        skills = ", ".join(f"`{skill}`" for skill in fm.get("skills", []) or []) or "—"
        memory = "Project" if fm.get("memory") == "project" else "None"
        lines.append(f"| `{name}` | `{fm.get('permissionMode', '—')}` | {write_capable} | {skills} | {memory} |")

    lines += ["", "#### Skills", "", "| Skill | Invocation mode | Owner agents |", "| --- | --- | --- |"]
    agent_owners: dict[str, list[str]] = {}
    for path in sorted(agents_dir.glob("*.md")):
        fm = frontmatter(path.read_text(errors="replace"))
        name = str(fm.get("name") or path.stem)
        for skill in fm.get("skills", []) or []:
            agent_owners.setdefault(str(skill), []).append(name)
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        skill = path.parent.name
        mode = command_invocation_mode(path)
        owners = ", ".join(f"`{owner}`" for owner in sorted(agent_owners.get(skill, []))) or "parent session"
        lines.append(f"| `{skill}` | {mode} | {owners} |")

    lines += ["", "#### Commands", "", "| Command | Canonical source |", "| --- | --- |"]
    for path in sorted(commands_dir.glob("*.md")):
        skill_path = skills_dir / path.stem / "SKILL.md"
        source = f"`.claude/skills/{path.stem}/SKILL.md`" if skill_path.exists() else "Intentional command-only"
        lines.append(f"| `/{path.stem}` | {source} |")

    event_map: dict[str, list[str]] = {}
    for event, entries in (settings.get("hooks", {}) or {}).items():
        for entry in entries or []:
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if isinstance(command, str):
                    script_name = referenced_hook_script(command)
                    if script_name:
                        event_map.setdefault(script_name, []).append(event)
    lines += ["", "#### Hooks", "", "| Hook script | Events |", "| --- | --- |"]
    for path in sorted(hooks_dir.glob("*.py")):
        events = ", ".join(f"`{event}`" for event in sorted(set(event_map.get(path.name, [])))) or "Not registered"
        lines.append(f"| `{path.name}` | {events} |")

    lines += ["", "#### Memories", "", "| Agent memory | Status |", "| --- | --- |"]
    for path in sorted(memory_dir.glob("*/MEMORY.md")):
        lines.append(f"| `{path.parent.name}` | Present |")
    lines += ["", INVENTORY_END]
    return "\n".join(lines)


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
        *(("synergy-contract.yml",) if (root / ".claude" / "rules" / "synergy-contract.yml").exists() else ()),
        *(("evidence-schema.yml",) if (root / ".claude" / "rules" / "evidence-schema.yml").exists() else ()),
        *(("settings-policy-waivers.yml",) if (root / ".claude" / "rules" / "settings-policy-waivers.yml").exists() else ()),
    ]
    for item in sorted(set(inventories)):
        if item not in readme:
            errors.append(f"README inventory missing: {item}")
    expected = generate_inventory(root)
    if INVENTORY_START not in readme or INVENTORY_END not in readme:
        errors.append("README missing generated Claude inventory block")
        return
    actual = readme.split(INVENTORY_START, 1)[1].split(INVENTORY_END, 1)[0]
    actual_block = f"{INVENTORY_START}{actual}{INVENTORY_END}"
    if actual_block != expected:
        errors.append("README generated Claude inventory block is stale; run validate-claude-config.py --print-inventory")


def run_self_test() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scratch = {
        "permissions": {"deny": ["Read(.env*)", "Bash(cat .env*)", "Bash(rm -rf *)"]},
        "hooks": {
            "InstructionsLoaded": [{"hooks": [{"type": "command", "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/log-instructions-loaded.py"'}]}],
            "PreCompact": [{"hooks": [{"type": "command", "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start-reminder.py"'}]}],
            "PostToolUseFailure": [{"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/validate-claude-config.py"'}]}],
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".claude" / "hooks").mkdir(parents=True)
        (root / ".claude" / "rules").mkdir(parents=True)
        for script in ("log-instructions-loaded.py", "session-start-reminder.py", "validate-claude-config.py"):
            (root / ".claude" / "hooks" / script).write_text("#!/usr/bin/env python3\n")
        (root / ".claude" / "settings.json").write_text(json.dumps(scratch))
        validate_settings(root, errors, warnings)
    return errors, warnings


def validate(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    validate_frontmatter(root, errors)
    skills = validate_skill_layout(root, errors)
    validate_skill_frontmatter(root, warnings)
    agents = validate_agent_skills_and_memory(root, skills, errors, warnings)
    validate_commands(root, skills, errors, warnings)
    validate_settings(root, errors, warnings)
    validate_synergy_contract(root, agents, skills, errors)
    validate_evidence_schema(root, errors)
    validate_memory_convention(root, warnings)
    validate_readme_inventory(root, skills, errors)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Claude Code project configuration.")
    parser.add_argument("--print-inventory", action="store_true", help="print generated Markdown inventory block")
    parser.add_argument("--self-test", action="store_true", help="validate representative newer hook events")
    args = parser.parse_args()
    if args.print_inventory:
        print(generate_inventory(ROOT))
        return 0
    if args.self_test:
        errors, warnings = run_self_test()
        if errors:
            print("claude config validator self-test failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print("claude config validator self-test ok")
        if warnings:
            print("warnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 0

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
