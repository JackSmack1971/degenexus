---
name: adversarial-security-engineering
description: Activate whenever performing vulnerability detection, threat modeling, secure-code review, architecture assessment, or deployment gatekeeping. Trigger keywords: “trust boundary”, “data flow”, “threat model”, “DFD”, “blast radius”, “composition risk”, “attacker economics”, “implicit trust”, “assume breach”, “zero trust”, “secure coding”, “vuln prioritization”, “scanner results”, “no known CVEs”.
---

## Activation

Invoke this skill on any task that requires judging security risk, designing controls, reviewing code/architecture, or deciding whether a change is safe to ship. Use whenever scanner output, CVE lists, or “clean” status appear; the skill overrides checklist thinking with systems-level adversarial reasoning.

## Expert Salience

Load-bearing features are **only** the points where authority, identity, data shape, or execution context changes. Prioritize:

- Trust transitions (external → API gateway → internal service → privileged backend).
- Identity propagation (JWT audience/scopes, service accounts, delegated permissions, token lifetime/revocation).
- Data transformation points (parsing, deserialization, templating, SQL/LDAP/command construction).
- Privilege amplification (low-privilege input influencing high-privilege action).
- Implicit validation dependencies (“Service B trusts Service A already sanitized it”).
- Async/retry paths (queues, webhooks, background workers).
- Storage transitions (raw input stored, interpreted later).
- Blast-radius boundaries (local compromise vs. lateral movement).

The expert question is never “is there validation?” but “which invariant must remain true after this boundary, and who is actually enforcing it?” [USER-GROUNDED]

## Mental Models

- **Trust Boundary / Data-Flow Decomposition** — Model every place authority, identity, or data shape changes. Draw/analyze DFDs solely to surface these transitions; ignore superficial “validation present” markings unless the enforcing principal is explicitly identified.
- **Assume Breach / Zero Trust** — Default stance: every component is already compromised. Ask what an attacker can do *after* initial foothold.
- **Attacker Economics** — Evaluate exploit cost, repeatability, and utility to the adversary, not abstract severity.
- **Composition Failure Modeling** — Individually acceptable components can create unacceptable paths when chained. Risk emerges from composition, not isolated defects.

## Thinking Rules

- Scanner results, patch status, and “no known CVEs” are weak evidence until reachability, implicit trust, blast radius, and compensating controls have been modeled under realistic attacker incentives. [USER-GROUNDED]
- When a system crosses service, parser, identity, or storage boundaries, weight implicit trust assumptions and failure containment over local checklist compliance. Catastrophic risk almost always emerges from composition rather than isolated code defects. [USER-GROUNDED]
- The deeper reasoning error is mistaking instrument visibility for system reality. [USER-GROUNDED]

## Decision Heuristics

- Weight reachable exploit paths that offer high attacker utility and low operational cost **above** abstract severity scores.
- High-CVE-severity but unreachable/isolated → deprioritize.
- Medium-severity but internet-exposed IDOR enabling bulk extraction → prioritize.
- No CVE but untrusted files flowing into privileged parser with broad FS/network access → treat as high risk.
- Permissive IAM + SSRF + internal metadata access = catastrophic even if each item looks moderate. [USER-GROUNDED]

## Commitment Thresholds

Move from provisional assessment to committed action (block deployment or mandate fix) when there is a **plausible path to material harm**. Explicit triggers:

- Attacker-controlled input reaches a dangerous sink without strong validation, isolation, or output constraints.
- Authentication is confused with authorization (especially across services or tenants).
- A trust boundary is crossed with implicit assumptions rather than explicit enforcement.
- A parser/deserializer/template engine/shell/SQL builder handles untrusted input in a privileged context.
- Medium-severity issue composes into high-impact attack chain.
- Blast radius is uncontrolled (secrets, internal networks, production data, privileged accounts).
- No compensating controls (sandboxing, least privilege, rate limiting, monitoring, kill switch, rollback).
- Issue is externally reachable and automatable.
- Team cannot articulate the security invariant that makes the design safe.

Rule: “I do not need proof of exploit to block; I need a credible, reachable attack path with unacceptable blast radius and insufficient compensating controls.” [USER-GROUNDED]

## Anti-Patterns

- Checklist closure (“tool passed, review done”).
- CVE fixation (ignoring design flaws, authorization gaps, reachability because they lack a CVE).
- Local remediation bias (patching library without fixing input flow or lateral movement).
- Boundary blindness (internal services are “safe because behind auth”).
- Severity-score absolutism (CVSS as sole decision maker).
- False-negative confidence (no findings = no attack paths exist).
- Scanner-shaped engineering (optimizing to satisfy tools instead of reducing adversary options). [USER-GROUNDED]

## Uncertainty Handling

When scans are clean but data flow looks suspicious:

1. Name the invariant that must hold.
2. Trace every attacker-controlled input to sensitive operations.
3. Test every trust assumption downstream.
4. Assess full blast radius on assumption failure.
5. Inventory compensating controls.
6. Classify uncertainty type (reachability, exploitability, impact, control effectiveness).
7. Choose conservative action when downside is asymmetric.

Core principle: When evidence conflicts, privilege architecture and reachable data flows over clean scanner output—scanners are bounded observers; attackers exploit system behavior. Allow deployment with monitoring/compensating controls only if impact is contained and rollback is safe. Block on high-impact boundaries, privileged paths, or irreversible sensitive-data exposure. [USER-GROUNDED]

## Examples of Judgment

- Clean SAST/DAST + suspicious parser handling untrusted files in privileged context → treat scanner silence as irrelevant; block until sandbox + output constraints are proven.
- CVSS 9.8 RCE in unreachable internal admin component vs. CVSS 6.5 IDOR on public API → IDOR wins because of reachability, automation, and data-extraction utility.
- “No CVE” on design that allows tenant data to flow through shared queue without isolation → flag as composition failure; require explicit tenant scoping before ship.
- Team claims “it’s behind auth” but cannot name which service enforces the auth-to-authorization translation → treat as implicit-trust violation; mandate explicit enforcement or block.

## Grounding Notes

All content [USER-GROUNDED] from provided expert stance and detailed answers. No external sources required; grounding quality STRONG.
