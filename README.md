# Degenexus

**A multi-agent AI trading desk simulator.**  
Specialized AI agents (Data Analyst, CEO, Quant, Risk Manager, Execution, and Portfolio Manager) run a structured 8-phase debate cycle to analyze markets, propose trades with strict risk controls, and manage a simulated portfolio — all inside your terminal. Every decision is logged for auditing.

```bash
# See a full debate cycle in one command (after the 2-minute setup)
python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY
```

## What You Get in the First 2 Minutes

Run the command above and watch the complete debate happen live in your terminal:

- The **Data Analyst** scans prices and technical indicators, then outputs market signals with confidence scores.
- The **CEO** immediately discards weak signals and keeps at most 2 strong ones per cycle.
- The **Quant** builds a trade proposal using recent performance data and half-Kelly position sizing.
- The **Risk Manager** first applies hard deterministic rules (these can **never** be overridden by the AI), then performs a second LLM review.
- The **CEO** may challenge exactly one contextual risk rejection.
- The **Execution** agent simulates the trade fill including realistic slippage.
- The **Portfolio Manager** tracks open positions, closes trades when needed, and reports portfolio value and PnL.

You receive a clean cycle summary showing trades taken, profit/loss, current portfolio value, and total events logged. The system is deliberately conservative and fully auditable.

> **Important**: This is a **simulation tool only**. It does **not** place real trades. Never use it with real money without extensive additional validation and your own risk controls.

## Quickstart (macOS, Linux, or Windows)

### Prerequisites
- Python 3.12 or newer
- An Anthropic API key (free tier available at https://console.anthropic.com — the system primarily uses Claude models)
- Git

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/JackSmack1971/degenexus.git
cd degenexus

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file with your API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
# (Replace sk-ant-your-key-here with your real key from Anthropic)

# 5. Run your first trading cycle (headless / log-only mode)
python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY,QQQ
```

**Expected observable success state**  
You will see colored terminal output showing each of the 8 debate phases, agent decisions, risk checks, any simulated trades, and a final cycle summary with portfolio value and PnL. No errors and a clean summary = success.

Want the live updating dashboard instead? Simply remove the `--no-dashboard` flag.

## Common Usage Examples

### List all available agents and their roles
```bash
python src/main.py --list-agents
```

### Run 5 cycles with a 30-second pause between them
```bash
python src/main.py --cycles 5 --delay 30 --symbols NVDA,TSLA
```

### Run continuously (great for long observation sessions)
```bash
python src/main.py --cycles 0 --delay 60
```

### Start with custom capital
```bash
python src/main.py --capital 50000 --cycles 3
```

All command-line flags can also be set via environment variables. See `src/main.py` for the exact variable names.

## How the System Works (Feature Map)

| Agent                    | Phase in the Debate Cycle          | What It Does                                                                 |
|--------------------------|------------------------------------|-------------------------------------------------------------------------------|
| **DataAnalystAgent**     | Phase 1: SCAN                      | Fetches real market data via yfinance and calculates technical indicators     |
| **CEOAgent**             | Phase 2: Triage + Phase 6: Final   | Filters weak signals; keeps max 2 per cycle; can override one risk rejection  |
| **QuantAgent**           | Phase 3: Design proposal           | Uses performance stats + half-Kelly criterion to size positions               |
| **RiskManagerAgent**     | Phase 4 + 5: Hard gate + Review    | Applies non-overridable deterministic rules first, then contextual LLM review |
| **ExecutionAgent**       | Phase 7: Execute                   | Simulates order fill with configurable slippage                               |
| **PortfolioManagerAgent**| Continuous monitoring + exits      | Tracks positions, closes trades, updates equity curve                         |
| **TradingOrchestrator**  | Coordinates the full cycle         | Enforces limits, emits events, tracks performance                             |

**Built-in safety guarantees**:
- Hard risk rules **cannot** be overridden by any LLM.
- Maximum 2 signals processed per cycle (prevents over-trading).
- Complete event log for every decision.
- Performance feedback loops into future proposals.

## Installation & Configuration

The project uses a standard Python `src/` layout with `pyproject.toml` and `requirements.txt`.

```bash
pip install -r requirements.txt
# For development / editable install
pip install -e .
```

**Required environment variable** (create a `.env` file):
- `ANTHROPIC_API_KEY` — your Anthropic Claude API key (primary model provider)

Optional: `OPENAI_API_KEY` for future fallback use.

Key files:
- `pyproject.toml` — project metadata, pytest, and coverage settings
- `src/main.py` — CLI entry point and flag definitions
- `CLAUDE.md` — complete engineering doctrine and mandatory development rules

## Documentation & Deep Reference

- **CLAUDE.md** — Full engineering doctrine (Forensic-Driven Development, Full State Verification, memory protocol, STRIDE security). Required reading before contributing.
- `.audit-log.md` — Recent automated forensic audit results.
- `memory/` directory — Progress, decisions, architecture, and glossary tracking.

## Project Health & Trust Signals

- **Maturity**: Active early-stage research prototype (pyproject version 1.0.0). No GitHub releases yet.
- **Testing**: Comprehensive pytest test suite located in `tests/`. High coverage goals with configuration in `pyproject.toml`.
- **CI/CD**: GitHub Actions workflows present (`ci.yml` + CodeQL security scanning).
- **Architecture & Quality**: Follows strict Forensic-Driven Development and Full State Verification rules defined in `CLAUDE.md`. Automated audits run regularly.
- **License**: No `LICENSE` file is present yet. All rights reserved by the author until a license is added.
- **Security**: No `SECURITY.md` yet. The project follows STRIDE threat modeling principles and keeps all secrets in environment variables only. Report issues via GitHub.
- **Compatibility**: Python ≥ 3.12. Core dependencies include yfinance, Anthropic Claude, LangChain, pandas, TA-Lib indicators, Pydantic, and Rich.
- **Status**: This is a **simulation and research tool**. It is not intended for live trading.

## Contributing

We welcome contributors who want to help build reliable, auditable AI trading systems.

### Development Setup
```bash
git clone https://github.com/JackSmack1971/degenexus.git
cd degenexus
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Before Opening a Pull Request
1. Read `CLAUDE.md` (the project’s non-negotiable engineering doctrine).
2. Run the full test suite: `pytest`.
3. Ensure coverage on changed files does not drop significantly.
4. Update `memory/PROGRESS.md` and `memory/DECISIONS.md` following the memory protocol.

### Good First Contributions
- Improve test coverage in `src/indicators.py`, `src/performance.py`, or `src/context_injector.py`.
- Add new technical indicators or risk rules.
- Improve dashboard visualizations in `src/display/`.
- Help add a proper `LICENSE` and `SECURITY.md`.

Open an issue or pick up one of the existing GitHub issues created by the automated audit process. All changes must include before/after evidence (Full State Verification).

## Roadmap & Philosophy

The project follows a strict **Forensic-Driven Development** doctrine:
- Never claim “done” without Source-of-Truth evidence.
- Prefer deletion over workarounds.
- Every change must consider at least 3 edge cases.
- Architecture must support dependency injection and testability.

Current focus areas:
- Increase test coverage on indicators, performance analytics, and portfolio close paths.
- Reduce hard-wired dependencies in the orchestrator.
- Add more robust error handling and graceful degradation.

## Acknowledgements

Built with:
- Anthropic Claude models
- LangChain
- yfinance + pandas-ta
- Rich terminal UI
- Pytest + automated agentic auditing

Special thanks to the rigorous engineering practices in `CLAUDE.md` that keep this system honest and maintainable.

---

**Degenexus** — Where specialized AIs argue like a professional trading desk before any capital is risked.
</readme>
