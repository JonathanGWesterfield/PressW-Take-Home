# Seam Map

This is the submission summary; [the root investigation map](../SEAMS.md) contains
longer probe notes and links. Discovery used public HTTP, the supplied source and
schema, and Postgres; it did not inspect the Callboard binary/container internals.
Observations below describe specific experiments, not universal guarantees.

## Probe log

| Probe | Observation | Conclusion |
| --- | --- | --- |
| `recorded-*`, `baseline` → `before-writes` in [HTTP log](../investigation/evidence/http.jsonl) and [DB timeline](../investigation/evidence/db-timeline.json) | 32 supplied GETs captured; all six tables unchanged across this interval. | Crew reads are a plausible first wave; this is observed read invariance, not proof for all inputs. |
| `crew-foreign`, `crew-update-foreign`, `crew-no-org`, `crew-bad-id` | Cross-org IDs yield HTTP-200 `not found`; missing org and invalid IDs yield distinct application errors, including Postgres diagnostics. | Tenant scope and error precedence belong in the compatibility contract. |
| `crew-zero-size-page-two`, `crew-per-negative`; frozen fixture/fuzz cases | Size zero returns all rows; negative sizes behave like slicing; Python pagination parsing differs from PostgreSQL detail-ID parsing. | Modern validation must not be reused as the legacy parser. |
| `crew-rate-lead-update` and following tick | Only crew rate/lead changed; existing accepted pay stayed unchanged. | Crew fields influence later decisions; do not introduce retroactive repricing. |
| `shift-create` | Shift 61 copied venue name/timezone; New York local 07:00 stored as 12:00 UTC in the tested date. | Scheduling depends on venue metadata and local-time interpretation. |
| `assignment-offer`, `assignment-accept` | Offer created assignment 181 plus CALLOUT 121; acceptance changed O→A, pay to $187 (8.5 × $22), open slots 2→1, lead to 181, and queued ACCEPT. | Acceptance is a multi-table business transition; crew lead fallback exists in this case. |
| `confirm-stale`, `confirm-fresh`, `stale-direct-accept` | Confirmation accepts an assignment, marks CALLOUT read, creates CONFIRM, and updates staffing/pay/queue. A 30-day-old offer was accepted before maintenance. | Messaging has another acceptance entry point; expiry was not enforced synchronously in these probes. |
| `shift-cancel`, `shift-cancel-repeat` | Shift became CXL, assignments 88–90 became X, three CXL messages appeared; open slots was not reset. Repeat returned `already cancelled` without writes. | Cancellation spans scheduling/messages and contains observable stale projections and failure behavior. |
| `after-cancel-repeat` → `after-maintenance` | At 16:19:18 UTC, 82 old offers became E, eight ACCEPT queue entries disappeared, three DIGEST messages appeared; no crew/venue/shift/pay changes observed. | Maintenance owns assignments, queue, and messages; this tick did not establish reconciliation or repricing. |
| Same tick, org 7 | Crew 18 received DIGEST; crew 2, whose lead flag was cleared, did not, despite digest preference Y. | Digest eligibility depends on crew state; exact precedence remains unresolved. |
| [Full replay and direct SQL follow-up](../investigation/MAINTENANCE_BEHAVIOR.md), 13:08:03 → 13:09:06 America/Chicago | After all 51 supplied requests, three previously prepared ACCEPT queue events disappeared and five DIGEST messages appeared. All captured crew, venue, shift and assignment fields stayed unchanged. | Independent evidence for queue consumption and per-org digest fan-out; immediate replay/acceptance effects are excluded from this maintenance delta. |
| Same experiment, follow-up through 13:15:13 | No additional captured changes across the next expected window; queue remained empty. | No duplicate digests were observed; unchanged snapshots do not independently prove another job execution. |
| `confirm-after-expiry`, `accept-after-expiry`, `confirm-repeat` | `not open`; snapshots showed no corresponding writes. | Preserve failure behavior; do not silently make repeats idempotent successes. |
| [Frozen corpus](../tests/characterization/README.md), [crew notes](../investigation/LEGACY_CREW_BEHAVIOR.md) | 171 original and 828 fuzz request/response cases captured before Encore; encoded routes, duplicate headers, raw preferences, nulls, and exact bytes matter. | The reference is executable and independent of the new implementation; its coverage is bounded. |
| [Gateway boundary](../investigation/evidence/gateway-boundary.jsonl) | Direct HEAD/OPTIONS return 200, gateway returns 405; 308 redirect Host/HTML differs by ingress. | Direct and gateway parity need different observed baselines. |
| [Recorded replay](../investigation/evidence/recorded-replay-2026-10-24.json) | All 51 requests returned HTTP 200; three bodies reported failure; all were served by Callboard. GETs were sent before POSTs, without DB snapshots. | Replay documents legacy outcomes, not Encore parity or independently verified persisted effects. |

## Couplings found

- **Crew (`tg_crew`) → scheduling and digests:** acceptance reads rates/lead state;
  maintenance recipients depend on crew state. Reads can move while those writers
  retain the same shared fields. Crew writes require broader compatibility work.
- **Scheduling (`shifts`, `assignments`) ↔ messaging (`messages`):** offer,
  confirmation, acceptance, and cancellation cross these tables. Names/titles are
  duplicated. Roster also returns HTML, so JSON-only parity would miss a frontend
  contract. Observed co-occurrence does not prove transaction atomicity.
- **Assignments → `callboard_queue` → maintenance → messages:** deferred effects
  continue for org 7 after an HTTP route flip. Routing does not transfer job ownership.
- **`venues` → shifts:** copied metadata and venue-local timestamps are part of
  scheduling semantics. The schema has no foreign keys for these relationships;
  application writers must enforce ownership and consistency.

## Wave plan

| Wave | What moves (endpoints, behaviors, tables) | Why this is safe to move as a unit |
| --- | --- | --- |
| 1 | Org-7 crew list/show reads plus modern list/detail; read existing `tg_crew`. | No new writes, copied state, or maintenance worker. Callboard retains all writers/jobs; next-request reads observe committed shared data. Implemented and verified directly and at ingress; I1 demonstrated actual org-7 cutover/rollback/reapply. Final integrated R1 review remains pending. |
| 2 | Coordinated scheduling slice: crew writes, shift operations/roster, assignment offer/accept, message confirmation, cancellation, and associated background invariants over crew/venues/shifts/assignments/messages/queue. | Keep acceptance entry points and dependent writes under one defined transaction/job owner. Subdivide only after characterizing and preserving those contracts. Not yet proven safe or implemented. |
| 3 | Remaining manual messaging, delivery/read preferences, and retirement of residual legacy endpoints/jobs/storage. | Move after scheduling producers/consumers have explicit contracts and legacy jobs can be disabled safely. Requires additional discovery. |

## Cut couplings & mitigations

- **Legacy writer / Encore reader:** org 7's crew update remains on Callboard;
  Encore reads `tg_crew` directly without caches. The isolated gateway suite
  verifies a persisted legacy HTTP update followed by wrapper and v3 list/detail
  reads, then restores fixture state and checks scoped DB invariants. I1
  repeated live write visibility and restored crew state exactly. Do not
  route the whole crew prefix: it includes update. Use individual list/show
  prefixes with an org-7 override and legacy defaults.
- **Gateway / wrapper:** prefix routing also selects suffixes and wrong methods;
  exact header-string matching leaves some padded org values on legacy. Preserve
  those decisions and compare actual ingress bytes/headers against legacy before
  cutover. Isolated tests demonstrate rollback by changing only the two org
  overrides and checking the same gateway instance. The deployment configuration
  uses a directory mount for atomic rename. The first host-side publication
  caused 28 HTTP 500s on the Mac/Colima share before recovery. I1 corrected it
  with validated publication from a temporary Linux-view container, then
  demonstrated cutover/rollback/reapply with the same gateway instance and 58
  successful sampled requests. Use the corrected [D2 publisher](../tasks/D2-rollout-configuration.md);
  host-side rename alone is unsafe on this share. The supplied single-file
  mount can retain a replaced inode; in-place writes can expose partial YAML.
- **Crew writes / legacy scheduling:** changing rate/lead semantics could alter
  future pay or digest recipients. Preserve shared field meaning and do not add
  repricing; characterize more before transferring writes.
- **Confirmation / acceptance / cancellation:** separate implementations can mark
  messages read without acceptance, accept twice, or cancel only part of a shift.
  Use one acceptance transition and transactional ownership; probe contention and
  rollback before splitting these writers.
- **New HTTP scheduling / legacy maintenance:** tonight's legacy job still runs
  for half-migrated org 7. New queue formats or a second consumer could lose or
  duplicate digests or race expiry. Keep the legacy owner until an explicit per-org
  job handoff exists. Config rollback cannot undo data mutations or sent messages.

## Open questions

- Exact offer-expiry cutoff, digest preference/lead precedence, crash/retry
  delivery behavior, and which staffing projections maintenance repairs, if any.
- Concurrent accept/confirm/cancel, duplicate offers, overbooking, and failure-path
  atomicity. A sequence of DB snapshots alone cannot prove these guarantees.
- DST ambiguity/nonexistent local times and roster HTML escaping before scheduling
  moves; production org authentication before trusting client-supplied identity.
- Remaining unrecorded operations and real tenant sizes; the finite recording and
  corpus are not the full production API.
- [R1](../tasks/R1-independent-review.md) integrated review, remote CI execution/branch
  enforcement and candidate-supplied interview timing remain outstanding.
  Direct legacy/Encore, modern and gateway/mixed checks pass; the saved
  [I1 evidence](../investigation/evidence/i1-integration-20261024.jsonl) demonstrates
  actual cutover/rollback/reapply after a corrected publication failure.
  [Current evidence](TRADEOFFS.md) lists exact reports, reconciled counts and
  limits; finite success samples do not prove every possible interleaving.
