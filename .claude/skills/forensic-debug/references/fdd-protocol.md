# FDD Investigation Protocol

1. Capture symptom, invariant violated, timeframe, affected source-of-truth state, and reproduction evidence.
2. Generate at least three plausible hypotheses before testing any one hypothesis.
3. Assign a prior probability and a falsification test to each hypothesis.
4. Use independent source-of-truth reads where possible; logs alone are insufficient proof.
5. Eliminate hypotheses explicitly. If all are eliminated, expand the hypothesis set.
6. Run a 5-Whys chain only after one hypothesis survives falsification.
7. State root cause, contributing factors, non-causes, and permanent fix requirements.
8. Use `fsv-verify` to define PRE/ACT/POST/DIFF evidence for validating the fix.
