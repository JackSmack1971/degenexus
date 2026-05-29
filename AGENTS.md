# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/`. Use `src/agents/` for trading-desk roles, `src/core/` for execution and risk primitives, `src/data/` for feeds and indicators, `src/memory/` for persistence and analytics, `src/models/` for Pydantic models, and `src/display/` for terminal UI. The CLI entry point is `src/main.py`; debate orchestration sits in `src/orchestrator.py`. Tests mirror runtime modules in `tests/` with `test_*.py` names. Repo process docs live in `CLAUDE.md`, `.audit-log.md`, `memory/`, and `.github/`.

## Build, Test, and Development Commands
Create an environment with `python -m venv .venv` and install deps using `pip install -r requirements.txt`.

- `python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY` runs one headless simulation cycle.
- `python src/main.py --list-agents` lists registered agents and roles.
- `python -m pytest tests/ -v` runs the full test suite.
- `python -m pytest tests/ --cov=src --cov-report=term-missing` checks coverage.
- `python -m compileall -q src/` validates imports and syntax.
- `pip-audit -r requirements.txt` checks Python dependencies for known vulnerabilities.

## Coding Style & Naming Conventions
Target Python >=3.11 per `pyproject.toml` (CI runs 3.12), 4-space indentation, explicit type hints, and small focused functions. Follow existing naming: `snake_case` for modules/functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Preserve the current `src/` package layout instead of adding one-off top-level scripts. Use `pytest-mock`’s `mocker` fixture for test doubles rather than importing `unittest.mock` directly.

## Testing Guidelines
Pytest is configured in `pyproject.toml` with `testpaths = ["tests"]` and `python_functions = ["test_*"]`. Add or update tests with every behavioral change, especially around risk gates, portfolio state, and prompt sanitization. CI enforces coverage with `pytest --cov=src --cov-fail-under=90`, matching the 90%+ target in `CLAUDE.md`. Prefer deterministic fixtures in `tests/conftest.py`.

## Commit & Pull Request Guidelines
Recent history follows conventional-style subjects such as `docs(audit): ...` and `fix(risk): ...`. Keep commits scoped and imperative. Pull requests must link an issue, summarize the change, include FSV evidence, list at least three edge cases, paste test output, and note any `memory/` updates. Use `.github/PULL_REQUEST_TEMPLATE/default.md` or `bug-fix.md` as appropriate.

## Security & Agent Workflow
Never commit secrets; use `.env` for `ANTHROPIC_API_KEY` and related credentials. Run the pre-work GitHub scans from local agent instructions before starting, and claim the issue before editing. If you notice a doctrine/security breach or another triggered anomaly you are not fixing in this turn, open or update an issue before stopping.
