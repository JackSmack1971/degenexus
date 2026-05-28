# Test Writer — Agent Memory

## Current operating assumptions

- Follow `.claude/rules/02-agent-synergy.md` and `.claude/rules/synergy-contract.yml` for routing.
- Emit `.claude/rules/evidence-schema.yml` fields for routed findings.
- Record only stable project facts, recurring validated patterns, or durable false positives; never secrets or transient task state.

## Recent validated learnings

- 2026-05-28: Memory file uses the documented uppercase `MEMORY.md` project-memory contract.

## Historical notes

> Persistent memory for the test-writer subagent.
> Stores: testing patterns, coverage gaps, common edge cases for this codebase.

## Memory Write Criteria
- Record only recurring patterns, validated false positives, and stable project facts.
- Do not record one-off task details.
- Include date and source evidence for every entry.

## Testing Patterns That Work Well in This Codebase
[Empty — populated as test suites are written]

## Persistent Coverage Gaps
[Empty — populated as audits reveal untested areas]

## Component-Specific Edge Cases (recurring)
[Empty — populated when BVA/ECP reveals patterns across components]
