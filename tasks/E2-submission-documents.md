# E2: reconcile submission documents

- **Owner:** `/root/e2_implementer` (review: `/root/e2_reviewer`)
- **Status:** Complete for E2; submission documents reconciled with saved I1 evidence and independently approved; integrated R1 remains separate
- **Dependencies:** Begin after D1/D2 interfaces stabilize; finalize using I1 evidence and R1 verdict
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

Own `templates/SCOPING.md`, `templates/TRADEOFFS.md`, `templates/SEAMS.md`, and this task file. Coordinate edits to root `SEAMS.md` and `api-endpoints.md` with their current owner/integrator before editing them.

## Task

1. Read the current source, design, maintenance findings, test results and Git history. Replace stale intermediate-state claims with current verified facts.
2. Describe the two legacy crew reads, shared retrieval, intentional v3 differences, org-7 cutover and config-only rollback. Keep the interview submission concise.
3. Record scope cuts and risks: no new writes/jobs/schema/cache, bounded parity evidence, shared database dependency, and unresolved later-wave maintenance/transaction questions.
4. Cite actual final report identities and results from I1/R1. Reconcile pytest method counts with JUnit subtest counters rather than copying contradictory totals.
5. State remaining gaps honestly. Do not claim cutover, review, remote CI execution or branch protection happened until corresponding evidence exists.
6. Use candidate-provided delivery/window information for interview timing. Do not invent a timer start or classify post-window work from stack startup alone.

## Acceptance checklist

- [x] Submission documents match the current implementation and saved demonstrated rollout; integrated R1 review remains explicitly pending.
- [x] Stale missing-wrapper and obsolete test-failure claims are resolved.
- [x] Available evidence references, counts and limitations are internally consistent; I1 evidence is incorporated and integrated R1 is explicitly pending.
- [x] Scope and tradeoffs remain interview-sized and understandable.
- [x] Any unresolved timing question is explicitly recorded rather than guessed.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Claimed E2 after verifying the other chat owns active I1 live integration/rehearsal. E2 owns the three submission templates and this task record only; no application, runner, root evidence or running-stack edits. Final claims must follow actual I1 evidence, including any failed/recovery attempts.

### Changes made

- Reconciled the three submission templates against the complete Wave 1 design, current adapter/service/repository code, gateway acceptance, CI workflow, Git history, root seam map and maintenance findings. Preserved their established template sections and bounded interview scope.
- Removed obsolete missing-wrapper, all-legacy-test-fixture, old HEAD and unresolved collection/header-construction-failure claims. Distinguished implemented/read-only scope, unchanged frozen reference, deliberate v3 differences, isolated proof, pending actual rollout and R1 review.
- Added the second busy maintenance observation and quiet follow-up to the seam summary, separating API preparation/replay from cleanup effects. Callboard retains all writes and maintenance.
- Retained candidate-owned timing disclosure: kit delivery/start is unknown; no invented four-hour classification.


### Validation and evidence

- E2 performed read-only source/artifact inspection only; no stack operations, database requests, code/test/config/evidence edits, commits or pushes.
- Inspected I1 saved full-gate `run.txt`, `exit-code.txt`, JUnit and timestamped Compose logs: legacy `test-results/showcall-verify-814fd83dd4ff/`, Encore `test-results/showcall-verify-a4e3b870b5e4/`, gateway `test-results/showcall-verify-66349a73c416/`. All exit 0, zero failures/errors/skips. Direct XML contains 1,084 testcase elements each, while suite counter is 1,097 because of 13 unittest subtest increments; gateway has 81 entries/counter. These are existing I1 results, not fresh E2 test runs.
- `git diff --check -- templates/SCOPING.md templates/TRADEOFFS.md templates/SEAMS.md tasks/E2-submission-documents.md` passed after draft and review correction. A read-only local Markdown link check passed for all three templates.
- Read the saved compact `investigation/evidence/i1-integration-20261024.jsonl` and local `test-results/i1-live-final/summary.json`, route publication/phase/identity records and `test-results/i1-integration/linux-publisher-check.json`. The original host-side publisher caused 28 HTTP 500s and no HTTP writes; the corrected Linux-view publisher passed actual org-7 cutover → rollback → final Encore reapply with one gateway instance and 58 successful sampled requests. Preserved failure and finite-sampling limits in the templates.
- Independently compared parsed `crew-before.json`/`crew-final.json`, `schema-before.json`/`schema-final.json` and `other-tables-before.json`/`other-tables-final.json`: exact equality for each pair. Current `proxy/routes.yaml` SHA-256 matches the saved final config (`3d09086645b195fe78d453a8fefe8f78584de7fa0141fe9cdff9cca378c25c51`). These are read-only checks of existing artifacts, not live DB queries by E2.
- Fresh SHA-256 comparison against the first reference-manifest record confirms both frozen contract JSON files unchanged. Current HEAD advanced concurrently to `4ff8a3c`; wrapper/support commit claims were reconciled after rechecking Git history/status.


### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| `/root/e2_reviewer`: recovery without restart was presented as a fact without a saved I1 artifact. | Qualified it as coordinator-reported recovery; saved recovery/retry evidence and final route state remain pending. | Correction applied; reviewer recheck requested. |
| `/root/e2_reviewer`: task completion must remain bounded while I1/R1 are pending. | Recorded E2 document review separately from integrated R1 approval; later incorporated actual saved I1 evidence without claiming R1 completion. | Correction applied; final reviewer recheck requested. |
| `/root/e2_reviewer`: concurrent `4ff8a3c` commit made working-tree-wrapper claims stale. | Updated snapshot, built scope and timing paragraphs to show wrapper/support committed, final routing/docs uncommitted. | Git history/status rechecked; final reviewer recheck requested. |
| `/root/e2_reviewer`: new I1 evidence supports final corrected live claims while retaining the first failure. | Added exact 28-error failed attempt, corrected Linux-view publisher, stable gateway, 58 successful samples, restored DB state, final org-7 routing and rollback procedure reference. | Reviewer independently inspected all compact evidence records/source hashes and final config; final wording recheck requested. |

### Handoff

- Changed files: `templates/SCOPING.md`, `templates/TRADEOFFS.md`, `templates/SEAMS.md`, and this task record only. These were uncommitted at the writer handoff.
- Integration requests / dependencies: I1 evidence is now incorporated. R1 must supply the integrated verdict; reconcile its findings before marking the whole wave complete. The I1/design owner should reconcile WAVE1_DESIGN status and host-publisher guidance with the corrected Linux-view procedure; E2 did not edit that file outside ownership. No shared-stack rerun is requested by E2.
- Remaining risks or blockers: initial deployment errors remain disclosed; corrected sampled success does not establish every interleaving. Integrated R1, remote Actions/branch protection and candidate-owned delivery/window classification are unverified. These remain explicitly documented rather than inferred.
- Final status and reviewer reference: E2 documents reconciled with saved I1 evidence and review corrections; `/root/e2_reviewer` final wording recheck approved with no blocking E2 findings. Integrated R1 approval is a separate remaining task.

### Final independent E2 review

- `/root/e2_reviewer` read the full `templates/WAVE1_DESIGN.md`, assessment brief, E2/I1 context, source/test/CI/history, seam map and maintenance findings, then reviewed the three final submission templates after the feedback loop. No blocking E2 findings remain. This document review does not approve the separate R1 integrated acceptance.
- Rechecked all three saved gate identities and XML counters directly: legacy/Encore each exit 0 with 1,084 testcase elements versus 1,097 suite counter (13 unittest subtest increments); gateway exit 0 with 81 entries/counter. No failures/errors/skips. These are inspected I1 results, not fresh reviewer runtime tests.
- Inspected every compact I1 evidence record; selected source hashes and the final route SHA-256 match current files. Saved gateway prepared/rollback/final health identities match. Saved crew-before bytes equal crew-restored and crew-final bytes. Final claims correctly preserve the initial 28 HTTP 500s and bound corrected success to 58 sampled requests.
- All local Markdown targets exist and scoped whitespace checks pass. No code/test/config/evidence changes, stack operations, database requests, commits or pushes were performed by this reviewer.
- Standalone review: `/Users/codexai/Documents/Codex/2026-10-24/i-m-doing-a-coding-challeng/outputs/E2-submission-review.md`. Final R1, remote execution/enforcement, assessment timing and the design-owner status/publication-guidance reconciliation remain separate handoffs.

### Packaging update

- After the approved document review, I1 was committed as `05bd1c0`. Refreshed the submission snapshot/commit-state wording to reflect that commit; the underlying verified results and R1 limitations are unchanged.
- Package also includes the previously created task index, R1 task scaffold and template index pointer so all linked documentation is present in a fresh checkout. No implementation or runtime changes are included.
