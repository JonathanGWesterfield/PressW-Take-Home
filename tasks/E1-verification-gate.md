# E1: finish the verification gate

- **Owner:** `/root/e1_implementer` (review: `/root/e1_reviewer`)
- **Status:** Implemented and independently reviewed; full integration/GitHub execution pending
- **Dependencies:** Can prepare in parallel; finalize scenario selection with D1 and runner changes with I1
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

Own `.github/workflows/verify.yml`, `tests/README.md`, and this task file. Propose any `scripts/verify`, `tests/run_stack.py`, `tests/compose.yml` or `tests/conftest.py` changes to I1 rather than editing those files concurrently.

## Task

1. Inspect the current entry point and backend selectors; reuse the existing framework and implemented commands.
2. Define automatic named CI jobs for direct legacy, direct Encore, and gateway/mixed acceptance. Keep modern v3 checks included.
3. Make failures propagate and retain/upload JUnit, logs and diagnostic artifacts on failures as well as success.
4. Confirm that the gateway target uses its ingress-specific checks rather than silently substituting direct-corpus assertions or falling back to Callboard.
5. Document exact full verification commands, focused investigation commands, required check names, and known limitations.
6. Distinguish workflow execution from enforcement: document the required GitHub branch rules, but do not change remote settings in this task.

## Acceptance checklist

- [x] Automatic PR verification covers legacy, Encore and gateway acceptance.
- [x] Commands and scenario selections match the current implemented runner; reviewer confirmed ingress and modern assertions. Fresh combined live proof remains I1 work.
- [x] Modern tests remain part of acceptance.
- [x] Evidence upload is configured for failed runs and tests determine job status (remote execution remains unverified).
- [x] Documentation identifies required status checks without claiming remote protection was configured.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Read the assessment, seam map, coordination index, design, current workflow and runner before edits. Preserved existing unrelated work; no shared runner/stack/application files changed.

### Changes made

- Added automatic PR/main matrix checks for legacy, Encore and gateway with fail-fast disabled, direct exit propagation, and always-upload artifacts unique per backend/run/attempt. Preserved manual backend selection as a separate job.
- Updated tests/README.md with exact check names/commands, explicit ingress and modern selection, evidence behavior, bounds, and remote-enforcement limits.

### Validation and evidence

- Fresh bounded check: `.venv/bin/python -m pytest tests/unit/test_verification_runner.py tests/unit/test_stack_runner.py -q` → **19 passed in 0.18s**. These exercise failure/cleanup exit semantics, isolated ownership, both-target execution, and explicit gateway selection without containers. Modern suite inclusion was verified by source inspection, not an explicit assertion in these 19 tests. Coordinator independently reported 19 passing in 1.38s; reviewer also independently reported 19 passing.
- Fresh PyYAML `BaseLoader` structural assertions on `.github/workflows/verify.yml` passed: PR/main/manual events; all three backend entries with distinct names; `fail-fast: false`; direct verify command with no `continue-on-error`; both upload steps use `always()` and run/attempt-qualified names. `BaseLoader` preserves GitHub's `on` key instead of YAML 1.1 boolean coercion.
- `git diff --check -- .github/workflows/verify.yml tests/README.md tasks/E1-verification-gate.md` → exit 0. `actionlint` is unavailable; YAML structure checks are not a GitHub Actions execution.
- No Docker stack/matrix or remote workflow was run by E1. No fresh full acceptance artifact exists for this task. CI artifacts will be `verification-<backend>-<run_id>-<run_attempt>` containing `test-results/<project>/`; manual artifacts add `manual-`. I1 owns full combined verification and recorded reports.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| `/root/e1_reviewer`: initial implementation independently reviewed; no implementation findings; final record review requested precise evidence wording. | Clarified that runner tests assert gateway selection; modern inclusion was source-inspected. Reviewer read the full implementation design and checked scope against E1. | Approved after fresh 19-test runner check, YAML/README checks, ingress served-by/modern source inspection, and scoped whitespace check. GitHub execution and remote branch settings remain unverified. |

### Handoff

- Changed files: `.github/workflows/verify.yml`, `tests/README.md`, `tasks/E1-verification-gate.md`.
- Integration requests / dependencies: I1 must run all three full commands against the final combined tree. D1/I1 should confirm the already-implemented gateway scenario selection; no runner changes requested.
- Remaining risks or blockers: GitHub execution/upload and remote required-check enforcement are unverified; no remote settings were changed. Existing runner startup/test bounds fit the 30-minute automatic job; manual both has 60 minutes.
- Final status and reviewer reference: `/root/e1_reviewer` approved the initial implementation with no implementation findings; final evidence wording was corrected as requested. Ready for I1 integration and final full verification. Packaged for a dedicated E1 commit; integration verification remains pending.
