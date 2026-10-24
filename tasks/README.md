# Wave 1 tasks

Each agent receives one task file and records its progress, evidence, and handoff in that file. Task files are the execution record; the design remains in [WAVE1_DESIGN.md](../templates/WAVE1_DESIGN.md).

## Status and dependencies

Initial snapshot: 2026-10-24, HEAD `b557934`, with implementation actively changing in the working tree. A (reference preservation) and B (shared reads/v3, commit `69438b9`) are complete. C (legacy wrappers) has passed direct parity/review but is uncommitted. D/E are in progress. Inspect current files and evidence before changing anything; task checkboxes below are not assertions that existing work is absent.

| Task | Starting state | Dependencies | Output |
| --- | --- | --- | --- |
| [D1: gateway acceptance](D1-gateway-acceptance.md) | Complete; implementer and independent reviewer each passed 81 tests | I1 combined acceptance and actual rollout remain | Gateway contract, mixed routing, HTTP-write visibility, full-matrix rollback and scoped DB evidence |
| [D2: rollout configuration](D2-rollout-configuration.md) | Prepared and independently reviewed; bounded checks pass | I1 live mount, cutover and rollback rehearsal pending | Reviewed directory mount, stable route fixtures and atomic publication runbook |
| [E1: verification gate](E1-verification-gate.md) | Implemented and independently reviewed; local checks pass | I1 combined runs and GitHub execution remain unverified | Three named CI checks covering direct backends, modern API and ingress |
| [E2: submission documents](E2-submission-documents.md) | Reconciled with saved I1 evidence; independently reviewed | R1 verdict and interview timing remain distinct | Accurate scoping, tradeoffs, seams, rollout/recovery evidence and limitations |
| [E3: design reconciliation](E3-design-reconciliation.md) | Complete and independently reviewed | R1 integrated verdict remains separate | Design aligned with delivered code, CI and corrected I1 publication evidence |
| [I1: integration and live rehearsal](I1-integration-rehearsal.md) | Complete and independently reviewed; full matrix and live rehearsal pass | R1 whole-system review and E2 final documents remain | Org-7 cutover, config-only rollback, final mixed routing and recorded evidence |
| [R1: independent review](R1-independent-review.md) | Final combined review pending | I1; review E2 draft alongside final evidence | Findings, correction loop and final verdict |

D1, D2 and E1 can run concurrently with one coordinator. Start E2 as a slot becomes available and interfaces stabilize. I1 owns the combined run and changes to the shared running stack. R1 reviews the integrated result and sends findings back to each owner; E2 is finalized with that verdict.

## Coordination rules

- One agent owns each implementation task's files and its task record. Set the owner/status before starting and use the output sections in that file.
- The integrator owns shared runner files: `scripts/verify`, `tests/run_stack.py`, `tests/compose.yml`, `tests/conftest.py`. Other agents propose changes in their task handoff.
- Preserve existing uncommitted work and frozen golden responses. Coordinate before editing another task's files; do not overwrite them.
- Use targeted checks during implementation. Coordinate full Docker matrices and shared-stack operations through I1; use isolated projects for any independent live checks.
- Implement two crew reads only. Keep Callboard's writes and maintenance ownership. No extra endpoints, schema migration, cache or replacement worker are needed.
- Commit, push and remote settings changes remain under the user's control; task assignment alone does not request them.
- Update this index only for milestone/status changes. Keep detailed findings and output in the owning task file.

Historical direct results inspected for the original breakdown: legacy `showcall-verify-17ee51dac5bb` and Encore `showcall-verify-eb297d7faca5`, exit 0; gateway `showcall-verify-e6b550ce4c0c`, exit 0. They are saved evidence, not fresh validation of subsequent changes. JUnit counters include unittest subtests.
