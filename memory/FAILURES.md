# FAILURES

## 2026-05-27 — Audit orchestration blocked by missing GitHub mutation tooling
- **Failure mode:** Required forensic mutations (issue create/update) could not be executed from this environment.
- **Physical evidence:** `gh` is not installed (`gh: command not found`), and `git remote -v` shows no configured remote, so repository default-branch metadata and authenticated mutation path are unavailable.
- **Root cause:** Environment/tooling gap, not repository code behavior.
- **Blast radius:** Audit can collect read-only evidence but cannot complete mandatory “create/update forensic issue” handoff when a new anomaly requires issue mutation.
- **Containment:** Record all anomalies with duplicate mapping to existing open issues where possible; mark session `completion_verdict=blocked` if any anomaly cannot be mutated per doctrine.
