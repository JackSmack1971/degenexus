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

## 2026-05-27 — FDD+FSV audit anomalies (codex)
- **Failure mode:** Quality gates fail in current workspace: `ruff check src tests` reports 27 violations (unused imports/redefinitions/unused vars in tests).
- **Physical evidence:** Command output includes F401/F811/F841 across test modules (e.g., `tests/conftest.py`, `tests/test_execution_gate.py`, `tests/test_trade_store.py`).
- **Root cause:** Test-suite hygiene drift; lint gate not enforced at commit boundary.
- **Blast radius:** CI/static-quality non-compliance; can mask real regressions.
- **Containment:** Open/update forensic issue and defer code fixes to implementation agent.

- **Failure mode:** Type-check gate fails: `mypy src` reports 6 errors in 2 files due to missing third-party type stubs (`pandas`, `ta`, `yfinance`).
- **Physical evidence:** `import-untyped` diagnostics in `src/data/indicators.py` and `src/data/market_feed.py`.
- **Root cause:** Strict mypy gate without complete stub/typing strategy for external deps.
- **Blast radius:** Static-type gate cannot pass reliably; weakens typed contracts.
- **Containment:** Track as forensic issue; implementation agent to add stub deps or config policy.

- **Failure mode:** Required audit tools missing: `radon` and `pip-audit` unavailable in environment.
- **Physical evidence:** `python3 -m radon cc src/ -a` => `No module named radon`; `pip-audit` => `command not found`.
- **Root cause:** Incomplete auditor runtime toolchain.
- **Blast radius:** Cannot verify complexity and dependency-vulnerability gates.
- **Containment:** Track as environment blocker; rerun in provisioned environment.
