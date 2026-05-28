# docs-memory-curator Project Memory

## Current operating assumptions

- Follow `.claude/rules/02-agent-synergy.md` and `.claude/rules/synergy-contract.yml` for routing.
- Emit `.claude/rules/evidence-schema.yml` fields for routed findings.
- Record only stable project facts, recurring validated patterns, or durable false positives; never secrets or transient task state.

## Recent validated learnings

- 2026-05-28: Memory file uses the documented uppercase `MEMORY.md` project-memory contract.

## Historical notes

> Persistent project memory for the docs-memory-curator subagent. Claude Code loads the first 200 lines or 25KB from this file when `memory: project` is declared.

## Write Criteria

- Record only stable project facts, recurring validated patterns, or durable false positives.
- Do not record secrets, credentials, speculative conclusions, transient task state, or raw user data.
- Use dated, append-only bullets with source file or evidence references when possible.

## Entries

- 2026-05-28: Memory file created to satisfy Claude Code project-memory naming contract; no durable specialist facts recorded yet.
