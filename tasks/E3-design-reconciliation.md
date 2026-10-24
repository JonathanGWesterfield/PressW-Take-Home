# E3: reconcile the design with verified Wave 1 delivery

- **Owner:** `/root/e1_implementer` (independent review: `/root/e1_reviewer`)
- **Status:** Complete; independently approved for dedicated commit
- **Dependencies:** Committed I1/E2 evidence; R1 integrated review remains separately owned

## Context and ownership

E2 explicitly handed the design owner reconciliation of `templates/WAVE1_DESIGN.md`: its implementation status and host-side publication guidance lag the verified delivery and corrected Linux-view procedure. Read the assessment README, complete Wave 1 design, tasks/E2-submission-documents.md, tasks/I1-integration-rehearsal.md, tasks/D2-rollout-configuration.md, compact I1 evidence and current source before editing.

Own only `templates/WAVE1_DESIGN.md` and this task file. Preserve the design structure, architecture and selected two-read boundary. Do not change code, tests, routing, shared stack, other task records or final submission templates. R1 is actively owned elsewhere; do not claim its verdict or duplicate it.

## Task and acceptance

- [x] Reconcile proposed/current/completed wording with committed code and verified I1 facts; retain unfinished requirements as explicit limits.
- [x] Replace unsafe host-side publication guidance with the tested Linux-view publisher procedure, linking the concrete D2 runbook and disclosing the failed attempt and bounded corrected evidence.
- [x] Align runner, gateway boundaries, actual mixed routing, CI configuration and remote-enforcement limitations with current repository evidence.
- [x] Preserve the design intent and future-wave boundaries; do not invent evidence, assessment timing or R1 approval.
- [x] Independent reviewer reads the full system plan, returns findings, and rechecks corrections; relative links and scoped whitespace pass.

## Agent output

### Changes and rationale

- Reconciled design status, registered adapters/shared retrieval, implemented modern contract, completed direct/ingress/live acceptance and final mixed org-7 configuration with the committed implementation/I1 evidence. Preserved all eight numbered sections and architecture/two-read boundary.
- Removed stale SQL-only write-proof and pending-cutover claims; clarified that the conditional Host forwarding adjustment was investigated and not implemented.
- Aligned automatic check names, retained modern suites and separate gateway oracle with actual runner/workflow. Remote execution/enforcement and separately owned R1 remain explicitly unverified.
- Replaced generic/host publication advice with D2's tested Linux-view publisher, concrete cutover/rollback commands and deployment prerequisites. Disclosed all 28 first-attempt HTTP failures, zero attempted writes, corrected 6,319 temporary reads/58 live samples and finite-evidence limits without copying full task logs.

### Validation and evidence

- Read assessment/full plan, E2 handoff, completed I1/D2 records, compact evidence, current gateway/modern/repository/service/main/runner/workflow/config sources and recent Git history. No runtime, database, code, test or route operation performed.
- Fresh `.venv/bin/python` read-only assertions passed: preserved section numbering against HEAD; all relative Markdown targets exist; compact I1 selected source hashes match current bytes; exact 28/0 failed-attempt counts and 6,319/58 corrected sample counts match evidence; saved pytest results are 1,084/1,084/81; all three actual CI names appear; effective routes equal mixed fixture; referenced implementation commits resolve.
- `git diff --check -- templates/WAVE1_DESIGN.md tasks/E3-design-reconciliation.md` passed. These are document/source fact checks, not fresh matrix/live validation; runtime results remain attributed to saved I1 evidence.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| `/root/e1_reviewer` initial context: stale SQL-only update proof and ambiguous conditional Host fix. | Design now records implemented HTTP writer proof; Host adjustment is explicitly investigated/unimplemented. | Full revised plan approved against actual source/evidence. |
| `/root/e1_reviewer` full-plan review. | No additional actionable findings. | Independently checked eight sections, relative links, selected source/corpus hashes, effective mixed routes, CI names, commit refs and scoped whitespace. E3 approved; integrated R1 remains separate. |

### Handoff

Changed only `templates/WAVE1_DESIGN.md` and this task. `/root/e1_reviewer` approved the complete revised plan with no unresolved E3 findings; ready for parent packaging as a dedicated commit. R1 remains independently owned; no approval claim, push or runtime change.
