# R1: independently review the integrated Wave 1 result

- **Owner:** unassigned
- **Status:** Final combined review pending
- **Dependencies:** I1 combined implementation/evidence; coordinate E2 final documents
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

Own this review/task file. Do not edit implementation or frozen corpus files; send actionable findings to their owners. Record each finding here, with file/line references and an observable recheck. Task owners record corrections in their own task files.

## Task

1. Compare the integrated result against the assessment README, Wave 1 design and task acceptance criteria. Keep scope at two reads, shared retrieval, org-7 migration and rollback.
2. Review tenant scoping, bound raw-ID conversion, error handling/session cleanup, raw legacy transport/serialization and intentional modern differences.
3. Check direct frozen compatibility and independent gateway ingress evidence; ensure routing/fallback cannot produce a false parity pass.
4. Assess the actual mixed configuration, legacy HTTP-write visibility, containing-directory mount/atomic publication, and no-restart rollback. Confirm maintenance/write ownership never moved.
5. Independently run bounded relevant checks, coordinating live tests with I1. Inspect final full-run artifacts, cleanup and documentation; distinguish source-reviewed CI from remotely executed CI.
6. Send concrete findings to D1/D2/E1/E2 or I1, then re-review corrections. Do not demand later-wave production features to approve this interview-sized slice.
7. Issue a verdict listing resolved findings, any remaining blockers, accepted limitations and evidence. E2 incorporates that final state.

## Acceptance checklist

- [ ] Every declared Wave 1 acceptance requirement has evidence or an explicit blocker.
- [ ] No frozen expectations were weakened to accommodate the replacement.
- [ ] Final integrated checks and actual cutover/rollback evidence are assessed.
- [ ] Feedback is routed to owners and corrections are rechecked.
- [ ] Final verdict and limits are written below and handed to I1/E2.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Not started in this task record.

### Changes made

- Pending.

### Validation and evidence

- Pending.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| Pending | | |

### Handoff

- Changed files: pending.
- Integration requests / dependencies: pending.
- Remaining risks or blockers: pending.
- Final status and reviewer reference: pending.
