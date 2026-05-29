from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "validate-claude-config.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_claude_config", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_minimal_claude(root: Path) -> None:
    claude = root / ".claude"
    (claude / "agents").mkdir(parents=True)
    (claude / "skills" / "sample-skill").mkdir(parents=True)
    (claude / "commands").mkdir(parents=True)
    (claude / "hooks").mkdir(parents=True)
    (claude / "agent-memory" / "sample-agent").mkdir(parents=True)
    (claude / "agents" / "sample-agent.md").write_text(
        "---\n"
        "name: sample-agent\n"
        "skills:\n"
        "  - sample-skill\n"
        "memory: project\n"
        "permissionMode: dontAsk\n"
        "disallowedTools:\n"
        "  - Write\n"
        "  - Edit\n"
        "  - MultiEdit\n"
        "---\nBody\n"
    )
    (claude / "skills" / "sample-skill" / "SKILL.md").write_text(
        "---\nname: sample-skill\ndescription: Sample skill.\n---\nBody\n"
    )
    (claude / "commands" / "sample.md").write_text("---\ndescription: Sample command.\n---\n")
    (claude / "hooks" / "validate-claude-config.py").write_text("print('ok')\n")
    (claude / "agent-memory" / "sample-agent" / "MEMORY.md").write_text("# Memory\n")
    import json

    (claude / "settings.json").write_text(
        json.dumps(
            {
                "permissions": {"deny": ["Read(.env*)", "Bash(cat .env*)", "Bash(rm -rf *)"]},
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/validate-claude-config.py\"",
                                }
                            ],
                        }
                    ]
                },
            }
        )
    )
    (claude / "README.md").write_text(
        "sample-agent\nsample-skill\nsample\nvalidate-claude-config.py\n"
    )


def sync_generated_inventory(root: Path, validator) -> None:
    readme = root / ".claude" / "README.md"
    content = readme.read_text()
    inventory = validator.generate_inventory(root)
    if validator.INVENTORY_START in content and validator.INVENTORY_END in content:
        before = content.split(validator.INVENTORY_START, 1)[0]
        after = content.split(validator.INVENTORY_END, 1)[1]
        readme.write_text(before + inventory + after)
    else:
        readme.write_text(content + inventory + "\n")


def test_validator_accepts_minimal_valid_project(tmp_path: Path) -> None:
    validator = load_validator()
    write_minimal_claude(tmp_path)
    sync_generated_inventory(tmp_path, validator)

    errors, warnings = validator.validate(tmp_path)

    assert errors == []
    assert warnings == []


def test_validator_rejects_lowercase_project_memory(tmp_path: Path) -> None:
    validator = load_validator()
    write_minimal_claude(tmp_path)
    sync_generated_inventory(tmp_path, validator)
    memory_dir = tmp_path / ".claude" / "agent-memory" / "sample-agent"
    (memory_dir / "MEMORY.md").unlink()
    (memory_dir / "memory.md").write_text("# wrong case\n")

    errors, _warnings = validator.validate(tmp_path)

    assert any("missing project memory file" in error for error in errors)
    assert any("lowercase project memory" in error for error in errors)


def test_validator_flags_missing_skill_and_forbidden_permission(tmp_path: Path) -> None:
    validator = load_validator()
    write_minimal_claude(tmp_path)
    sync_generated_inventory(tmp_path, validator)
    agent = tmp_path / ".claude" / "agents" / "sample-agent.md"
    agent.write_text(agent.read_text().replace("sample-skill", "missing-skill").replace("dontAsk", "bypassPermissions"))

    errors, _warnings = validator.validate(tmp_path)

    assert any("missing skill reference" in error for error in errors)
    assert any("forbidden permissionMode" in error for error in errors)


def test_validator_warns_on_command_skill_collision_and_unknown_skill_field(tmp_path: Path) -> None:
    validator = load_validator()
    write_minimal_claude(tmp_path)
    (tmp_path / ".claude" / "commands" / "sample-skill.md").write_text("---\ndescription: collision\n---\n")
    skill = tmp_path / ".claude" / "skills" / "sample-skill" / "SKILL.md"
    skill.write_text(skill.read_text().replace("description: Sample skill.", "description: Sample skill.\nunknown-field: true"))
    readme = tmp_path / ".claude" / "README.md"
    readme.write_text(readme.read_text() + "sample-skill\n")
    sync_generated_inventory(tmp_path, validator)

    errors, warnings = validator.validate(tmp_path)

    assert errors == []
    assert any("slash command name collides" in warning for warning in warnings)
    assert any("unknown skill frontmatter field" in warning for warning in warnings)


def test_validator_accepts_arch_audit_extension_fields(tmp_path: Path) -> None:
    validator = load_validator()
    write_minimal_claude(tmp_path)
    skill = tmp_path / ".claude" / "skills" / "sample-skill" / "SKILL.md"
    skill.write_text(
        "---\n"
        "name: sample-skill\n"
        "description: Sample skill.\n"
        "disable-model-invocation: true\n"
        "user-invocable: false\n"
        "agent: Plan\n"
        "---\nBody\n"
    )

    import json

    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["disableSkillShellExecution"] = False
    data["awsAuthRefresh"] = "aws sso login --profile enterprise-devsecops"
    settings.write_text(json.dumps(data))
    sync_generated_inventory(tmp_path, validator)

    errors, warnings = validator.validate(tmp_path)

    assert errors == []
    assert not any("unknown skill frontmatter field" in warning for warning in warnings)
    assert not any("unknown settings top-level key" in warning for warning in warnings)
