# Degenexus

**A multi-agent AI trading company simulator.** Specialized AI agents (CEO, Analyst, Quant, Risk Manager, Execution, Portfolio Manager) collaborate through a structured 8-phase debate cycle to scan markets, size positions with risk controls, and manage a simulated portfolio.

```bash
# See it work in one command (after setup)
python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY
```

## What You Get in the First 2 Minutes

Run one trading cycle and watch the full debate happen in your terminal:

- **Data Analyst** scans symbols and produces market signals with confidence scores
- **CEO** triages and keeps only the strongest signals (max 2 per cycle)
- **Quant** designs a trade proposal using performance stats and half-Kelly sizing
- **Risk Manager** applies hard deterministic rules first, then contextual LLM review
- **CEO** can challenge a risk rejection once (hard rules are final)
- **Execution** simulates the fill with slippage
- **Portfolio Manager** monitors and closes positions
- You see a clean cycle summary: trades opened, PnL, portfolio value, and event count

The system is deliberately conservative and auditable. Every decision leaves a traceable event log.

## Quickstart (Works on macOS, Linux, Windows)

### Prerequisites
- Python 3.12 or newer
- An Anthropic API key (create free at https://console.anthropic.com — the system primarily uses Claude models)
- Git

### Step-by-Step

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

# 4. Create your environment file
cp .env.example .env 2>/dev/null || echo "ANTHROPIC_API_KEY=your_key_here" > .env
# Edit .env and add your real key:
# ANTHROPIC_API_KEY=sk-ant-...

# 5. Run your first trading cycle (headless / log mode)
python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY,QQQ
```

**Expected observable success state:**
You will see colored terminal output showing the debate phases, agent decisions, risk checks, any simulated trades, and a final cycle summary with portfolio value and PnL. No errors = success.

Want the live dashboard instead? Remove `--no-dashboard`.

## Common Usage Examples

### List all available agents and their roles
```bash
python src/main.py --list-agents
```

### Run 5 cycles with a 30-second delay between them
```bash
python src/main.py --cycles 5 --delay 30 --symbols NVDA,TSLA
```

### Run continuously until you stop it (great for watching behavior)
```bash
python src/main.py --cycles 0 --delay 60
```

### Start with more starting capital
```bash
python src/main.py --capital 50000 --cycles 3
```

All flags also work via environment variables (see `src/main.py` for the exact names).

## How the System Works (Feature Map)

| Component              | Role in the Debate Cycle                          | Key Behavior |
|------------------------|---------------------------------------------------|--------------|
| **DataAnalystAgent**   | Phase 1: SCAN                                     | Fetches price data via yfinance + computes technical indicators (ta library) |
| **CEOAgent**           | Phase 2: Triage + Phase 6: Final approval         | Filters weak signals; can override one contextual risk rejection |
| **QuantAgent**         | Phase 3: Design proposal                          | Uses recent performance + half-Kelly criterion for position sizing |
| **RiskManagerAgent**   | Phase 4: Hard gate + Phase 5: Contextual review   | Deterministic rules first (final), then LLM risk scoring |
| **ExecutionAgent**     | Phase 7: Execute                                  | Simulates market fill with configurable slippage |
| **PortfolioManagerAgent** | Continuous monitoring + exits                  | Tracks positions, closes trades, updates equity curve |
| **TradingOrchestrator**| Coordinates the full 8-phase cycle                | Enforces limits (max 2 signals/cycle), emits events, tracks performance |

**Core guarantees built into the architecture:**
- Hard risk rules cannot be overridden by the LLM
- Only 2 signals processed per cycle (prevents over-trading)
- Full event log for every decision (great for auditing)
- Performance stats feed back into future proposals

## Installation & Configuration

The project uses a standard Python layout with `pyproject.toml` + `requirements.txt`.

```bash
pip install -r requirements.txt
# or for development
pip install -e .
```

**Required environment variables** (put in `.env`):
- `ANTHROPIC_API_KEY` — primary LLM provider
- Optional: `OPENAI_API_KEY` (fallback / future use)

**Key configuration files**
- `pyproject.toml` — project metadata and test settings
- `src/main.py` — CLI flags and defaults
- `CLAUDE.md` — full engineering doctrine the project follows

## Project Health & Trust Signals

- **Status**: Active early-stage research prototype (pyproject version 1.0.0, no GitHub releases yet)
- **Tests**: 266+ tests passing, ~90% coverage (improving with every automated audit)
- **CI/CD**: GitHub Actions workflows present (`ci.yml` + CodeQL security scanning)
- **Architecture & Quality**: Automated forensic audits run regularly (see `.audit-log.md`). Follows strict "Forensic-Driven Development" and "Full State Verification" rules defined in `CLAUDE.md`
- **License**: No `LICENSE` file present yet. All rights reserved by the author until a license is added.
- **Security**: No `SECURITY.md` yet. The codebase follows STRIDE threat modeling principles during audits and keeps secrets in environment variables only.
- **Compatibility**: Python ≥ 3.12. Depends on yfinance (stocks), Anthropic Claude models, LangChain, pandas, TA-Lib indicators, and Pydantic.

**Important**: This is a **simulation tool** for research and learning. It does **not** execute real trades. Never use it with real capital without thorough additional validation, paper-trading, and your own risk controls.

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
1. Read `CLAUDE.md` (the project’s engineering doctrine)
2. Run the full test suite: `pytest`
3. Make sure coverage on changed files does not drop significantly
4. Update `memory/PROGRESS.md` and `memory/DECISIONS.md` if you follow the memory protocol

### Good First Contributions
- Improve test coverage in `src/indicators.py`, `src/performance.py`, or `src/context_injector.py`
- Add new technical indicators or risk rules
- Improve dashboard visualizations (`src/display/`)
- Help add a proper `LICENSE` and `SECURITY.md`

Open an issue or pick up one of the existing GitHub issues created by the automated audit process. All changes should include before/after evidence (Full State Verification).

## Roadmap & Philosophy

The project follows a strict **Forensic-Driven Development** doctrine:
- Never claim “done” without Source-of-Truth evidence
- Prefer deletion over workarounds
- Every change must consider ≥3 edge cases
- Architecture must support dependency injection and testability

Current focus areas (from recent audits):
- Increase test coverage on indicators, performance analytics, and portfolio close paths
- Reduce hard-wired dependencies in the orchestrator
- Add more robust error handling and graceful degradation

## Acknowledgements

Built with heavy use of:
- Anthropic Claude models
- LangChain
- yfinance + pandas-ta for market data
- Rich for terminal UI
- Pytest + automated agentic auditing

Special thanks to the rigorous engineering practices documented in `CLAUDE.md` that keep this system honest and maintainable.

---

**Degenexus** — Where multiple specialized AIs argue like a trading desk before any capital is risked (even in simulation).

*Not financial advice. For research and educational purposes only.*
