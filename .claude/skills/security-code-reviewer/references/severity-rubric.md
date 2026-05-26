# Severity Rating Rubric

> Load this file when: assigning or challenging severity ratings, or when
> the Commitment Threshold conditions in SKILL.md require structured scoring.

## Rating Scale

| Severity      | Exploit Path                         | Attacker Reach                             | Blast Radius                         | Action                        |
| ------------- | ------------------------------------ | ------------------------------------------ | ------------------------------------ | ----------------------------- |
| CRITICAL      | End-to-end traced                    | Unauthenticated or low-auth                | PII/key/admin/RCE/data loss at scale | Immediate — block merge       |
| HIGH          | End-to-end traced                    | Authenticated or requires one prerequisite | Significant data or privilege impact | Fix before release            |
| MEDIUM        | Partial path — one unknown           | Any                                        | Bounded or requires chaining         | Fix in next sprint            |
| LOW           | Theoretical — multiple unknowns      | Constrained                                | Minimal                              | Track and schedule            |
| INFORMATIONAL | No exploitable path identified       | N/A                                        | N/A                                  | Log for hardening backlog     |
| UNKNOWN       | Path incomplete — blocker documented | Unresolved                                 | Unresolved                           | Resolve blocker before rating |

## Chainability Upgrade Rule

If finding A (severity X) enables finding B (severity Y), the chained
severity = max(X, Y) + 1 level. Two mediums chained = high. Medium + high
chained = critical.

## Blast Radius Tiers

1. Single record / single user session — LOW floor
2. User population segment or business logic bypass — MEDIUM floor
3. Credential/key exposure, admin escalation, PII at scale — HIGH floor
4. Full system compromise, supply chain impact, irreversible data loss — CRITICAL floor

## Downgrade Conditions (all must apply)

Severity may be downgraded one level only if ALL of the following are true:

- An independent, deterministic control on the same attack path has been verified
- That control survives the deployment configuration in use
- The control cannot be bypassed from the same attacker position
- The downgrade is explicitly documented with the name of the compensating control

Compensating controls do not stack — downgrade is capped at one level regardless
of the number of compensating controls claimed.
