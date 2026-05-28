# Audit Manifest — System-Wide Audit
**Session:** `claude/system-wide-audit-A6EtF`  
**Date:** 2026-05-28  
**Auditor:** system-wide audit agent  
**Branch:** `claude/system-wide-audit-A6EtF`  
**HEAD at audit start:** `d11d20b91540b3d19ae92da8a4f8a77c8903421e`

---

## Baseline

| Item | Value |
|------|-------|
| Repo | JackSmack1971/degenexus |
| Default branch | main |
| Audit branch | claude/system-wide-audit-A6EtF |
| HEAD SHA | d11d20b91540b3d19ae92da8a4f8a77c8903421e |
| Git status at start | clean (no uncommitted changes) |
| Open issues at start | 2 (#101, #102) |
| Open PRs at start | 0 |
| Python runtime (cloud env) | 3.11.15 |
| Prior test result | 389 passed, 4 skipped |
| Prior coverage | TOTAL 97% |
| Prior ruff | CLEAN |
| Prior mypy | CLEAN (35 source files) |
| Prior pyflakes | CLEAN |
| Prior radon | A average (2.951) |
| Prior pip-audit | No known vulnerabilities |
| Tooling gap | pytest/ruff/mypy/pyflakes not on system Python — static reads used instead |

---

## Coverage Checklist (10 Passes)

| Pass | Domain | Status | Notes |
|------|--------|--------|-------|
| 1 | Orientation: ecosystem, entrypoints, docs | ✅ | README, AGENTS.md, CLAUDE.md, main.py, orchestrator.py reviewed |
| 2 | Deps: requirements.txt, pyproject.toml, locks | ✅ | Unused langchain deps found; pip-audit clean per prior session |
| 3 | Build/test/CI: ci.yml, codeql.yml, pyproject.toml | ✅ | Three CI gaps found (threshold, lint gate, version matrix) |
| 4 | Runtime: logic, edge cases, validation, states | ✅ | SHORT partial TP bug found; hash bypass found |
| 5 | Sec/privacy: secrets, env, injection, auth | ✅ | No new secrets issues; get-model-list.py confirmed fixed (#87) |
| 6 | Arch/maint: coupling, cycles, contracts | ✅ | hasattr guard in orchestrator:302 noted (investigated, not confirmed) |
| 7 | Obs/ops: logs, retry, timeout | ✅ | LLM timeout/retry in BaseAgent confirmed correct |
| 8 | Docs/UX: README, AGENTS.md, CLAUDE.md | ✅ | Stale Python version, wrong env var, wrong dep name in README+AGENTS.md |
| 9 | DX: setup, tooling, onboarding | ✅ | No lint gate in CI confirmed; CI Python version gap found |
| 10 | Final: dedupe, evidence, manifest | ✅ | This manifest |

---

## Issues Created (7 new)

| # | Title | Category | Severity | Confidence |
|---|-------|----------|----------|------------|
| [#104](https://github.com/JackSmack1971/degenexus/issues/104) | `check_partial_tp` wrong formula for SHORT — fires immediately at entry | BUG | P1 | high |
| [#105](https://github.com/JackSmack1971/degenexus/issues/105) | CI `--cov-fail-under=50` far below documented 90%+ target | CI | P2 | high |
| [#106](https://github.com/JackSmack1971/degenexus/issues/106) | `langchain` and `langchain-anthropic` unused — unneeded supply-chain surface | DEPS | P2 | high |
| [#107](https://github.com/JackSmack1971/degenexus/issues/107) | No ruff/mypy/pyflakes gate in CI — quality regressions pass silently | CI | P2 | high |
| [#108](https://github.com/JackSmack1971/degenexus/issues/108) | `_apply_conditions` recomputes hash but ExecutionGate not re-validated — audit trail mismatch | BUG | P2 | high |
| [#109](https://github.com/JackSmack1971/degenexus/issues/109) | README.md and AGENTS.md stale: wrong Python version, wrong env var, wrong dep name | DOCS | P3 | high |
| [#110](https://github.com/JackSmack1971/degenexus/issues/110) | CI tests Python 3.12 only — no 3.11 matrix after pyproject.toml requires-python fix | CI | P3 | high |

---

## Duplicates Found (0)

All 7 findings were confirmed novel against:
- Open issues (#101, #102)
- GitHub issue search by keyword/path/symptom for each finding
- PROGRESS.md and FAILURES.md history of prior sessions

---

## Investigated but Not Confirmed

| Finding | Reason Not Filed |
|---------|-----------------|
| `orchestrator.py:302` `hasattr(self, "portfolio_manager")` defensive check | Legitimate guard: `_build_context()` is called during `__init__` before `portfolio_manager` is assigned (line 64 vs 71); not a bug |
| `TradeStore.get_recent_trades()` excludes `PARTIALLY_CLOSED` | Intentional — performance stats only use terminal trades; partially closed trades remain open |
| `src/core/openrouter_client.py` ALLOWED_FREE_MODELS hardcoded list | Maintenance concern but no confirmed bug; models were verified against actual OpenRouter API in prior sessions |
| `Portfolio.__init__` uses `os.getenv("STARTING_CAPITAL")` fallback | By design per CLAUDE.md SoT table (matches `RiskLimits.from_env()` pattern); Settings class is for LLM secrets only |
| `_parse_json` markdown fence stripping edge cases | Handles all common LLM response formats; no confirmed failure path found |
| CI `python-version: "3.12"` vs AGENTS.md "Target Python 3.12+" | Both are stale after #89 — filed as one DOCS issue (#109 covers AGENTS.md) |

---

## Tooling Gaps

| Tool | Status | Impact |
|------|--------|--------|
| pytest | Not on system Python `/usr/local/bin/python3` | Could not run test suite live; relied on PROGRESS.md for prior pass state |
| ruff | Not on system Python | Could not run live lint; relied on source inspection |
| mypy | Not on system Python | Could not run live type check; relied on source inspection |
| pyflakes | Not on system Python | Could not run live; relied on source inspection |
| radon | Not on system Python | Could not run live; relied on prior session result (A average) |
| pip-audit | Not on system Python | Could not run live; relied on prior session result (clean) |

**Mitigation:** All 10 audit passes performed via static file reading, `grep`/`find` bash commands, and GitHub MCP issue search. Evidence quality is high for all filed issues — each finding has direct source-code evidence with file paths and line numbers.

---

## Safety Check

| Check | Result |
|-------|--------|
| Source/test code edited | NO |
| Commits created | NO (memory artifacts only, committed below) |
| PRs created | NO |
| Issues closed/merged | NO |
| Issues deleted | NO |
| Code pushed to main | NO |
| Secrets accessed | NO |
| Forbidden actions performed | NONE |
| Issues created without confirmed evidence | NONE — all 7 have direct path+line evidence |

---

*Audit complete. 7 issues created. All findings novel. All evidence confirmed.*
