# ARCHITECTURE

## System: DegenExus — AI Trading Debate Cycle

### 8-Phase Cycle (TradingOrchestrator)
SCAN → CEO_TRIAGE → QUANT_DESIGN → RISK_EVALUATE → CEO_FINAL → EXECUTE → MONITOR → LEARN

### Source of Truth Locations
- Capital / positions: `Portfolio` (in-memory, rebuilt from scratch on restart — no persistence)
- Trade history: `TradeStore` (SQLite WAL, `memory/trading_history.db`)
- Trade state machine: `TradeLifecycle` (enforces VALID_TRANSITIONS)

### Key Invariants
- Partial TP dedup: `_partial_tp_flags: set[str]` in PortfolioManagerAgent; seeded from DB (PARTIALLY_CLOSED trades) on init
- direction field: `Direction` enum (`LONG`|`SHORT`) enforced at `MarketSignal` and `TradeProposal` model boundaries via field_validator
- upsert_trade ON CONFLICT: updates state, fill_price, slippage_pct, shares, stop_loss, take_profit, close_price, close_reason, realized_pnl, realized_pnl_pct, opened_at, closed_at, agent_reasoning

### Agent Hierarchy
```
TradingOrchestrator
├── CEOAgent (LLM triage + counter-challenge)
├── DataAnalystAgent (market data → MarketSignal)
├── QuantAgent (proposal sizing, Kelly)
├── RiskManagerAgent (contextual LLM assessment, after hard gate)
├── ExecutionAgent (fill + slippage)
└── PortfolioManagerAgent (monitor open trades, partial/full TP/SL)
```

### Partial TP Flow
1. monitor_cycle: check_partial_tp → _execute_partial_tp → transition(PARTIALLY_CLOSED) → upsert_trade
2. Guard: shares_to_close >= trade.shares → skip (1-share trades delegated to TP/SL)
3. Guard: risk_distance == 0 → check_partial_tp returns False
4. On restart: _partial_tp_flags seeded from TradeStore.get_partially_closed_trade_ids()
