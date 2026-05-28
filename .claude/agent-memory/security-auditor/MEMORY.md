# Security Auditor — Agent Memory

## Current operating assumptions

- Follow `.claude/rules/02-agent-synergy.md` and `.claude/rules/synergy-contract.yml` for routing.
- Emit `.claude/rules/evidence-schema.yml` fields for routed findings.
- Record only stable project facts, recurring validated patterns, or durable false positives; never secrets or transient task state.

## Recent validated learnings

- 2026-05-28: Memory file uses the documented uppercase `MEMORY.md` project-memory contract.

## Historical notes

> Persistent project memory for the security-auditor subagent.

## Memory Write Criteria
- Record only recurring vulnerability patterns, validated false positives, and stable project security facts.
- Do not record one-off task details or secrets.
- Include date, source evidence, and affected files for every entry.

## Recurring Patterns in This Codebase
[Empty — populate as security reviews accumulate]

## High-Risk Components (based on review history)
[Empty — populated after first review cycles]

## Common False Positives (skip these in future reviews)
[Empty — populated as review patterns emerge]
