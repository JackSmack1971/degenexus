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
