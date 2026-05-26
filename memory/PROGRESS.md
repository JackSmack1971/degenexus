# PROGRESS

## Session: 2026-05-26 (claude/agent-issues-queue-DHSOl)

### Completed — All source:agent issues resolved (5/5)

| # | Title | Status | Commit |
|---|-------|--------|--------|
| #47 | portfolio.py: missing Position/Trade imports → get_type_hints() NameError | ✅ closed | ffd486a |
| #50 | QuantAgent._fallback_proposal: 0% coverage | ✅ closed | eefa3cf |
| #49 | ContextInjector (20% cov) + PerformanceAnalytics (38% cov) | ✅ closed | ffb9daa |
| #48 | 23+ unused imports across 14 production files | ✅ closed | ac9ce5e |
| #51 | TradingOrchestrator hard-instantiates all 11 subsystems — no DI | ✅ closed | c231882 |

### Previous session completed issues
| #40 | 1-share partial TP crashes monitor_cycle | ✅ closed | 8f6c38b |
| #28 | Dead guard + zero-distance partial TP trigger | ✅ closed | 8f6c38b |
| #42 | upsert_trade ON CONFLICT omits shares | ✅ closed | d8554bf |
| #41 | PARTIALLY_CLOSED not persisted on restart | ✅ closed | 179f759 |
| #36 | direction field: raw str, invalid values propagate | ✅ closed | fc46d28 |
| #29 | SHORT direction tests missing | ✅ closed | 30ed433 |
| #37 | 6 agent files zero test coverage | ✅ closed | 252ff75 |

### Key Changes Made This Session
- `src/core/portfolio.py`: Added `from ..models.trade import Position, Trade` (real import, not TYPE_CHECKING) so `get_type_hints()` resolves at runtime
- `src/models/signals.py`: Fixed `_normalise_direction` validator to use `v.value` for enum inputs (Python 3.11 `str(Direction.LONG)` returns `"Direction.LONG"` not `"LONG"`); removed unused `TYPE_CHECKING/AgentID` block
- `tests/test_quant_agent.py`: +7 tests in `TestFallbackProposal` class covering LONG/SHORT arithmetic, zero/negative price, insufficient cash, min-1-share floor, field consistency
- `tests/test_performance_analytics.py`: New (17 tests) covering compute(), _compute_streak(), _compute_symbol_stats()
- `tests/test_context_injector.py`: New (26 tests) covering build_context() all branches, _streak_string()
- 14 production files: Removed 30+ unused imports (pyflakes clean)
- `src/orchestrator.py`: Added `portfolio`, `trade_store`, `risk_gate` as optional keyword-only DI params; removed redundant `hasattr(self, "portfolio")` guards

### Test State
265 tests pass, 3 skipped (265 vs 222 start of session = 43 new tests added)
Branch: claude/agent-issues-queue-DHSOl
pyflakes src/ → CLEAN (0 warnings)
