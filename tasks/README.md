# Wave 1 tasks

Each agent receives one task file and records its progress, evidence, and handoff in that file. Task files are the execution record; the design remains in [WAVE1_DESIGN.md](../templates/WAVE1_DESIGN.md).

## Status and dependencies

Current coordination snapshot: 2026-10-24, after `2f52b24`. Shared reads/v3 (`69438b9`), legacy wrappers/verification support (`4ff8a3c`), gateway acceptance (`b1716ae`), named CI gates (`c46b810`), actual rollout/recovery (`05bd1c0`), and E2 submission documents (`2f52b24`) are committed. I1 and E2 independently passed their scoped reviews. R1 independently passed the bounded local implementation and its documentation correction loop; remote CI execution and required-check enforcement remain unverified release gates. Inspect current files and evidence before changing anything.

| Task | Starting state | Dependencies | Output |
| --- | --- | --- | --- |
| [D1: gateway acceptance](D1-gateway-acceptance.md) | Complete; implementer and independent reviewer each passed 81 tests | I1 combined acceptance and actual rollout passed; R1 local review passed | Gateway contract, mixed routing, HTTP-write visibility, full-matrix rollback and scoped DB evidence |
| [D2: rollout configuration](D2-rollout-configuration.md) | Preparation reviewed; I1 corrected publisher and passed live rehearsal | R1 local review passed; deployment sampling remains bounded | Reviewed directory mount, stable route fixtures and atomic publication runbook |
| [E1: verification gate](E1-verification-gate.md) | Implemented and independently reviewed; local checks pass | I1 combined local runs passed; GitHub execution/enforcement remain unverified | Three named CI checks covering direct backends, modern API and ingress |
| [E2: submission documents](E2-submission-documents.md) | Reconciled with saved I1 evidence; independently reviewed | R1 local verdict incorporated; interview timing remains candidate-owned | Accurate scoping, tradeoffs, seams, rollout/recovery evidence and limitations |
| [E3: design reconciliation](E3-design-reconciliation.md) | Complete and independently reviewed | R1 integrated verdict remains separate | Design aligned with delivered code, CI and corrected I1 publication evidence |
| [I1: integration and live rehearsal](I1-integration-rehearsal.md) | Complete and independently reviewed; full matrix and live rehearsal pass | E2 reconciled; R1 local review passed | Org-7 cutover, config-only rollback, final mixed routing and recorded evidence |
| [R1: independent review](R1-independent-review.md) | Complete: local PASS after implementer/reviewer correction loop | Remote CI execution/artifact upload and required-check/PR enforcement remain unverified | Findings, correction loop and final verdict |

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
