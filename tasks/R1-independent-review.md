# R1: independently review the integrated Wave 1 result

- **Owner:** `/root/r1_implementer` (independent review: `/root/r1_reviewer`)
- **Status:** PASS for bounded local Wave 1; later CI/upload success observed at `31758ea`; required-check/PR enforcement disabled
- **Dependencies:** I1 combined implementation/evidence; coordinate E2 final documents
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../templates/SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

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

- [x] Every declared Wave 1 acceptance requirement has evidence or an explicit blocker.
- [x] No frozen expectations were weakened to accommodate the replacement.
- [x] Final integrated checks and actual cutover/rollback evidence are assessed.
- [x] Feedback is routed to owners and corrections are rechecked.
- [x] Final verdict and limits are written below and handed to I1/E2.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Claimed after confirming I1 passed, E2 document review passed, and the other chat completed its E2 packaging commit (`2f52b24`). No shared-stack operations are planned; use existing integrated evidence plus independent bounded checks. Preserve the unrelated IDE changes.

### Changes made

- Corrected the frozen-contract README's obsolete pre-wrapper claim that direct
  Encore parity was expected to fail. It now records the final separately seeded
  `--backend both` result, keeps the immutable corpus distinction, and states
  that gateway ingress is a separate contract.
- Reconciled the design's finished-slice status and publication instructions
  with I1's bounded evidence. It now distinguishes local direct/gateway/live
  success from pending R1 and remote enforcement, retains the failed host-side
  publication provenance, and points operational publication at D2's tested
  Linux-view helper.

### Validation and evidence

- Read the assessment brief, complete Wave 1 design, root seam map, D1/D2/E1/E2
  and I1 records, current application/gateway/test sources, final route file,
  frozen-corpus manifest, I1 compact evidence, and final JUnit reports.
- Parsed final reports directly: legacy `showcall-verify-814fd83dd4ff` and
  Encore `showcall-verify-a4e3b870b5e4` each exited 0 with 1,084 testcase
  elements, JUnit suite count 1,097, and zero failures/errors/skips; gateway
  `showcall-verify-66349a73c416` exited 0 with 81 testcase elements and zero
  failures/errors/skips. These are existing I1 artifacts, not an R1 rerun.
- Fresh bounded source checks: `.venv/bin/python -m pytest
  tests/unit/test_crew_repository.py tests/unit/test_legacy_crew.py
  tests/unit/test_v3_crew.py tests/unit/test_gateway_routing.py
  tests/unit/test_verification_runner.py tests/unit/test_stack_runner.py -q`
  passed **65 tests** (one upstream TestClient deprecation warning).
- `git diff --check` passed before the documentation correction. Frozen corpus
  hashes match the saved manifest; full matrix/live operations remain I1-owned
  and are not repeated by R1.
- After reconciliation, `git diff --check -- templates/WAVE1_DESIGN.md
  tests/characterization/README.md templates/SCOPING.md templates/TRADEOFFS.md
  templates/SEAMS.md tasks/E2-submission-documents.md
  tasks/R1-independent-review.md tasks/README.md` passed. A local Markdown
  target check over those files also passed.

### Acceptance assessment

The assessment below is R1's original review snapshot. The subsequent dated
evidence update at the end records CI/upload success without rewriting that
review's history or claiming required-check enforcement.

| Requirement | Evidence and R1 disposition |
| --- | --- |
| Scope and shared reads | Source review confirms only legacy crew list/show for canonical org 7 route to Encore; wrappers and v3 share tenant-scoped retrieval. Writes, maintenance and schema ownership remain Callboard. PASS. |
| Direct parity and frozen reference | Both final direct reports exit 0 with 1,084 testcase elements; frozen corpus hashes match the pre-port manifest. No expectation was regenerated or weakened. PASS, bounded to observed inputs. |
| Modern contract and tenant safety | Source/unit review covers explicit tenant predicates, bound raw-ID cast, session rollback/close, secret-free projection and intentionally distinct v3 validation. PASS. |
| Gateway, writer visibility and rollback | Final gateway report exits 0 with 81 tests. I1 evidence records canonical-only routing, legacy HTTP write/read visibility and restoration, unchanged gateway identity through rollback, and final mixed reapply. PASS, with finite live sampling. |
| Publication/recovery | The first Colima host-side publication failed with 28 HTTP 500s before any HTTP write. The corrected Linux-view publisher has saved concurrency/live-rehearsal evidence. PASS for the corrected procedure; do not use host-side rename. |
| Release enforcement | Named workflow jobs exist, but remote Actions execution/artifact upload and GitHub required-check/PR enforcement were not verified. Explicit outstanding release gate; not a local implementation blocker. |

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| IMPORTANT: `tests/characterization/README.md:132-134` described the pre-wrapper future state and contradicted final direct Encore evidence. Independent reviewer. | Replaced it with the final separately seeded `--backend both` result, explicit immutable-corpus/direct-wrapper scope, and separate ingress qualification. | Reviewer rechecked: accurate; no frozen expectation changed. |
| IMPORTANT: `templates/WAVE1_DESIGN.md` status/runbook wording presented completed D/I1 evidence as pending. Independent reviewer. | Reconciled status/runbook with final reports and the corrected Linux-view publisher; retained 28-error failed-attempt provenance, finite-sampling limit, and remote gaps. | Reviewer rechecked: accurate; no implementation/config behavior changed. |

### Handoff

- Changed files: `templates/WAVE1_DESIGN.md`,
  `tests/characterization/README.md`, `templates/SCOPING.md`,
  `templates/TRADEOFFS.md`, `templates/SEAMS.md`,
  `tasks/E2-submission-documents.md`, and this task record.
- Integration requests / dependencies: submission templates now incorporate the
  verdict; parent owns the task-index final milestone update. No I1 rerun or
  shared-stack action is requested.
- Remaining risks or blockers: remote CI execution/artifact upload and GitHub
  required-check/PR enforcement are unverified release gates. Candidate-supplied
  interview timing is not derivable from repository evidence. Compatibility and
  live publication evidence remain bounded; host-side rename is unsafe on this
  Colima share.
- Final status and reviewer reference: **PASS for bounded local Wave 1**.
  `/root/r1_reviewer` independently matched selected implementation/test/runner
  hashes to I1's source-after manifest, verified frozen hashes/final route hash,
  parsed final reports and passed the same fresh 65-test subset. No
  BLOCKER/IMPORTANT implementation finding remains. Its final wording recheck
  approved all eight changed Markdown documents/index, local links and scoped
  `git diff --check`, with no further finding.

### Subsequent GitHub evidence (2026-10-24)

Read-only inspection of [run 40125062976](https://github.com/JonathanGWesterfield/PressW-Take-Home/actions/runs/40125062976)
confirms all three automatic verification/upload jobs passed at `31758ea`, with
three nonexpired artifacts listed. [Recorded metadata](../investigation/evidence/github-actions-20261024.jsonl)
keeps the remote revision separate from local JUnit counts and live rehearsal.
Application/test/workflow bytes match that revision; later local documentation
and IDE commits were not themselves executed by that run. GitHub reported `main`
unprotected and the repo public. Required-check/PR enforcement, private sharing,
candidate timing disclosure and final-revision publication/verification remain.
This update changes no runtime behavior or original R1 verdict.
