# D1: finish gateway acceptance

- **Owner:** `/root/d1_implementer` (review: `/root/d1_reviewer`)
- **Status:** Complete for D1; independent review and isolated gateway gate pass; production rollout remains D2/I1
- **Dependencies:** Existing B/C implementation; fixture contract agreed with D2
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../templates/SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

Own `proxy/app.py`, `tests/e2e/test_gateway_ingress.py`, `tests/unit/test_gateway_routing.py`, and this task file. Shared runner edits belong to I1. D2 owns rollout fixture changes; agree on their interface first.

## Task

1. Inspect the current gateway test and proxy changes; retain completed work.
2. Keep the frozen direct-backend corpus separate from the independently observed gateway contract. Test duplicate headers, encoded paths, methods, suffixes, redirects, tenant boundaries, and unchanged nonmigrated traffic.
3. Prove canonical org 7 list/show route to Encore while other orgs and crew/update, scheduling and messaging remain legacy-owned.
4. Verify a legacy HTTP write is visible in Encore reads and v3, restore the test data, and check read-side DB invariance using appropriate scoped comparisons.
5. Verify config-only rollback restores both list and detail behavior, with the same gateway instance and no restart. Fill concrete gaps in existing coverage.
6. Report focused test results and any shared runner changes to I1.

## Interface with other tasks

Use fixtures `tests/routes/legacy.yaml` and `tests/routes/mixed-org7.yaml`. Mixed routing moves only the two read prefixes for canonical org string `7`. Coordinate fixture changes with D2. Do not reconfigure the shared running development stack; I1 owns that rehearsal.

## Acceptance checklist

- [x] Relevant gateway/unit checks pass against the observed ingress contract.
- [x] Mixed routing and legacy HTTP-write visibility are demonstrated.
- [x] Both reads recover through config-only rollback without restarting the gateway.
- [x] Frozen expected responses are not weakened or regenerated from Encore.
- [x] Test state is restored and concrete evidence is recorded below.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Claimed D1 after inspecting active chat/task records: the other chat is implementing D2. D1 will use the existing `legacy.yaml` / `mixed-org7.yaml` fixture contract without editing those fixtures or production configuration. No shared development-stack changes or commits are authorized by this task.
- Read the complete Wave 1 design, task/index, assessment README, relevant SEAMS findings, gateway source, ingress tests, verification runner/topology and shared database fixture helpers. Existing ingress behavior and direct-backend goldens remain authoritative at their respective boundaries.

### Changes made

- Expanded gateway ingress comparisons for both migrated read prefixes: POST/PUT/PATCH/DELETE, HEAD/OPTIONS, trailing slash and suffixes, duplicated query values, parsing precedence and missing IDs. Canonical org 7 moves to Encore; orgs 3/12/19, padded orgs, unknown/missing orgs, and existing scheduling/messaging reads retain legacy ownership.
- Added installed reserved-tenant crew fixtures and owned-tenant list/detail/foreign-ID fallback reads. Global crew and six-table fixture-org snapshots now accompany actual reads for those owned tenants, instead of only checking unrelated empty scopes.
- Added exact expected database delta for the one legacy HTTP notes update, checks that wrapper and modern list/detail see it immediately, and repeated read-side invariance checks. Restore requires both HTTP success and application success; the complete crew state must return to the pre-write snapshot.
- Added explicit absence of upstream markers for all gateway-generated HEAD/OPTIONS 405s; checked supplied and generated trace IDs. Named parity assertions identify the failing request case in one stateful workflow.
- Extended unit cases for exact org-string routing, both list/detail prefixes, and config-only rollback of both prefixes. No new proxy behavior change was needed; existing dirty `proxy/app.py` implementation was preserved.

### Validation and evidence

- Local focused check: `.venv/bin/python -m pytest tests/unit/test_gateway_routing.py -q` -> **15 passed**.
- Implementer isolated gate: `python3 scripts/verify --backend gateway` -> **81 passed**, exit **0**, report directory `test-results/showcall-verify-bd1b6408d499/` (`junit.xml`, `compose.log`, `run.txt`, `exit-code.txt`). Its unique containers, network and route-state volume were removed. The last post-rollback DB assertion was added after this image's test COPY; the independent reviewer rerun must validate that final addition.
- Independent reviewer final-tree gate: `python3 scripts/verify --backend gateway` -> **81 passed**, **0 failures/errors/skips**, exit **0**, in `test-results/showcall-verify-ee1b1f804be9/`. This run includes the final post-rollback database assertion. JUnit, timestamped Compose logs, run identity and exit code are saved there. Source review compared the complete design, D1 scope, assessment brief, seam map and original gateway observations with the implementation; no blocking findings remain.
- Reviewer cleanup check found no remaining review-project volumes or networks; the four development containers retained the same IDs observed before the run. Reviewer's first attempt `showcall-verify-c775982f626d` could not access the sandboxed Docker socket; the approved isolated rerun above completed normally.
- Frozen corpus hashes remain `33b5e10b5a818e3cf472814cf477fdf9d0b87fb00bc0bd9e938a34d04cb54056` and `e6e6db978bd7672eab6c48d5604911ec3b6fe7d0020ba552e3bda19803edf336`, matching the preimplementation reference manifest.
- Initial sandboxed attempt `showcall-verify-6903ccd9e928` could not access Docker's Unix socket; no stack was started. Authorized Docker access completed the real run above.
- `git diff --check -- tests/e2e/test_gateway_ingress.py tests/unit/test_gateway_routing.py proxy/app.py` -> pass.
- Scope: global crew is checked exactly, while other tables are checked for the owned reserved fixture orgs. Seeded org-3/7 scheduling, messages and queue are excluded because legacy maintenance may legitimately change them. These checks do not prove globally quiescent seeded scheduling or newly characterize maintenance. All write/read checks use the disposable test topology, not the development stack.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| Reviewer: existing noncrew snapshot scopes had no corresponding owned-tenant ingress requests. | Install existing CrewFixture and read its reserved tenants through fallback ingress; document seeded scheduling exclusion. | Source review accepted; independent final gateway gate passed. |
| Reviewer: equality failures need the case name. | Added case labels to migrated, fallback and rollback comparisons. | Source review accepted. |
| Reviewer: rollback read phase lacked a final scoped DB invariant. | Assert complete scoped snapshot after rollback reads and before unchanged gateway instance check. | Final source reviewed; independent final gateway gate passed. |

### Handoff

- Changed files for this task: `tests/e2e/test_gateway_ingress.py`, `tests/unit/test_gateway_routing.py`, `tasks/D1-gateway-acceptance.md`. Existing proxy changes retained without new changes.
- Integration requests / dependencies: use unchanged `tests/routes/legacy.yaml` and `tests/routes/mixed-org7.yaml` inputs; no shared-runner changes requested. D2 production config preparation and I1 development-stack cutover/rehearsal remain separate work.
- Remaining risks or blockers: no D1 blocker. Direct legacy/Encore matrix and actual deployment rollout were not rerun by D1; this is focused gateway acceptance evidence only. Seeded noncrew maintenance invariance and exhaustive malformed-input equivalence are not claimed.
- Final status and reviewer reference: **PASS**, reviewed by `/root/d1_reviewer` against the complete implementation design and D1 scope, with a correction loop and independent final-tree Docker verification. Standalone review: `/Users/codexai/Documents/Codex/2026-10-24/i-m-doing-a-coding-challeng/outputs/D1-gateway-review.md`.
