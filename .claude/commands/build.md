---
description: Implement the next DegenExus task incrementally with tests, FSV evidence, and verification
---

Use the local `test-engineer` workflow plus `edge-case-audit` and `fsv-verify` skills. Do not reference plugin-only skill names unless a plugin dependency is documented and verified.

For each task:

1. Read acceptance criteria and identify the source of truth.
2. Load relevant code, tests, and project conventions.
3. Write a failing Prove-It or feature test when behavior changes.
4. Implement the minimum change to satisfy the test.
5. Reread the source of truth and compare the expected delta.
6. Run targeted tests, then broader tests when feasible.
7. Run `python3 -m compileall -q src/` for runtime changes.
8. Commit with a scoped conventional-style subject when the change is ready.

If verification fails repeatedly, stop and use `fdd-investigator` for read-only root-cause analysis before more edits.
