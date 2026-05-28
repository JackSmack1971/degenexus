# FDD Investigator — Agent Memory

## Current operating assumptions

- Follow `.claude/rules/02-agent-synergy.md` and `.claude/rules/synergy-contract.yml` for routing.
- Emit `.claude/rules/evidence-schema.yml` fields for routed findings.
- Record only stable project facts, recurring validated patterns, or durable false positives; never secrets or transient task state.

## Recent validated learnings

- 2026-05-28: Memory file uses the documented uppercase `MEMORY.md` project-memory contract.

## Historical notes

> Persistent memory for the fdd-investigator subagent.
> Stores: common root causes in this codebase, component reliability scores, investigation patterns.

## Memory Write Criteria
- Record only recurring patterns, validated false positives, and stable project facts.
- Do not record one-off task details.
- Include date and source evidence for every entry.

## Root Cause Patterns (most frequent in this codebase)
[Empty — populated as investigations accumulate]

## Component Reliability Log
[Empty — populated with failure rate per component over time]

## Investigation Shortcuts (known fast paths to root cause)
[Empty — populated when patterns repeat across investigations]
