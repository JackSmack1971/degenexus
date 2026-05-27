# Doctrine Summary — DegenExus Turn-Start Operational Checklist

## §MANDATORY TURN-START (execute in order, SKIP = PROTOCOL VIOLATION)

1. `READ memory/PROGRESS.md` → restore work state
2. `READ memory/FAILURES.md` → load known failure modes (avoid repeating)
3. `READ memory/ARCHITECTURE.md` → confirm structural assumptions
4. IDENTIFY the Source of Truth (SoT) for this task (see table below)
5. LOAD `.claude/rules/` context relevant to file types being changed

## §SOURCE OF TRUTH QUICK REFERENCE

| Domain | SoT |
|--------|-----|
| Live capital / positions | `Portfolio` object (in-memory, not DB) |
| Trade history | `TradeStore` SQLite WAL (`memory/trading_history.db`) |
| Trade state machine | `TradeLifecycle.VALID_TRANSITIONS` dict |
| Indicator values | `IndicatorEngine.compute_all()` return dict |
| Performance stats | `PerformanceAnalytics.compute()` return value |
| Risk limits | `RiskLimits.from_env()` (env vars, never hardcodes) |
| LLM config | `Settings` pydantic-settings model |

## §FSV LAW (non-negotiable on every write)

```
PRE → Read SoT. Record state.
ACT → Execute the operation.
POST → Read SoT again. Record new state.
DIFF → Assert: (post − pre) == expected_delta
HALT → If assertion fails: STOP. Report. Do NOT proceed.
```

## §FDD LAW (assume guilt until physical evidence proves innocence)

1. Collect physical evidence (logs, stack traces, SoT state)
2. Form ≥3 hypotheses; rank by prior probability
3. Falsify highest-ranked; repeat until one survives
4. Fix ROOT CAUSE — not the symptom

## §ANTI-SYCOPHANCY CONTRACT

- NEVER report success based on exit code alone
- NEVER say "Fixed" without before/after SoT evidence
- ALWAYS prefer uncomfortable truth over comfortable approximation

## §MEMORY PROTOCOL (update at every session end)

| Event | Action |
|-------|--------|
| Session END | Write to `memory/PROGRESS.md` |
| Failure encountered | Write to `memory/FAILURES.md` immediately |
| Architecture decision | Write ADR to `memory/DECISIONS.md` |
| Component understood | Update `memory/ARCHITECTURE.md` |

## §SECURITY GATES (always active — see `.claude/rules/01-security.md`)

- `_sanitize_external_text()` on ALL text crossing a trust boundary before LLM injection
- Pydantic validators at ALL model boundaries (`MarketSignal`, `TradeProposal`)
- No secrets in source — env vars via `Settings` only
- `pip-audit -r requirements.txt` after every new package addition
