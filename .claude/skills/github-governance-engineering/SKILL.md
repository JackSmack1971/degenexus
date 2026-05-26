---
name: github-governance-engineering
description: Activates when engineering a GitHub org or enterprise as programmable distributed governance surface (rulesets, custom properties, .github/ orchestration, OIDC, CODEOWNERS, reusable workflows). Triggers on platform engineering decisions involving blast-radius isolation, continuous convergence, least-privilege enforcement, or drift reconciliation. Replaces ad-hoc per-repo configs, manual checklists, or point-in-time gates with declarative platform-native controls and reconciliation loops.
---

### Activation

Invoke this skill when any of the following load-bearing conditions appear in a conversation, ticket, or IaC change:

- Discussion of org-wide policy, rulesets, custom properties, or .github/ centralization
- Questions about scaling governance beyond single-repo workflows or CODEOWNERS
- Requests to evaluate “green CI + documented process” versus true continuous convergence
- Proposals involving PATs, static secrets, manual PR templates, or local workflow overrides
- Planning OIDC federation, SBOM signing, or reconciliation workflows

### Expert Salience

The principal platform engineer ignores superficial green checkboxes and focuses exclusively on five non-obvious, platform-native signals that reveal whether GitHub is operating as a living governance surface or a collection of disconnected developer tools:

1. **Ruleset coverage %** (GitHub API `/orgs/{org}/rulesets` filtered by custom properties or repo patterns): ≥95% of repos under active org rulesets. [USER-GROUNDED]
2. **Drift rate** (IaC vs runtime via Terraform plan or GitHub API diff on branch protection, workflow permissions, custom properties): zero high-severity divergences over 30 days. [USER-GROUNDED]
3. **Audit-log bypass events** (`ruleset_bypass`, `permission_change`, `workflow_run` with `write-all` or elevated tokens): <0.5% incidence, with automated SIEM alerting. [USER-GROUNDED]
4. **Custom property completeness** (e.g., `data_sensitivity`, `tier`, `compliance_level` populated on every repo). [USER-GROUNDED]
5. **OIDC claim anomalies** (unexpected `repo_property_*` values in token issuance logs). [USER-GROUNDED]

Green CI + docs = provisional if any signal fails. True convergence = all signals clean + reconciliation workflow confirms no UI/API desync. [GROUNDED]

### Mental Models

**Core mental model: .github/ as centralized governance kernel vs ad-hoc per-repo configuration**  
Treat `.github/` (or dedicated platform-workflows repo) as the programmable distributed control plane—single source of truth (SSOT) for reusable workflows (`workflow_call`), composite actions, issue forms, and CODEOWNERS. [USER-GROUNDED]
