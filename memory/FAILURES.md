# FAILURES

## 2026-05-27 — Audit orchestration blocked by missing GitHub mutation tooling
- **Failure mode:** Required forensic mutations (issue create/update) could not be executed from this environment.
- **Physical evidence:** `gh` is not installed (`gh: command not found`), and `git remote -v` shows no configured remote, so repository default-branch metadata and authenticated mutation path are unavailable.
- **Root cause:** Environment/tooling gap, not repository code behavior.
- **Blast radius:** Audit can collect read-only evidence but cannot complete mandatory “create/update forensic issue” handoff when a new anomaly requires issue mutation.
- **Containment:** Record all anomalies with duplicate mapping to existing open issues where possible; mark session `completion_verdict=blocked` if any anomaly cannot be mutated per doctrine.

---

## F-001 — ta wheel build fails on setuptools>=65 / Python 3.11 (resolved by codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Symptom:** `pip install ta>=0.11.0` raises `AttributeError: install_layout` in distutils C-extension build path when setuptools>=65.  
**Root cause:** `ta` uses legacy distutils commands that are incompatible with setuptools>=65 which removed the `install_layout` attribute.  
**Blast radius:** 11 tests in `TestBollingerPriceClassification` + `TestRSIExceptionFallback` fail with `ModuleNotFoundError: No module named 'ta'` because `patch("ta.volatility.BollingerBands", ...)` resolves the dotted path at patch-time, requiring `ta` to be importable.  
**Fix:** (a) Pin `setuptools<65` in `requirements.txt` to allow `ta` wheel to build. (b) Replaced dotted-path string patches in the 11 failing tests with `sys.modules` injection via `_ta_patch()` helper — tests now pass regardless of whether `ta` is installed.  
**Never repeat:** Do not use `patch("some.module.ClassName", ...)` when the parent module may not be installed — use `sys.modules` injection instead.

---

## F-002 — Tests using `mocker.patch` on uninstalled module dotted paths fail at patch resolution (resolved by codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Symptom:** `mocker.patch("ta.momentum.RSIIndicator", side_effect=...)` throws `ModuleNotFoundError` before the test body executes when `ta` is not installed.  
**Root cause:** `unittest.mock.patch` with a dotted string resolves the target module by importing it, not by inspecting sys.modules.  
**Fix:** Use `patch.dict(sys.modules, {"ta": fake_ta, "ta.momentum": fake_mom})` to inject the mock module before the code under test tries to import it.  
**Never repeat:** All indicator tests now use `_ta_patch()` helper for consistent sys.modules injection.
