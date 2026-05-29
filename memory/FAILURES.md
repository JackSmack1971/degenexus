# FAILURES

## F-016 — 2026-05-29 — AGENTS.md coverage gate stale after PR #125 raised CI threshold

- **Failure mode:** AGENTS.md documented `--cov-fail-under=50` while CI enforced `--cov-fail-under=90` since PR #125 merged.
- **Physical evidence:** `grep "cov-fail-under" AGENTS.md` → `50`; `grep "cov-fail-under" .github/workflows/ci.yml` → `90`.
- **Root cause:** CI threshold updated in PR #125 without a corresponding AGENTS.md edit.
- **Blast radius:** Contributors reading AGENTS.md believe 51% coverage is sufficient; PRs could drop coverage from 98% toward 50% believing CI will pass.
- **Issue:** #137
- **Fix:** Updated AGENTS.md line 20 to `--cov-fail-under=90`.
- **Never repeat:** When changing CI coverage thresholds, update AGENTS.md in the same PR.

---

## F-014 — 2026-05-29 — Open forensic audit drift after issue #105/#106 remediation

- **Failure mode:** Six source:agent issues (#137-#142) remained open with no open PRs: stale coverage docs, stale mypy overrides, non-configurable risk decision TTL, dead `HardRuleViolation` API, incorrect README module paths, and missing PR templates referenced by AGENTS.md.
- **Physical evidence:** GitHub REST API returned open issues #137-#142 and zero open PRs; local SoT scans found `--cov-fail-under=50` in AGENTS.md, `langchain` mypy overrides in `pyproject.toml`, missing `RISK_DECISION_TTL_SECONDS` in `RiskLimits.from_env()`, `HardRuleViolation` only defined/exported, stale README paths, and absent `.github/PULL_REQUEST_TEMPLATE/` directory.
- **Root cause:** Prior issue-specific fixes updated CI/dependencies/runtime policy but did not propagate the state delta to adjacent contributor docs, type-checker config, and GitHub workflow scaffolding.
- **Blast radius:** Contributor onboarding and PR creation could follow stale instructions; risk TTL could not be tuned through supported env configuration; static type policy silently retained removed dependency waivers.
- **Issues:** #137, #138, #139, #140, #141, #142
- **Fix:** Synchronize docs/config/templates with current SoT, add env-backed TTL mapping with tests, and remove the unused exception contract.
- **Never repeat:** After resolving a forensic issue that changes CI thresholds, dependencies, or governance workflows, grep adjacent docs/config/templates and update memory in the same PR.

## F-011 — 2026-05-28 — IndicatorEngine success-path coverage 87% regression from #55

- **Failure mode:** `src/data/indicators.py` is at 87% coverage (11 missed lines: 48-49, 57-60, 77, 103-104, 115-116) — below 90% threshold. Regression from closed issue #55.
- **Physical evidence:** `python3 -m pytest tests/ --cov=src --cov-report=term-missing` on HEAD `c68e47d`. Four tests in `tests/test_indicators.py` guard happy paths with `pytest.skip("ta library not available")` instead of sys.modules injection. No sys.modules-injected success-path tests exist for MACD (lines 57-60) or EMA (lines 103-104).
- **Root cause:** (1) RSI/ATR/BB success-path tests use skip guards instead of the `_ta_patch()` sys.modules injection pattern already established in the file; (2) MACD/EMA happy paths have no sys.modules-injected coverage at all, unlike Bollinger which uses `_make_bollinger_result()`.
- **Blast radius:** Any CI environment where `ta` wheel cannot be built will have 87% indicators coverage. MACD/EMA success paths are untested in ALL environments.
- **Issue:** #101
- **Never repeat:** When adding ta-dependent tests that use `pytest.skip` as a guard, instead use `_ta_patch()` sys.modules injection. Exception-path tests are insufficient — also test the happy path via mock injection.

---

## F-012 — 2026-05-28 — CLAUDE.md § KNOWN TECHNICAL DEBT table stale after issue closures

- **Failure mode:** CLAUDE.md lists issues #54, #55, #56 as "medium" (open) but all three were closed 2026-05-26.
- **Physical evidence:** CLAUDE.md line `*Last updated: 2026-05-27*`; GitHub shows #54/#55/#56 closed `2026-05-26`. Issues #57/#58 are correctly marked "done" in the same table.
- **Root cause:** Table was written at issue-creation time; not updated after the 2026-05-26 session closed the issues.
- **Blast radius:** Future agents reading CLAUDE.md will treat #54/#55/#56 as open work items; may re-attempt closed fixes.
- **Issue:** #102
- **Never repeat:** At session end, update CLAUDE.md § KNOWN TECHNICAL DEBT whenever issues in that table change state.

---

## F-010 — 2026-05-28 — src/main.py mutates os.environ["STARTING_CAPITAL"] bypassing Portfolio DI injection

- **Failure mode:** `main.py:142` writes `os.environ["STARTING_CAPITAL"] = str(args.capital)` as a workaround for Portfolio capital propagation. The `portfolio=` DI injection param was added in issue #51 but `main.py` was never updated to use it.
- **Physical evidence:** `src/main.py:142` + `src/core/portfolio.py:34` (os.getenv fallback) + `src/orchestrator.py:58` (DI injection point exists).
- **Root cause:** `main.py` written before DI fix (#51); not updated after DI became available.
- **Blast radius:** Global `os.environ` mutation; implicit capital config flow; DI injection intent obscured; env write is now dead code when Portfolio DI is used.
- **Issue:** #91
- **Never repeat:** After adding DI injection to any orchestrator subsystem, update `main.py` to pass the subsystem via DI instead of env mutation.

---

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

## F-013 — Conditioned Execution Must Restamp and Revalidate Proposal Hashes

**Date:** 2026-05-28
**Issue:** #108
**Failure mode:** `ExecutionAgent.execute()` validated the original proposal hash, then applied Risk Manager size-reduction conditions that recomputed `TradeProposal.proposal_hash` without keeping `RiskDecision.proposal_hash` in sync. Conditioned fills could therefore execute proposal B while retaining approval metadata for proposal A.
**Prevention:** Whenever execution conditions mutate proposal fields that participate in `compute_hash()`, restamp the risk decision hash to the effective proposal and re-run `ExecutionGate.validate()` before constructing the trade/fill. Cover null/no-op, min/max reduction, and duplicate-condition paths in execution tests.
