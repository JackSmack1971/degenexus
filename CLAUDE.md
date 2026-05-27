# UNIFIED ENGINEERING DOCTRINE — Claude Code Framework v2.0
> **The Single Rule:** *"A return value is a claim. The Source of Truth is the verdict. Read the verdict."*
> **Status:** Source of Truth. When this conflicts with any other instruction, this wins.

---

## § MANDATORY TURN-START RITUAL

Execute at the START of EVERY session and EVERY new task:

```
1. READ  memory/PROGRESS.md     → restore current work state
2. READ  memory/FAILURES.md     → load known failure modes (avoid repeating)
3. READ  memory/ARCHITECTURE.md → confirm structural assumptions
4. IDENTIFY the Source of Truth (SoT) for this task
5. LOAD relevant .claude/rules/ context for the file types involved
```

**SKIP ANY STEP = PROTOCOL VIOLATION. Do not proceed.**

---

## § PROJECT IDENTITY

**DegenExus** — a multi-agent AI trading desk simulator.

Six specialized AI agents run a structured 8-phase debate cycle to analyze markets,
propose trades with strict risk controls, and manage a simulated portfolio entirely
inside the terminal. Every decision is logged for auditing. No real trades are placed.

---

## § CORE STACK PARAMETERS

- **Runtime:** Python 3.12
- **Package Manager:** `pip` with `requirements.txt` — do NOT substitute poetry/uv
- **Framework:** Custom multi-agent orchestration (no web framework)
- **Database:** SQLite in WAL mode via `TradeStore` (`memory/trading_history.db`)
- **Test Runner:** pytest 8+ with `pytest-asyncio` (asyncio_mode = "auto")
- **LLM Providers:** Anthropic Claude (`claude-sonnet-4-6`) or OpenRouter (configurable)
- **Key Libraries:** pydantic v2, pydantic-settings, yfinance, `ta` (technical analysis), rich

---

## § DEVELOPMENT COMMANDS

| Action           | Command                                                    |
|-----------------|------------------------------------------------------------|
| Run (dashboard) | `python src/main.py --symbols AAPL,SPY,QQQ`               |
| Run (headless)  | `python src/main.py --cycles 1 --no-dashboard`            |
| Unit Tests      | `python3 -m pytest tests/ -v`                             |
| Tests + coverage| `python3 -m pytest tests/ --cov=src --cov-report=term`    |
| Static analysis | `python3 -m pyflakes src/`                                |
| Complexity audit| `python3 -m radon cc src/ -a`                             |
| List agents     | `python src/main.py --list-agents`                        |
| Install deps    | `pip install -r requirements.txt`                         |

> **No build step.** No migration command — SQLite schema is self-initializing in `TradeStore._init_db()`.

---

## § CODEBASE STRUCTURE

```
degenexus/
├── src/
│   ├── main.py                    # CLI entry point (argparse)
│   ├── orchestrator.py            # TradingOrchestrator — coordinates all 8 phases
│   ├── agents/
│   │   ├── base_agent.py          # LLM wrapper (Anthropic + OpenRouter), prompt injection defense
│   │   ├── ceo_agent.py           # Signal triage + counter-challenge decisions
│   │   ├── data_analyst.py        # Market data fetch + indicator computation → MarketSignal
│   │   ├── quant_agent.py         # Half-Kelly position sizing → TradeProposal
│   │   ├── risk_manager.py        # Contextual LLM risk assessment (layer 2 only)
│   │   ├── execution_agent.py     # Fill simulation with slippage
│   │   └── portfolio_manager.py   # Monitors open positions; triggers partial/full TP/SL
│   ├── core/
│   │   ├── portfolio.py           # Portfolio — SoT for all live capital/position state
│   │   ├── risk_gate.py           # RiskGate — hard deterministic rules (layer 1, unovverridable)
│   │   ├── trade_lifecycle.py     # TradeLifecycle — enforces VALID_TRANSITIONS state machine
│   │   ├── execution_gate.py      # ExecutionGate — pre-fill validation
│   │   ├── slippage.py            # SlippageModel — spread + impact + gaussian noise
│   │   ├── openrouter_client.py   # OpenRouter (OpenAI-compat) HTTP client
│   │   └── settings.py            # Pydantic-settings env config
│   ├── models/
│   │   ├── trade.py               # Trade, Position, Fill, TradeState, Direction, CloseReason
│   │   ├── signals.py             # MarketSignal, TradeProposal, RiskDecision, Challenge
│   │   └── messages.py            # Agent message envelope types
│   ├── data/
│   │   ├── market_feed.py         # yfinance wrapper → OHLCVBar list
│   │   ├── indicators.py          # IndicatorEngine — RSI, MACD, BB, EMA, ATR, volume
│   │   └── fallback.py            # Deterministic fallback signal generator (LLM-free)
│   ├── memory/
│   │   ├── trade_store.py         # TradeStore — SQLite WAL, SoT for all trade history
│   │   ├── performance.py         # PerformanceAnalytics — computes stats from closed trades
│   │   └── context_injector.py    # ContextInjector — formats stats into agent system prompts
│   └── display/
│       ├── dashboard.py           # Rich live dashboard
│       └── trade_feed.py          # Live trade event feed panel
├── tests/                         # 266+ pytest tests (no __init__.py)
├── memory/
│   ├── ARCHITECTURE.md            # Live architecture doc (update when structure changes)
│   ├── PROGRESS.md                # Session-by-session progress log
│   ├── FAILURES.md                # Known failure modes
│   └── trading_history.db         # SQLite trade store (gitignored in production)
├── pyproject.toml                 # pytest + coverage config, package discovery
├── requirements.txt               # pip dependencies
└── CLAUDE.md                      # This file
```

---

## § 8-PHASE DEBATE CYCLE

```
SCAN → CEO_TRIAGE → QUANT_DESIGN → RISK_HARD_GATE → RISK_EVALUATE → CEO_FINAL → EXECUTE → MONITOR
```

| Phase            | Agent                  | Key Output                        |
|------------------|------------------------|-----------------------------------|
| SCAN             | DataAnalystAgent       | `MarketSignal` per symbol         |
| CEO_TRIAGE       | CEOAgent               | PROCEED / ABORT per signal        |
| QUANT_DESIGN     | QuantAgent             | `TradeProposal` (half-Kelly)      |
| RISK_HARD_GATE   | RiskGate (pure Python) | violations list; FINAL if any     |
| RISK_EVALUATE    | RiskManagerAgent       | `RiskDecision` (LLM contextual)   |
| CEO_FINAL        | CEOAgent               | PROCEED / ABORT (+ 1 challenge)   |
| EXECUTE          | ExecutionAgent         | `Fill` + `Trade` record           |
| MONITOR          | PortfolioManagerAgent  | Partial TP / full TP / SL exits   |

**Hard gate is FINAL.** No LLM, no CEO can override a hard rule violation.
CEO counter-challenge only applies to contextual (layer 2) rejections.
Max 2 signals processed per cycle. Max 1 CEO counter-challenge per cycle.

---

## § SOURCE OF TRUTH LOCATIONS

| Domain             | SoT                                              |
|--------------------|--------------------------------------------------|
| Live capital/positions | `Portfolio` in-memory object (`src/core/portfolio.py`) |
| Trade history      | `TradeStore` SQLite (`memory/trading_history.db`) |
| Trade state        | `TradeLifecycle.VALID_TRANSITIONS` dict          |
| Indicator values   | `IndicatorEngine.compute_all()` return dict      |
| Performance stats  | `PerformanceAnalytics.compute()` return value    |
| Risk limits        | `RiskLimits.from_env()` (env vars, not hardcodes)|
| LLM config         | `Settings` pydantic-settings model               |

> Portfolio is **NOT** persisted on restart — it is rebuilt from scratch.
> TradeStore IS persisted (SQLite WAL). Positions are not rebuilt from DB on restart.

---

## § KEY INVARIANTS

1. **Direction validation**: `Direction` enum (`LONG`|`SHORT`) is enforced at `MarketSignal` and `TradeProposal` model boundaries via `_normalise_direction` field_validator. Always use `.value` when calling `str()` on an enum in Python 3.11+ (`str(Direction.LONG)` → `"Direction.LONG"`, not `"LONG"`).

2. **Trade level ordering** (model_validator enforced):
   - LONG: `stop_loss < entry_price < take_profit`
   - SHORT: `stop_loss > entry_price > take_profit`

3. **Partial TP dedup**: `PortfolioManagerAgent._partial_tp_flags: set[str]` is seeded from `TradeStore.get_partially_closed_trade_ids()` on init. Guards prevent double-closing 1-share trades and zero-distance risk calculations.

4. **TradeState machine**: Only transitions in `VALID_TRANSITIONS` are allowed. Terminal states (`CLOSED`, `REJECTED`, `DROPPED`, `CANCELLED`) cannot transition further.

5. **Risk decision TTL**: `RiskDecision` has `expires_at`; stale decisions are not valid for execution.

6. **upsert_trade ON CONFLICT**: Updates all mutable fields — state, fill_price, slippage_pct, shares, stop_loss, take_profit, close_price, close_reason, realized_pnl, realized_pnl_pct, opened_at, closed_at, agent_reasoning.

---

## § AGENT CONVENTIONS

### BaseAgent (`src/agents/base_agent.py`)
- All agents inherit from `BaseAgent`.
- LLM provider selected via `LLM_PROVIDER` env var (`"anthropic"` default, `"openrouter"`).
- Every subclass **must** implement `_fallback(context: str) -> dict` for LLM-unavailable mode.
- `_sanitize_external_text()` must be called on all external/prior-agent text before injecting into prompts (prompt injection defense).
- `call_llm()` automatically falls back to `_fallback()` after `MAX_RETRIES=2` failures.
- `update_context(context)` is called every cycle by the orchestrator to refresh performance context.

### Dependency Injection
- `TradingOrchestrator` accepts `portfolio`, `trade_store`, and `risk_gate` as optional keyword-only constructor params — use these in tests instead of monkeypatching.
- `PortfolioManagerAgent` accepts `market_feed` as an injectable param — pass a mock in tests.

### LLM Response Format
- All agents return JSON; `_parse_json()` strips markdown fences automatically.
- Fallback responses are deterministic rule-based dicts — not stubs.

---

## § ENVIRONMENT VARIABLES

```
ANTHROPIC_API_KEY      # Required for LLM mode (Anthropic)
OPENROUTER_API_KEY     # Required for LLM mode (OpenRouter)
LLM_PROVIDER           # "anthropic" (default) or "openrouter"
OPENROUTER_MODEL       # Model slug for OpenRouter
LLM_TIMEOUT_SECONDS    # LLM call timeout (default: 30.0)
STARTING_CAPITAL       # Portfolio starting capital (default: 10000.00)
WATCHLIST              # Comma-separated symbols (default: AAPL,SPY,QQQ,NVDA)
MAX_CYCLES             # 0 = infinite (default: 0)
LOG_LEVEL              # DEBUG/INFO/WARNING (default: INFO)
# Risk gate tuning:
MAX_LOSS_PCT_PER_TRADE  # default: 0.02
MAX_OPEN_POSITIONS      # default: 5
MAX_TOTAL_EXPOSURE_PCT  # default: 0.80
MAX_CONSECUTIVE_LOSSES  # default: 3
MIN_RISK_REWARD         # default: 1.5
MIN_CONFIDENCE          # default: 0.55
```

All secrets go in `.env` (gitignored) — never in source code.

---

## § TESTING CONVENTIONS

- Test files live in `tests/` with no `__init__.py`.
- Naming: `test_<module>.py` → `Test<Class>` → `test_<method>_<scenario>`.
- `pytest-asyncio` is configured `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed.
- `pyproject.toml` excludes `src/display/*`, `src/main.py`, `src/orchestrator.py` from coverage.
- **Coverage target: 90%+** (last known state: 90% overall, 266 tests passing).
- Use `pytest-mock` (`mocker` fixture) for all mocking — do not import `unittest.mock` directly.
- LLM calls must always be mocked in tests; never make real API calls from the test suite.
- Inject dependencies via constructor params (DI), not monkeypatching instance attributes.

### Coverage Gaps to Close (known open issues)
- Issue #55: IndicatorEngine — MACD/Bollinger/EMA/ATR untested paths
- Issue #58: PerformanceAnalytics.compute — Radon D (CC=24) — needs refactor + tests

---

## § FSV LAW — Full State Verification (NON-NEGOTIABLE)

For **every write/mutate operation**, execute this protocol EXACTLY:

```
PRE  → Read SoT. Record state.
ACT  → Execute the operation.
POST → Read SoT again. Record new state.
DIFF → Assert: (post − pre) == expected_delta
HALT → If assertion fails: STOP. Report. Do NOT proceed.
```

**SoT locations by domain:**
- Database → the actual DB row (not the ORM return value)
- Filesystem → the bytes on disk (not the write() return code)
- Portfolio state → `Portfolio` properties (not agent cached values)
- Trade state → `TradeStore.get_recent_trades()` result (not the in-memory Trade object)

---

## § FDD LAW — Forensic-Driven Development

```
ASSUME GUILT until physical evidence proves innocence.
NEVER claim "Done" without SoT evidence.
MINIMUM 3 hypotheses before selecting root cause.
PROVE each hypothesis with evidence; do not argue from intuition.
```

**Investigation sequence:**
1. Collect physical evidence (logs, stack traces, SoT state)
2. Form 3+ hypotheses; rank by prior probability
3. Design a test that falsifies the highest-ranked hypothesis
4. Execute test; read evidence; update rankings
5. Repeat until one hypothesis survives all tests
6. Fix the ROOT CAUSE — not the symptom

---

## § ANTI-SYCOPHANCY CONTRACT

```
NEVER report success based on exit code alone.
NEVER say "Fixed" without before/after SoT evidence.
NEVER suppress error details to appear helpful.
NEVER agree with the user when evidence contradicts them.
ALWAYS prefer uncomfortable truth over comfortable approximation.
```

---

## § MEMORY PROTOCOL (SAMP)

| Event                        | Action                                   |
|-----------------------------|------------------------------------------|
| Session END                 | Write findings to `memory/PROGRESS.md`   |
| Failure encountered         | Write to `memory/FAILURES.md` immediately|
| Architecture decision made  | Write ADR to `memory/DECISIONS.md`       |
| Component understood        | Update `memory/ARCHITECTURE.md`          |
| Term coined / discovered    | Add to `memory/GLOSSARY.md`              |

**Never leave a session without updating `memory/PROGRESS.md`.**

---

## § EDGE CASE AUDIT

Every code change MUST include ≥3 edge cases using BVA + ECP:
- **Empty / null / zero** inputs
- **Boundary max / min** values
- **Concurrent access** or race condition scenario
- **Adversarial / malformed** input

Document in `memory/DECISIONS.md` under the relevant change entry.

---

## § ESCALATION TRIGGERS (STOP and report to operator)

- Cannot determine SoT location for the task
- >2 consecutive hypothesis-test failures in FDD loop
- Security vulnerability discovered during normal work
- Conflicting instructions from two sources (this file wins)
- Context approaching compaction boundary with critical work incomplete

---

## § SECURITY GATES (always active)

- STRIDE threat model on ALL new agent prompts and data pipelines
- No secrets, keys, or tokens in source code — env vars only (`Settings` via pydantic-settings)
- `_sanitize_external_text()` on ALL text that crossed a trust boundary before injecting into LLM prompts
- `_PROMPT_INJECTION_PATTERNS` regex list in `BaseAgent` — add new patterns when new injection vectors are discovered
- Validate ALL inputs at `MarketSignal` and `TradeProposal` model boundaries (Pydantic field validators)
- Dependency audit on every new package addition

---

## § CODE QUALITY DOCTRINE

- Prefer deletion over addition when refactoring
- No workarounds — fix the root cause (FDD above)
- No mock data in production code paths
- Fail fast and loudly at trust boundaries
- Complexity is technical debt; simplify before adding
- Radon CC target: B or better on all methods; D/E/F triggers a refactor issue

---

## § KNOWN TECHNICAL DEBT

| ID  | Location                            | Issue                                          | Priority |
|-----|-------------------------------------|------------------------------------------------|----------|
| #54 | `PortfolioManagerAgent.monitor_cycle` | 26 uncovered lines                           | medium   |
| #55 | `IndicatorEngine`                   | 39% miss rate on MACD/BB/EMA/ATR paths        | medium   |
| #56 | `TradeStore` audit tables           | 16 uncovered lines                            | medium   |
| #57 | `PortfolioManagerAgent.MarketFeed`  | Fixed via DI (closed)                         | done     |
| #58 | `PerformanceAnalytics.compute`      | Radon D (CC=24) — refactored to B(6)          | done     |

---

*Last updated: 2026-05-27 — reflects codebase state after session claude/autonomous-auditor-skills-cJDLY*
