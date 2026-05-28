# Prove-It and FSV-AAA Test Rules

- For bugs, write a regression test that fails before the fix and passes after it.
- Structure behavioral tests as PRE source-of-truth read, one ACT, POST reread, and DIFF assertion.
- Mock LLM providers, network/yfinance calls, time, random behavior, and filesystem side effects.
- Use deterministic fixtures from `tests/conftest.py` where possible.
- Use `pytest-mock`'s `mocker` fixture instead of importing `unittest.mock` directly.
- Include at least three edge cases: empty/zero, min/max boundary, malformed/adversarial input, concurrency/ordering, stale state, or network degradation as applicable.
- Prefer targeted pytest first, then broader regression tests and `python -m compileall -q src/` for runtime changes.
