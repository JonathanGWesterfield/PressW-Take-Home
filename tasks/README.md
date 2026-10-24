# Wave 1 tasks

Each agent receives one task file and records its progress, evidence, and handoff in that file. Task files are the execution record; the design remains in [WAVE1_DESIGN.md](../templates/WAVE1_DESIGN.md).

## Status and dependencies

Current coordination snapshot: 2026-10-24, through local `024a52e` and R1 commit `9ec6192`. Shared reads/v3, compatibility wrappers, gateway acceptance, rollout/recovery, CI workflow and submission documents are committed. I1/E2/E3 passed their scoped reviews; R1 independently passed the bounded local implementation. [GitHub run 40125062976](https://github.com/JonathanGWesterfield/PressW-Take-Home/actions/runs/40125062976) passed three automatic jobs/uploads at `31758ea`. Later documentation/IDE commits are not represented by that run. GitHub reported `main` unprotected and the repository public; required-check/PR enforcement, private sharing, timing disclosure and final-revision publication/verification remain. Inspect current files and evidence before changing anything.

| Task | Starting state | Dependencies | Output |
| --- | --- | --- | --- |
| [D1: gateway acceptance](D1-gateway-acceptance.md) | Complete; implementer and independent reviewer each passed 81 tests | I1 combined acceptance and actual rollout passed; R1 local review passed | Gateway contract, mixed routing, HTTP-write visibility, full-matrix rollback and scoped DB evidence |
| [D2: rollout configuration](D2-rollout-configuration.md) | Preparation reviewed; I1 corrected publisher and passed live rehearsal | R1 local review passed; deployment sampling remains bounded | Reviewed directory mount, stable route fixtures and atomic publication runbook |
| [E1: verification gate](E1-verification-gate.md) | Implemented/reviewed; local matrix and three remote jobs/uploads pass | Required-check/PR enforcement disabled; verify final published revision | Three named CI checks covering direct backends, modern API and ingress |
| [E2: submission documents](E2-submission-documents.md) | Reconciled with saved I1 evidence; independently reviewed | R1 local verdict incorporated; interview timing remains candidate-owned | Accurate scoping, tradeoffs, seams, rollout/recovery evidence and limitations |
| [E3: design reconciliation](E3-design-reconciliation.md) | Complete and independently reviewed | R1 local PASS incorporated; subsequent CI evidence reconciled | Design aligned with delivered code, CI and corrected I1 publication evidence |
| [I1: integration and live rehearsal](I1-integration-rehearsal.md) | Complete and independently reviewed; full matrix and live rehearsal pass | E2 reconciled; R1 local review passed | Org-7 cutover, config-only rollback, final mixed routing and recorded evidence |
| [R1: independent review](R1-independent-review.md) | Complete: local PASS after implementer/reviewer correction loop | Remote CI/upload now observed at `31758ea`; required-check/PR enforcement disabled | Findings, correction loop and final verdict |

D1, D2 and E1 ran as separate workstreams; I1 completed the combined runs and shared-stack rehearsal. E2 reconciled the submission documents with I1 evidence. R1 reviewed the integrated result through an implementer/reviewer correction loop; its local PASS and outstanding remote release gates are incorporated in E2. I1 retains ownership of any further shared-stack operations.

## Coordination rules

- One agent owns each implementation task's files and its task record. Set the owner/status before starting and use the output sections in that file.
- The integrator owns shared runner files: `scripts/verify`, `tests/run_stack.py`, `tests/compose.yml`, `tests/conftest.py`. Other agents propose changes in their task handoff.
- Preserve existing uncommitted work and frozen golden responses. Coordinate before editing another task's files; do not overwrite them.
- Use targeted checks during implementation. Coordinate full Docker matrices and shared-stack operations through I1; use isolated projects for any independent live checks.
- Implement two crew reads only. Keep Callboard's writes and maintenance ownership. No extra endpoints, schema migration, cache or replacement worker are needed.
- Commit, push and remote settings changes remain under the user's control; task assignment alone does not request them.
- Update this index only for milestone/status changes. Keep detailed findings and output in the owning task file.

Historical direct results inspected for the original breakdown: legacy `showcall-verify-17ee51dac5bb` and Encore `showcall-verify-eb297d7faca5`, exit 0; gateway `showcall-verify-e6b550ce4c0c`, exit 0. They are saved evidence, not fresh validation of subsequent changes. JUnit counters include unittest subtests.
