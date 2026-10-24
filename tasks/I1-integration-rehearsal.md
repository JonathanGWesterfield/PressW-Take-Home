# I1: integrate, verify and rehearse the migration

- **Owner:** `/root/e1_implementer` (review: `/root/e1_reviewer`)
- **Status:** PASS; combined gates and corrected live rehearsal independently reviewed
- **Dependencies:** D1/D2/E1 ready; coordinate E2 draft and R1 review
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

The coordinator owns `scripts/verify`, `tests/run_stack.py`, `tests/compose.yml`, `tests/conftest.py`, this task file, and changes to the shared running stack. Other workers submit requests for these shared files in their handoffs. Coordinate implementation-file corrections with their task owner.

## Task

1. Read D1/D2/E1 handoffs and resolve shared interfaces/file conflicts. Preserve all unrelated working-tree changes.
2. Run targeted checks for changed components, then one complete direct legacy/Encore and gateway acceptance matrix. Use isolated test databases. Avoid redundant full matrices after every small edit.
3. Save the current live routing/config and confirm health. Prepare the actual gateway topology once with all routing still on Callboard, as specified by D2.
4. Apply canonical org-7 read routing. Verify served-by decisions, other orgs/paths staying legacy, legacy HTTP-write visibility through Encore, and relevant response/DB invariants.
5. Revert the two read routes by config edit only; demonstrate both reads recover without restart. Reapply the intended final org-7 route configuration and record final state.
6. Leave all writes and maintenance on Callboard. Use the existing maintenance evidence and appropriate read checks; no replacement worker or repeated broad investigation is needed.
7. Provide combined code/evidence to R1. Apply owner corrections and rerun affected checks; repeat the full matrix when integrated changes invalidate earlier results.
8. Provide final results to E2. Commits, pushes and remote rule changes remain with the user.

## Acceptance checklist

- [x] Combined direct legacy/Encore, modern, and gateway checks pass.
- [x] Actual routing moves only intended crew read prefixes/canonical org and preserves legacy writers/jobs.
- [x] Corrected live config-only rollback is observed without gateway restart; first failed attempt is retained separately.
- [x] Final intended mixed route state and Linux-view recovery procedure are recorded.
- [x] Owned isolated resources/helpers are absent; original global crew state and DB schema restored, existing DB/backends retained.
- [x] Coordinator/reviewer receive the exact evidence below for R1/E2; independent I1 verdict is PASS.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Read the full design and D1/D2/E1 handoffs; waited for D1 final independently accepted gate before combined runs/live actions.
- Fresh targeted runner checks passed: `.venv/bin/python -m pytest tests/unit/test_verification_runner.py tests/unit/test_stack_runner.py -q` → 19 passed (0.23s).
- Ran one combined direct/gateway acceptance matrix, then existing-stack rehearsal. Preserved the first failed live attempt and corrected the deployment publication mechanism before a fresh reviewed retry.

### Changes made

- Adopted existing runner/discovery/topology support; no further runner/application/test source edits were necessary. Other owner committed support while these gates ran; byte fingerprints confirm only the intentional final `proxy/routes.yaml` changed since the tested source snapshot.
- Published final `tests/routes/mixed-org7.yaml` contents to `proxy/routes.yaml`. Only canonical org string `7` selects Encore for the list/show prefixes (including suffix/method error paths); writes, other orgs, scheduling and messaging stay Callboard-owned. Modern callers use direct Encore port 8092.
- Corrected D2's runbook under coordinator authorization after the real Colima mount exposed host-side rename incoherence. Clone-visible `publish_d2_routes` now validates and atomically publishes inside a disposable Linux-view helper container; gateway remains read-only and no persistent worker/service was added.
- Added compact clone-visible [integration evidence](../investigation/evidence/i1-integration-20261024.jsonl). Detailed traces, DB comparisons and scratch rehearsal code remain ignored/local; summary excludes passwords, password digests and full crew snapshots.

### Validation and evidence

| Full command | Backend/project | Fresh result |
| --- | --- | --- |
| `python3 scripts/verify --backend both` | legacy `showcall-verify-814fd83dd4ff` | Exit 0; pytest **1084 passed** in 11.40s; JUnit **1097**, 0 failures/errors/skips. |
| Same sequential `both` command, separately seeded project | Encore `showcall-verify-a4e3b870b5e4` | Exit 0; pytest **1084 passed** in 9.42s; JUnit **1097**, 0 failures/errors/skips. |
| `python3 scripts/verify --backend gateway` | `showcall-verify-66349a73c416` | Exit 0; pytest/JUnit **81 passed** in 2.11s, 0 failures/errors/skips. |

JUnit includes unittest subtests; it is not the pytest collected-test count. Each full run emitted one upstream Starlette/httpx TestClient deprecation warning. Reports are in `test-results/<project>/` (`junit.xml`, `compose.log`, `run.txt`, `exit-code.txt`); command logs/source manifests are in `test-results/i1-integration/`. Label-scoped checks confirmed no containers, networks or volumes remain for all three owned projects, and no I1 helper containers remain. Images/build cache intentionally remain.

- Source before/after SHA-256 manifests cover app, gateway, runner, tests and fixtures. Only `proxy/routes.yaml` changed (the intended real final cutover); code bytes tested by all three gates remained identical despite dependency commits changing HEAD. Both frozen corpus hashes match D1's preserved reference: `33b5e10b5a818e3cf472814cf477fdf9d0b87fb00bc0bd9e938a34d04cb54056` and `e6e6db978bd7672eab6c48d5604911ec3b6fe7d0020ba552e3bda19803edf336`.
- First live attempt (`test-results/i1-live-attempt1/`) failed before any HTTP write: host `os.replace` briefly made `/srv/routes/routes.yaml` missing in the Colima view and ingress returned 500. Exact host bytes were restored; mount convergence restored Callboard ingress without restart. This attempt is **not** successful zero-disruption evidence.
- Corrected publication was first checked in a temporary directory with disposable Linux-view reader/publishers: **6319 concurrent reads**, zero errors, both route versions observed. Reviewer inspected concrete helper code before live retry.
- Fresh corrected command `.venv/bin/python test-results/i1-live-final/live_rehearsal.py` → exit 0, **PASS**. Raw JSONL responses, original route bytes, sanitized local DB comparisons, health, container/mount identities and publication logs are in `test-results/i1-live-final/`. Only gateway was recreated during preparation with routes still legacy; DB, Callboard and Encore containers retained their IDs.
- Prepared gateway instance `a832e75599fa46609181b7a5a8fbcd8f` stayed identical through cutover, rollback and final mixed reapply. Full gateway container ID, start time and restart count also stayed unchanged; the actual containing-directory bind is read-only. Both reads recovered exact baseline status/body/relevant headers after rollback; mixed responses differed only by intended served-by marker. Nonmigrated orgs/paths stayed Callboard-served; HEAD/OPTIONS retained gateway 405/no-upstream-marker behavior.
- Controlled notes update for existing org-7 crew 2 was sent through legacy HTTP only, with pre-write whole-crew guard and unique marker. SQL confirmed the exact expected one-field delta; Encore wrapper list/detail and direct modern list/detail immediately saw it. A nested `finally` restored only our marker through legacy HTTP and verified the entire global crew state exactly matched its original snapshot. No other field/password change, DB reset or schema migration occurred.
- **58 continuous public crew-list samples** across publication/write restore/rollback/final reapply all returned HTTP 200, `result: ok`, and valid Callboard/Encore served-by markers. This is sampled deployment evidence, not proof over every possible interleaving or filesystem.
- DB schema fingerprint before/final is identical. Noncrew table fingerprints are retained in local/evidence summaries; seeded scheduling/message maintenance may evolve independently and globally quiescent scheduling is not claimed. Callboard retains its original maintenance process.

### Final state and recovery

Final `proxy/routes.yaml` equals `tests/routes/mixed-org7.yaml`. Modern `/v3/crew` callers remain direct on 8092. For rollback, define the clone-visible `publish_d2_routes` function from [D2](D2-rollout-configuration.md), then run `publish_d2_routes tests/routes/legacy.yaml` for all-legacy routing; use `test-results/i1-live-final/routes-before.yaml` instead for exact original comment/byte restoration. No restart or deploy is needed. Use the Linux-view publisher on this Colima deployment; host-side rename was observed unsafe. The publisher helper exits/removes itself and has no network access; only its route directory is writable.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| Reviewer pre-live: notes restoration failure could bypass route rollback. | Nested notes cleanup inside a guaranteed route-publication `finally`. | Reviewer AST fault injection exercised crew-read, restoration HTTP and application failures; every path published original routes. |
| Actual failed live attempt: host/Colima rename visibility broke ingress. | Preserved failed attempt, recovered original routes, switched to reviewed Linux-view one-shot publisher; amended D2 recovery instructions. | Temporary concurrent-reader check and fresh full live retry passed; 58 live samples had no 500/application failures. |
| Final independent evidence/config review. | No further findings. | `/root/e1_reviewer` independently reconciled summary/source/corpus hashes, JUnit/exits, full response equality, write/schema restore, sampling and process IDs against raw artifacts; embedded D2 publisher exactly matches tested helper. Final approval: PASS. |

### Handoff

- Changed files: `proxy/routes.yaml`, D2 runbook correction in `tasks/D2-rollout-configuration.md`, this I1 record, and `investigation/evidence/i1-integration-20261024.jsonl`. Shared runner/support files were adopted/committed by the dependency owner; I1 did not edit those sources.
- Integration requests / dependencies: coordinator can pass this record and compact evidence to R1/E2; no outstanding application/shared-runner correction is requested.
- Remaining risks or blockers: no unresolved I1 findings. R1 whole-system review and E2 submission reconciliation remain separate tasks. GitHub execution/upload and branch enforcement remain unverified. Use Linux-view publication on this Colima share; bounded compatibility and sampled live evidence are not exhaustive.
- Final status and reviewer reference: **PASS**, independently approved by `/root/e1_reviewer` with both correction loops resolved. Ready for coordinator packaging and R1/E2 handoff. No commits were made by I1; coordinator packages the dedicated commit.
