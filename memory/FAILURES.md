# FAILURES

Known failure modes encountered across audit sessions. Load at every turn-start to avoid repeating investigation work.

---

## F-001 — `ta` dependency build failure (Python 3.11 Linux, 2026-05-27)

**Symptom:** `pip install -r requirements.txt` fails with:
```
ERROR: Could not build wheels for ta
AttributeError: install_layout
```
**Impact:** 11 tests in `test_indicators.py` fail with `ModuleNotFoundError: No module named 'ta'`
**Root cause:** `ta>=0.11.0` requires C extension compilation. No pre-built wheel available for Python 3.11 on this Linux platform.
**Known workaround:** Run tests with `--ignore=tests/test_indicators.py` to get passing suite (coverage 90%+)
**Tracking issue:** #66
**Status:** OPEN — downstream fix required

---

## F-002 — `pydantic_settings` not in default environment (2026-05-27)

**Symptom:** `ModuleNotFoundError: No module named 'pydantic_settings'` during test collection
**Impact:** 10 test files fail to collect
**Root cause:** `pydantic-settings` is a separate package from `pydantic` (Pydantic v2 split), not auto-installed
**Resolution:** `pip install pydantic-settings` — resolves immediately
**Status:** RESOLVED (install required in fresh containers)

---

## F-003 — `DataAnalystAgent.__new__` workaround in tests (discovered 2026-05-27)

**Symptom:** `tests/test_data_analyst.py` uses `DataAnalystAgent.__new__(DataAnalystAgent)` to bypass constructor
**Impact:** `analyze()` and `_build_bar_summary()` never called in tests (19% coverage miss)
**Root cause:** `DataAnalystAgent.__init__` hard-instantiates `MarketFeed` and `IndicatorEngine` — no DI
**Tracking issue:** #69
**Status:** OPEN — DI fix required

---

## F-004 — orchestrator.py:99 unguarded `.value` on Optional[CloseReason] (2026-05-27)

**Symptom:** mypy `[union-attr]` error; potential runtime `AttributeError` in production
**Impact:** Crash in `run_cycle()` heartbeat if `close_reason=None` reaches line 99
**Root cause:** `Trade.close_reason: Optional[CloseReason] = None` but orchestrator accesses `.value` without None guard
**Tracking issue:** #67
**Status:** OPEN — None guard required

---

## F-005 — mypy type violations in execution_agent + data_analyst (2026-05-27)

**Symptom:** 
- `execution_agent.py:48`: `Optional[RiskDecision]` passed to param requiring `RiskDecision`
- `data_analyst.py:119`: `str` passed where `Direction` expected
**Impact:** Static contract broken; latent runtime risk if validator removed
**Root cause:** Type narrowing missing after `gate.validate()` call; Direction enum not explicitly constructed
**Tracking issue:** #68
**Status:** OPEN — assert + explicit enum construction required

---

## F-007 — CLAUDE.md @import + .claude/rules/ reference missing files (2026-05-27)

**Symptom:** Turn-start ritual Step 5 ("LOAD relevant .claude/rules/") fails silently — `.claude/rules/` directory does not exist; `.claude/imports/doctrine-summary.md` does not exist
**Impact:** STRIDE security rules undefined; @import directive silently fails; future doctrine-summary content unreachable
**Root cause:** CLAUDE.md was written from a template with @import and rules references pointing to files never created
**Tracking issue:** #70
**Status:** OPEN — create missing files or remove dead references

---

## F-006 — asyncio_mode config warning in pytest (2026-05-27)

**Symptom:** `PytestConfigWarning: Unknown config option: asyncio_mode`
**Impact:** Warning only — tests still run
**Root cause:** `pytest-asyncio` version mismatch with `asyncio_mode` config key in `pyproject.toml`
**Status:** NON-BLOCKING — cosmetic warning
