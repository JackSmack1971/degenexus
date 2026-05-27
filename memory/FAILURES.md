# FAILURES

## 2026-05-27 — Audit orchestration blocked by missing GitHub mutation tooling
- **Failure mode:** Required forensic mutations (issue create/update) could not be executed from this environment.
- **Physical evidence:** `gh` is not installed (`gh: command not found`), and `git remote -v` shows no configured remote, so repository default-branch metadata and authenticated mutation path are unavailable.
- **Root cause:** Environment/tooling gap, not repository code behavior.
- **Blast radius:** Audit can collect read-only evidence but cannot complete mandatory “create/update forensic issue” handoff when a new anomaly requires issue mutation.
- **Containment:** Record all anomalies with duplicate mapping to existing open issues where possible; mark session `completion_verdict=blocked` if any anomaly cannot be mutated per doctrine.

---

## F-001 — ta-dependent test failures from dotted-path patch (resolved by sys.modules injection, codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Symptom:** 11 tests in `TestBollingerPriceClassification` + `TestRSIExceptionFallback` fail with `ModuleNotFoundError: No module named 'ta'` when ta is not installed.  
**Root cause:** Tests used `patch("ta.volatility.BollingerBands", ...)` — Python's `patch()` resolves dotted paths by importing the root module at patch-time, requiring `ta` to be importable even for mock tests.  
**Fix:** Replaced dotted-path string patches with `sys.modules` injection via `_ta_patch()` helper. Tests pass whether or not `ta` is installed.  
**Note:** `setuptools<65` pin was attempted as secondary fix but caused CI `pip-audit` failures — removed (see F-003).  
**Never repeat:** Do not use `patch("some.module.ClassName", ...)` when the parent module may not be installed — use `sys.modules` injection instead.

---

## F-002 — Tests using `mocker.patch` on uninstalled module dotted paths fail at patch resolution (resolved by codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Symptom:** `mocker.patch("ta.momentum.RSIIndicator", side_effect=...)` throws `ModuleNotFoundError` before the test body executes when `ta` is not installed.  
**Root cause:** `unittest.mock.patch` with a dotted string resolves the target module by importing it, not by inspecting sys.modules.  
**Fix:** Use `patch.dict(sys.modules, {"ta": fake_ta, "ta.momentum": fake_mom})` to inject the mock module before the code under test tries to import it.  
**Never repeat:** All indicator tests now use `_ta_patch()` helper for consistent sys.modules injection.

---

## F-003 — setuptools<65 pin in requirements.txt causes pip-audit CVE failures in CI (learned from codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Symptom:** CI "test" job fails on `pip-audit -r requirements.txt` after pinning `setuptools<65`.  
**Root cause:** setuptools versions <65 have known CVEs. The pin causes CI's fresh-install run (new pip cache key) to flag these. Other PRs reuse the cached pip environment from main and bypass the fresh ta build.  
**Fix:** Remove `setuptools<65` from requirements.txt. Rely on sys.modules injection for test isolation.  
**Never repeat:** Do not add `setuptools<65` (or other pinned versions of core packaging tools with known CVEs) to requirements.txt — use test-isolation patterns instead.

## 2026-05-27 — GitHub governance mutation blocker persists in audit environment
- **Failure mode:** Cannot perform required create/update/search-for-duplicates workflow against GitHub issues from this runtime.
- **Physical evidence:** `gh --version` fails (`command not found`); unauthenticated `GET /repos/JackSmack1971/degenexus/issues?state=open` returned `[]`.
- **Root cause:** External tooling/auth visibility gap rather than repository code defect.
- **Blast radius:** Forensic anomaly-to-issue handoff can only proceed when authenticated GitHub mutation tooling is present.
- **Containment:** Restrict this session to evidence capture + memory synchronization + manifest update.

---

## 2026-05-27 — FDD+FSV audit-only findings (claude/fdd-fsv-audit-degenexus-rM1g1)

### F-004 — 27 ruff lint violations in test suite (F401/F811/F841)
- **Failure mode:** `ruff check src/ tests/` exits 1 with 27 findings. All are in test files; `pyflakes src/` passes.
- **Physical evidence:** 13 test files affected; all F401 (unused import), F811 (redefinition), or F841 (assigned-but-unused). 23 auto-fixable.
- **Root cause:** No ruff/static lint gate enforced on test files at commit boundary; unused imports accumulated from refactors.
- **Blast radius:** CI lint gate non-compliance; dead test imports can mask brittle tests.
- **Issue:** #84

### F-005 — 4 source files below 90% coverage threshold
- **Failure mode:** base_agent.py(89%), quant_agent.py(80%), risk_manager.py(86%), market_feed.py(87%) all below the 90% target.
- **Physical evidence:** `pytest --cov=src --cov-report=term-missing` — uncovered lines are LLM-provider dispatch branches, error handlers, and yfinance network call.
- **Root cause:** Tests mock at `call_llm()` level, above the untested provider-dispatch/error-handler/network code paths.
- **Blast radius:** Production fallback paths untested; `quant_agent._parse_proposal` error path could silently return None.
- **Issue:** #85

### F-006 — mypy strict mode fails with 7 import-untyped errors
- **Failure mode:** `python3 -m mypy src/` exits 1 with 7 errors; passes only with `--ignore-missing-imports`.
- **Physical evidence:** Missing stubs: pandas-stubs, types-requests; no py.typed marker for ta, yfinance.
- **Root cause:** No stub packages in requirements.txt; no `[tool.mypy]` config in pyproject.toml.
- **Blast radius:** mypy gate cannot run without suppression flag; typed contracts in indicators.py/market_feed.py unverifiable.
- **Issue:** #86

### F-007 — src/get-model-list.py reads API key via os.environ.get() — Security Policy violation
- **Failure mode:** `src/get-model-list.py:6` — `API_KEY = os.environ.get("OPENROUTER_API_KEY")` bypasses `Settings` pydantic-settings.
- **Physical evidence:** File absent from CLAUDE.md architecture; excluded from coverage; makes live external HTTP calls; bypasses `openrouter_client.py`.
- **Root cause:** Ad-hoc utility script added without security review; no `src.core.settings` import.
- **Blast radius:** Secrets policy violation; sets precedent for direct env access; latent key exposure in logs/reprs.
- **Issue:** #87

### F-008 — orchestrator.py docstring + ARCHITECTURE.md show stale 8-phase cycle
- **Failure mode:** Both show `RISK_EVALUATE` where `RISK_HARD_GATE → RISK_EVALUATE` should be; both show phantom `LEARN` phase.
- **Physical evidence:** `orchestrator.py:40` docstring; `memory/ARCHITECTURE.md:6` — both have `...QUANT_DESIGN → RISK_EVALUATE...→ LEARN`.
- **Root cause:** Docstring and ARCHITECTURE.md predate RISK_HARD_GATE introduction; LEARN phase was planned but never implemented.
- **Blast radius:** Wrong mental model for new developers; RISK_HARD_GATE "is FINAL" invariant invisible in docs.
- **Remediation applied this session:** ARCHITECTURE.md updated to correct phase sequence. orchestrator.py docstring still needs a code fix (issue #88).
- **Issue:** #88

### F-009 — pyproject.toml requires-python=">=3.12" but runtime is Python 3.11.15
- **Failure mode:** `python3 --version` → 3.11.15; `pyproject.toml` → `requires-python = ">=3.12"`.
- **Physical evidence:** 368 tests pass on 3.11.15; no hard 3.12-exclusive syntax in tested paths. `pip install .` on Python 3.11 would fail the version gate.
- **Root cause:** Runtime environment provisioned with Python 3.11 despite CLAUDE.md declaring "Runtime: Python 3.12".
- **Blast radius:** Contributors on Python 3.11 cannot install via pyproject.toml; subtle behavioral divergences possible.
- **Issue:** #89
