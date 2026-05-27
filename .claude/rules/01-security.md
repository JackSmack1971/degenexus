# Security Rules — DegenExus AI Trading Desk Simulator

## STRIDE Threat Model (Always Active)

### Trust Boundaries

| Source | Trust Level | Required Sanitization |
|--------|-------------|----------------------|
| LLM responses (Anthropic/OpenRouter) | **UNTRUSTED** | `_sanitize_external_text()` before injecting into agent prompts |
| Market data (yfinance/Alpha Vantage) | **UNTRUSTED** | Pydantic validators at `OHLCVBar` model boundary |
| Agent-to-agent messages (debate cycle) | **SEMI-TRUSTED** | `_sanitize_external_text()` on any prior-agent reasoning injected into next prompt |
| Environment variables (`.env`) | **TRUSTED** | Read via `pydantic-settings` only; never log raw secrets |
| SQLite trade history (`TradeStore`) | **TRUSTED** | Written by us; read via parameterized queries only (no string formatting in SQL) |

### STRIDE Analysis by Component

**Spoofing:**
- Agent identities (`agent_id`) are set at construction — not passed in external data
- No authentication between agents; orchestrator is single-process; spoofing is mitigated by architecture

**Tampering:**
- LLM responses could inject malicious values into `MarketSignal`/`TradeProposal` — **mitigated** by Pydantic validators at model boundaries
- Prompt injection via prior-agent `reasoning` field — **mitigated** by `_sanitize_external_text()` in `BaseAgent`

**Repudiation:**
- All trades logged to `TradeStore` SQLite (WAL mode) with agent reasoning at `upsert_trade`
- `challenge_log` and `event_log` tables provide audit trail for counter-challenges

**Information Disclosure:**
- API keys in `.env` only — never in source code (enforced by `Settings` pydantic-settings)
- No secrets in logs — `LOG_LEVEL=DEBUG` logs are acceptable but must not include raw API responses containing secrets

**Denial of Service:**
- LLM timeout enforced: `LLM_TIMEOUT_SECONDS` (default: 30s); `MAX_RETRIES=2` on failure
- `_fallback()` in every agent ensures system degrades gracefully without LLM

**Elevation of Privilege:**
- No user-facing input surfaces; all inputs flow from market data → LLM → structured models
- Prompt injection cannot elevate privileges because the system has no ACL — it can only affect simulated trades

---

## Prompt Injection Defense

**Pattern:** `_sanitize_external_text()` in `BaseAgent` strips injection patterns before inserting external text into LLM system prompts.

**Enforcement rule:** All text from these sources MUST pass through `_sanitize_external_text()` before injection:
- LLM response fields used as context in next prompt (e.g., `signal.reasoning`, `risk_decision.risk_reasoning`)
- Market data strings (e.g., company name, ticker from external API)
- Any string sourced from outside the current function scope

**Add new patterns to `_PROMPT_INJECTION_PATTERNS` in `BaseAgent` when new injection vectors are discovered.**

---

## Secrets Policy

- All API keys in `.env` (gitignored) — `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`
- Read exclusively via `Settings` (`pydantic-settings`) — never `os.environ.get()` directly in agent code
- Never log, print, or embed API keys in error messages, comments, or test fixtures
- `memory/trading_history.db` is gitignored in production — never commit SQLite files with real trade data

---

## Input Validation Policy

| Model | Enforced By |
|-------|-------------|
| `MarketSignal.direction` | `_normalise_direction` field_validator — accepts `"LONG"/"SHORT"` or `Direction` enum only |
| `TradeProposal` level ordering | `model_validator` — LONG: `stop_loss < entry_price < take_profit`; SHORT: reverse |
| `RiskDecision.expires_at` | Checked in `ExecutionGate.validate()` — stale decisions rejected |
| `OHLCVBar` fields | Pydantic model with typed fields |

**Rule:** Do not add runtime `isinstance` checks for values that Pydantic already enforces at model instantiation. Trust the model boundary.

---

## Dependency Audit

Run `pip-audit` after every `requirements.txt` change:
```
pip install pip-audit && pip-audit -r requirements.txt
```
Failing audits must be resolved before merging.
