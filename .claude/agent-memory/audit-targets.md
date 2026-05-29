# Architecture Audit Targets

This project-scoped memory file receives concise, actionable findings from the
`arch-audit-framework` skill. Keep entries deterministic and scoped so a later
implementation workflow can assign disjoint worktrees safely.

## Baseline Snapshot (2026-05-29)

Generated with Python AST traversal because `ast-grep` is not installed in this environment (`command -v ast-grep` returned no path).

| Package | Files | Classes | Sync functions | Async functions | Internal dependencies |
| --- | ---: | ---: | ---: | ---: | --- |
| `agents` | 8 | 8 | 44 | 0 | `core` |
| `core` | 8 | 13 | 42 | 0 | — |
| `data` | 4 | 5 | 15 | 0 | — |
| `display` | 3 | 2 | 12 | 0 | — |
| `memory` | 4 | 4 | 23 | 0 | — |
| `models` | 4 | 23 | 14 | 0 | — |
| `root` | 4 | 2 | 21 | 0 | `core`, `display`, `orchestrator` |

## Pending Targets

- Establish the first `ast-grep` baseline once the binary is available, using the default queries in `.claude/skills/arch-audit-framework/SKILL.md`.
- Confirm risk-gate, execution-gate, and portfolio state boundaries remain isolated before any implementation pass.
- Verify network and secret-handling paths against the zero-trust assumptions in `.claude/rules/01-security.md`.
- Keep remediation work outside the read-only audit skill and route it through `.claude/workflows/audit-orchestrator.js` after audit success.
