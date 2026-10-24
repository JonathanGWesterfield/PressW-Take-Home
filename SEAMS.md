# Seam map and migration proposal

Investigation started 2026-10-24, approximately 11:14 America/Chicago, when the stack
first started successfully. This is not a claim about when the assessment timer began.
The initial attempt in Downloads failed because Colima could not mount that directory.
All discovery used the supplied schema/source, public HTTP endpoints, and Postgres.

## Evidence and probe log

Exact HTTP requests, status codes, headers, and response bodies are in
[`investigation/evidence/http.jsonl`](investigation/evidence/http.jsonl); use the
labels below to locate probes. [`investigation/evidence/db-timeline.json`](investigation/evidence/db-timeline.json)
contains a complete baseline and ordered field changes for every snapshot.
Raw snapshots remain local; password hashes are omitted from both forms.
`python3 investigation/probe.py --snapshot NAME` captures all six tables in one
statement; `--recorded-reads` captures the supplied GET requests without replaying
the supplied writes. It uses Python's standard library and installs nothing.

| Probe / snapshots | Observation | Conclusion |
| --- | --- | --- |
| `recorded-*`; `baseline` → `before-writes` | All 32 recorded GET requests captured. All six tables identical between snapshots. | These reads produced no observed DB changes in this run. |
| `recorded-0`, `recorded-3` | Crew responses expose `user_name` as `crew_name`, rates as two-decimal strings, `is_lead` as `Y`/`N`. Show additionally exposes the raw preferences JSON string under `prefs`. | Legacy serialization belongs in an explicit adapter; modern schema should use honest names and types. |
| `crew-foreign`, `crew-update-foreign`, `recorded-50` | Reading/updating a crew member owned by another org returns HTTP 200 with `{"error":"not found","result":"fail"}`. | Scope reads and writes by both org and record ID. |
| `crew-no-org`, `crew-bad-org`, `crew-missing-id`, `crew-bad-id` | Missing/malformed org reports `missing org`; invalid IDs leak Postgres conversion errors. All use HTTP 200 JSON. | Framework validation responses would break wrapper compatibility. Document safer errors separately in v3. |
| `crew-page-zero`, `crew-page-negative`, `crew-pagination-bad`, `crew-empty-page`, `crew-empty-size` | Zero/negative page becomes 1; invalid nonempty page returns a Python conversion error; empty values use defaults. | Pagination coercion is observable behavior. |
| `recorded-2`, `crew-zero-size-page-two`, `crew-per-negative`, `crew-negative-size-page-two` | `per_page=0` returns all eight rows, even on page 2; `-1` returns seven rows on page 1 and none on page 2. | Legacy pagination has slicing-like edge cases. Do not silently impose v3 bounds in wrappers. |
| `crew-page-two`, `crew-page-beyond`, `crew-empty-org`, `crew-unknown-filter`; later `list_default` fixture case | ID-ordered pages, unchanged total beyond the last page, empty list for an unknown org, and ignored tested search/sort parameters. A later 32-row fixture establishes the default page size as 25. | Preserve total, ordering, ignored parameters, and the observed 25-row default. |
| `gateway-routing` | Gateway response has `X-Served-By: callboard` and a trace ID. | Routing is currently wholly legacy; headers provide a direct cutover check. |
| `crew-notes-update`; `before-writes` → `after-crew-notes` | Only crew 10's notes changed. | Notes are locally stored, but this does not establish independence of all crew updates. |
| `crew-rate-lead-update`; `after-crew-notes` → `after-crew-rate-lead` | Only crew 2's rate and lead flag changed; submitted `crew_name` and `display_name` were ignored. Accepted assignment pay was initially unchanged, and stayed unchanged through the observed tick. | Rate changes do not retroactively reprice accepted work in this experiment. |
| `shift-create`; `after-crew-rate-lead` → `after-shift-create` | New shift 61 stores venue name/timezone copies. 12/04/2026 07:00 in New York stores epoch 1796385600 (12:00 UTC). | Shift storage contains denormalized venue metadata; time parsing is venue-dependent in this probe. |
| `assignment-offer`; `after-shift-create` → `after-offer` | Assignment 181 and CALLOUT message 121 created together. Both store a title copy. | Offering work crosses scheduling and messaging tables. |
| `assignment-accept`; `after-offer` → `after-accept` | Assignment changes O→A with $187.00 pay (8.5 hours × $22); shift open slots changes 2→1; lead assignment becomes 181; an ACCEPT queue row appears. Crew 14 is not marked lead. | Acceptance owns several coupled invariants, including lead fallback. It cannot safely move as just one table write. |
| `assignment-accept-repeat`; `after-accept` → `after-accept-repeat` | HTTP 200 `not open`, with no DB change. | Repeat acceptance is rejected, rather than treated as idempotent success. |
| `confirm-stale`, `confirm-fresh`; `after-accept-repeat` → `after-confirm-21` → `after-confirm-28` | Confirmation accepts linked assignments, marks source CALLOUT read, writes a CONFIRM message, updates staffing/lead/pay, and queues ACCEPT. The 30-day-old offer was confirmable before maintenance. | Message confirmation is a second entry point into acceptance. Expiry is not checked synchronously in these observed paths. |
| `stale-direct-accept` | A second 30-day-old offered assignment was accepted directly before maintenance. | Do not infer an age check from the maintenance policy. |
| `offer-foreign-crew`, `offer-foreign-shift` | Each returns `not found`. | Both related objects need org ownership checks. |
| `message-send`; `after-confirm-28` → `after-message-send` | NOTE message with no assignment created. The same interval also includes `stale-direct-accept`; its assignment/shift/queue changes must not be attributed to message/send. | Manual notes have a smaller footprint than confirmations, but the message prefix contains both. |
| `shift-cancel`; `before-maintenance` → `after-cancel` | Shift 30 becomes CXL; assignments 88–90 become X; three CXL messages created. Its open_slots value is not synchronously reset. | Cancellation spans shifts, assignments, and messages; cached staffing can lag. |
| `shift-cancel-repeat`; `after-cancel` → `after-cancel-repeat` | `already cancelled`, with no further writes. | Repeat cancellation has an explicit legacy failure contract. |
| `recorded-8`, `roster-post-accept` | Roster rows are HTML (`text/html; charset=utf-8`), including `&mdash;` for missing pay. | Scheduling also owns a frontend HTML representation, not just JSON. |
| `after-cancel-repeat` → `after-maintenance` | At 16:19:18 UTC, 82 remaining old offers changed O→E, all eight ACCEPT queue rows were removed, and three DIGEST messages were added. No crew, venue, or shift fields changed; no pay changed. | The job crosses assignments, queue, and messages. Reconciliation/repricing was not observed. The exact expiry cutoff is still unknown. |
| Same maintenance interval | Org 3's four queued accepts were summarized for crew 1 and 17; org 7's four accepts for crew 18. Crew 2, whose lead flag had been cleared, received none despite `prefs.digest` still being Y. | Digest delivery depends on crew state as well as queued scheduling events. Lead eligibility and preference precedence need isolated follow-up probes. |
| `confirm-after-expiry`, `accept-after-expiry`, `confirm-repeat`; `after-maintenance` → `after-expired-confirm` → `after-repeat-confirm` | Expired and repeated accept/confirm attempts return `not open`. All six tables remain identical across these snapshots. | In these failures, confirmation did not mark the original message read or append a notification. |
| `crew-list-post`, `crew-show-trailing-slash` | Wrong method and trailing-slash routes return HTTP 200 JSON containing 405/404 error strings. | Framework-default HTTP 405/404 or redirect behavior would differ. Route matching is part of wrapper fidelity. |
| [Frozen crew contract](tests/characterization/README.md), captured before implementing Encore endpoints | 171 exact request/response cases using 32 reverse-inserted fixture crew plus a second org; behavioral tests cover committed-change visibility and all 13 recorded crew reads. | Wave 1 now has an executable legacy reference for serialization, pagination, tenant scope, malformed inputs, methods, and route shape. The same reference can later test Encore wrappers. |
| [Detailed crew nuances](investigation/LEGACY_CREW_BEHAVIOR.md) and 828 frozen fuzz cases | Encoded paths resolve to working routes; double slashes redirect with HTTP 308 HTML. Pagination accepts Unicode digits; PostgreSQL IDs additionally accept hex/octal/binary/underscore forms. Duplicate org headers fail. Every fuzz response matched its repeat observation. | Exact compatibility requires matching parsing and HTTP-stack behavior, not just the successful JSON shape. The complete suite now contains 1,001 tests, with the original 171 responses preserved. |
| [Gateway boundary checks](investigation/evidence/gateway-boundary.jsonl): six direct/gateway HTTP requests | Direct crew HEAD/OPTIONS return 200; gateway HEAD/OPTIONS return 405. A double-slash detail path returns 308 at both boundaries, but its Location/HTML uses `localhost:8091` directly and `callboard:8080` through the gateway. | Direct-backend parity and frontend-ingress parity need separate baselines. Do not change existing gateway method or redirect behavior as an incidental migration cleanup. |

## Recorded traffic replay follow-up (2026-10-24, approximately 11:39 America/Chicago)

Raw requests, response headers, HTTP statuses, and bodies are saved in
[`investigation/evidence/recorded-replay-2026-10-24.json`](investigation/evidence/recorded-replay-2026-10-24.json).
Indices below are zero-based positions in `traffic/traffic.jsonl`.

All **51 recorded requests**, covering **13 distinct method/path pairs**, were
called once through `http://localhost:8080`: 32 GETs first, then 19 POSTs after
explicit approval. This was not the original interleaved recording order. All
recorded responses returned HTTP 200 and `X-Served-By: callboard`. Gateway and
Encore health checks also returned HTTP 200; the evidence contains two rounds
of those checks (55 responses total).

| Probe | Observed response | Finding |
| --- | --- | --- |
| Index 50: org 19, `GET /callboard/crew/show?crew_id=1` | HTTP 200, `{"error":"not found","result":"fail"}` | A cross-org lookup fails at the application level. This agrees with the earlier ownership probes. |
| Index 29: org 7, `POST /callboard/assignment/accept`, `assignment_id=83` | HTTP 200, `{"error":"not open","result":"fail"}` | Acceptance is state-dependent. Earlier investigation already accepted assignment 83; this replay does not establish what a pristine seed would return. |
| Index 48: org 7, `POST /callboard/shift/cancel`, `shift_id=30` | HTTP 200, `{"error":"already cancelled","result":"fail"}` | Earlier investigation cancelled shift 30. A repeated cancellation reports an application failure rather than idempotent success. |
| Other 17 POSTs across orgs 3, 7, and 12 | HTTP 200 with `result: ok` | Crew update, shift creation, assignment offer/accept, message confirm, and message send reported success. Shift creation returned IDs 62–64, offers returned assignment IDs 182–184, and manual notes returned message IDs 133, 136, and 139. |
| Index 14: org 3, `POST /callboard/message/confirm`, `message_id=16` | Success body describes assignment 24 with status `A` | Confirms the observable messaging-to-assignment seam. A message endpoint returns an assignment representation; response shape and state transition belong in parity coverage. |
| Indices 8, 24, 40: `GET /callboard/shift/roster_rows` | HTML response bodies | Replay tooling must preserve raw bodies and content types instead of assuming every successful response is JSON. |

**Migration implications.** HTTP status alone cannot determine business success:
three recorded requests returned `result: fail` despite HTTP 200 (one GET and two
POSTs). Legacy wrappers must preserve these bodies and status codes. Parity tests
must compare payloads and start both backends from equivalent database state;
replaying writes successively against a shared database can produce expected
state-dependent differences. The successful writes also mean the database is no
longer at its pre-replay state.

**Evidence limits.** No before/after database snapshots accompanied this replay,
so successful response bodies are evidence of reported outcomes, not independent
verification of every persisted effect or transaction boundary. GETs preceded all
writes, so their captured bodies do not verify post-write visibility. No routes
were changed and no requests were served by Encore; this run characterizes the
legacy backend and does not prove migration parity or exhaustive API coverage
beyond the supplied recording.

## Couplings found

- **Crew → scheduling:** acceptance reads crew rate and chooses a lead. Live initial
  probes establish synchronous pay calculation and lead fallback. Changing crew
  rate did not reprice existing accepted work during the observed tick. Crew state
  also affects who receives acceptance digests.
- **Scheduling ↔ messaging:** offer creates CALLOUT; confirmation accepts an
  assignment; cancellation sends CXL. Names and titles are duplicated in storage.
- **Scheduling → queue → background behavior:** acceptance writes ACCEPT queue
  events. The first tick expired old offers, drained queued events, and emitted
  per-org DIGEST messages. It did not change staffing/lead/pay in this observation.
- **Venues → shifts:** shift creation copies venue name/timezone and interprets
  entered local times using the venue timezone in the observed New York example.
- **Shared storage:** the schema declares no foreign keys for these relationships.
  Writers must enforce tenant ownership and invariants in application transactions.

## Proposed waves

| Wave | What moves | Why this boundary |
| --- | --- | --- |
| 1 | Only `GET /callboard/crew/list` and `GET /callboard/crew/show`, plus modern crew list/detail under `/v3`. Initially org 7 only. | Two read endpoints can use the existing `tg_crew` table without taking ownership of writes, queue drain, or maintenance. Both remained side-effect-free in the observed read replay. |
| 2 | Crew writes, shift operations, assignment offer/accept, message confirmation, cancellation, roster projection, and their background invariants as a coordinated scheduling slice. | These share transactional and deferred effects. Subdivide only after defining a single owner for each write and background behavior. |
| 3 | Remaining manual messaging, delivery/read preferences, and retirement of residual legacy paths/jobs/storage. | Move after the scheduling message producers and consumers have explicit contracts. This wave requires more discovery, including unrecorded operations. |

The later waves are ownership proposals, not claims that their implementation fits
this assessment. The first wave deliberately stays small.

## Wave 1 plan after characterization and fuzzing

**Scope stays at two reads for org 7.** The new evidence increases the compatibility
work, not the number of endpoints to migrate. Crew update, all scheduling/message
writes, and the maintenance job remain legacy-owned. The reads share existing
committed `tg_crew` data; no table copy, schema migration, write ownership transfer,
or second background worker is required for this wave.

What changes in implementation and acceptance:

1. **Build an explicit legacy adapter.** Shared crew retrieval serves both the
   modern API and wrappers; request parsing and response serialization belong in
   their respective adapters. Do not use v3 validation/serialization as the legacy
   wire contract. Ordinary FastAPI defaults for 404/405/422, slash handling, nulls,
   and decimal values would drift from captured behavior. Preserve HTTP-200 JSON
   errors, raw preferences, empty-string distinctions, lead normalization, JSON
   formatting, HEAD/OPTIONS behavior, and the observed 308 HTML redirects.
2. **Keep the observed numeric parsers distinct.** Pagination accepts Python-style
   integer forms and slicing edge cases. Detail IDs accept Postgres 16 integer
   forms, including `910_001`, `0xde2b1`, octal and binary; Unicode decimal digits
   accepted for pagination fail for IDs. Retain raw legacy ID input through the
   compatible database conversion/error path rather than pre-validating every ID
   as a Python integer. Header validation, duplicate values, and error precedence
   are also observable contracts. These are requirements inferred from the frozen
   cases, not proposed improvements to legacy behavior.
3. **Treat the corpus as the reference.** The 171 original cases and 828 fuzz cases
   were captured from Callboard before wrapper implementation. All 1,001 tests
   passed in the standalone legacy run; the original baseline's SHA-256 stayed
   unchanged. Replay against Encore without rewriting awkward expected results.
   Fresh equivalent fixture data is required when comparing backends; a successful
   legacy-only verification run is not an Encore acceptance result.
4. **Test the real gateway boundary separately.** The new six-request baseline
   proves that direct HEAD/OPTIONS behavior is not the frontend's current behavior.
   The proxy also replaces Host with its upstream destination, changing absolute
   redirect Location/HTML. Compare the same frontend requests before/after cutover
   at the gateway; preserve its existing status/body contract and account explicitly
   for trace IDs and the intended `X-Served-By` change. The direct fuzz suite pins
   Host to its capture value and cannot alone establish this ingress parity.
5. **Prove the actual partial-routing configuration.** Use only the two read-path
   prefixes for org 7, retaining the legacy default. Prefix matches also capture
   suffixes; encoded paths, header variants, and unsupported methods need checks.
   Source inspection shows org matching is exact string comparison, whereas legacy
   org parsing accepts some padded/leading-zero values; those variants can remain
   on legacy under the supplied table. Do not normalize them as an unreviewed
   routing change. The earlier `tests/routes.yaml` sent the whole crew prefix
   and every org to Encore, which did not prove that crew/update or other orgs
   stayed legacy. Slice D replaces it with the actual two-prefix/org-7 fixture
   and explicit mixed-routing assertions.

Exit conditions before declaring wave 1 complete:

- The frozen corpus passes against Encore directly with equivalent fixture state;
  modern `/v3` reads share the retrieval logic and have their documented contract.
- Gateway comparisons pass against the actual org-7/read-only route configuration,
  including malformed requests, method handling, path variants, redirects, and
  tenant boundaries. Confirm both migrated reads are served by Encore and that
  crew/update, other functional areas, and non-migrated orgs remain legacy-served.
- A legacy write is visible through the next Encore read without a cache refresh;
  reads cause no changes in the compared DB state. Existing fixture checks cover
  all crew globally and the other five tables for fixture orgs, not arbitrary
  unrelated seeded scheduling writes during background maintenance.
- A route-file-only rollback returns org 7's two reads to Callboard without deploy
  or reverse data migration, and the relevant verification gate remains green.
- Record remaining limits and intentional `/v3` differences in the submission
  writeups. Later-wave expiry/digest/concurrency questions do not need to be solved
  to move these reads, but remain blockers for transferring those write/job owners.

## Wave 1 implementation progress: slices A through C

The [design's implementation sequence](templates/WAVE1_DESIGN.md#6-implementation-slices-and-verification)
has reached **C: legacy read wrappers**. Reference preservation (A) was
rechecked before code changes: the full legacy gate passed 1,028 tests, and both
frozen corpus hashes plus the fixture hash were recorded in
[`wave1-reference-manifest.jsonl`](investigation/evidence/wave1-reference-manifest.jsonl).
Those hashes remain unchanged after implementation.

Encore now provides `GET /v3/crew` and `GET /v3/crew/{crew_id}` through one shared
repository/service. Queries select only approved crew columns, bind tenant scope
in the database predicate, and close a fresh session after each retrieval. List
pagination and totals use the same ordered query result. The modern adapter
preserves nulls/raw preferences and formats money as decimal strings; its strict
validation and boolean lead field follow the intentional modern contract in
[the endpoint documentation](api-endpoints.md) and OpenAPI.

The implementer and independent reviewer each ran the complete isolated
`python3 scripts/verify --backend legacy` gate: **1,060 pytest tests passed** in
each run. Modern HTTP tests target Encore directly regardless of the compatibility
backend selector. Coverage includes tenant isolation, invalid/duplicate inputs,
nulls, raw invalid preferences, ordering, read-side DB checks, and visibility of
a committed table update on the next read. The reviewer also checked the code
against the design, assessment README, and this seam map, and exercised padded
IDs/orgs, malformed queries/headers, very large pages, and common not-found
responses against an isolated live stack. Final reports are local under
`test-results/showcall-verify-197d1c04f25d/` (implementation) and
`test-results/showcall-verify-d7d93063d69f/` (independent review); the manifest
retains their identities and reference checksums.

Slice B is committed as `69438b9`. Slice C adds the original
`/callboard/crew/list` and `/callboard/crew/show` wrappers over the same retrieval
service. The compatibility dispatcher preserves raw query/header handling,
first-value semantics, org/error precedence, legacy pagination, JSON bytes,
HEAD/OPTIONS behavior, and direct 308 redirects. Detail IDs remain bound text
cast by PostgreSQL inside a tenant-scoped query. Failed conversions roll back
and close the session; unrelated operational failures are not fabricated as
invalid-ID responses. The async middleware dispatches synchronous DB work to a
thread pool.

The implementer's final `python3 scripts/verify --backend both` run passed
**1,071 pytest tests per backend**, including the unchanged original/fuzz corpus
and modern regressions. Its isolated reports are
`test-results/showcall-verify-dd5a1d88e95a/` (legacy) and
`test-results/showcall-verify-fd47fbf799df/` (Encore). The test runner now names
`tests/` explicitly: otherwise the backend value `encore` can be mistaken for
the existing source directory during early pytest plugin discovery. New public
Callboard probes also established additional org-header and HTML-escaping quirks;
their source evidence and focused regression coverage are described in the
[behavior notes](investigation/LEGACY_CREW_BEHAVIOR.md#slice-c-follow-up-observations-2026-10-24).
The frozen corpus and fixture hashes remain unchanged.

Independent Slice C review **passed** against the design, assessment README,
this seam map, and the behavior evidence. The reviewer repeated the full
`--backend both` gate with **1,071 passing tests per backend** in
`test-results/showcall-verify-800089ad574d/` (legacy) and
`test-results/showcall-verify-a8cea30df596/` (Encore), with no failures, errors,
or skips. Direct live comparisons also matched the four new source observations
and a successful detail response byte-for-byte with identical Host input. All
isolated verification stacks were cleaned up. JUnit's suite counter includes
13 unittest subtests in addition to the 1,071 testcase elements; the manifest
records both counts. These results establish bounded direct-wrapper parity,
not ingress or customer-cutover acceptance.

Slice D's prepared implementation passed independent isolated gates:
`showcall-verify-c4a13cf8347d` (legacy, 1,076 pytest tests),
`showcall-verify-f61f993f62e1` (Encore, 1,076), and
`showcall-verify-79d7851d1749` (gateway, 73), with no failures/errors/skips.
Subsequent parallel D1 work expanded gateway coverage and independently passed
81 tests in `showcall-verify-ee1b1f804be9`; I1 must run the combined final tree.
The original 14-case gateway source observations are retained in
[`slice-d-original-gateway-20261024.jsonl`](investigation/evidence/slice-d-original-gateway-20261024.jsonl).
The shared-stack live rehearsal attempted by this chat did not execute: automatic
approval review rejected the command before startup, citing a development-write
risk. No live rehearsal artifact was created and this chat left routing legacy.
The newly assigned [I1 integration task](tasks/I1-integration-rehearsal.md) owns
subsequent combined verification and shared-stack changes; prepared test results
are not a claim that live cutover or rollback has happened.

**Wave 1 migration is still incomplete.** Slice D
must demonstrate actual mixed routing, legacy HTTP-write visibility, ingress
parity, and config-only rollback. Slice E must complete the acceptance matrix
and submission evidence. No production route, table schema, or legacy write/job
ownership changed in slice B.

## Cut couplings and mixed-routing mitigation

- In wave 1, legacy remains the writer of `tg_crew` and owner of every background
  job. Encore reads committed rows directly without caches. A legacy update must
  immediately be visible through Encore's next read. Check this in mixed-routing
  acceptance tests and compare all-table snapshots around read requests.
- Configure **individual endpoint prefixes** for org 7 rather than
  `/callboard/crew/`, which would accidentally send `crew/update` to Encore.
  The supplied gateway uses prefix matching, not HTTP method matching; confirm
  methods and suffixes before making the routing edit.
- Wave 1 rollback is only a route-file edit. Both backends use the same table,
  so no reverse copy or reconciliation is needed for the read-only cutover.
- Migrating rate/lead writes while acceptance and digest processing remain legacy
  must preserve shared fields and semantics: rates affect future acceptances, and
  crew state affects digest recipients. Existing pay stayed unchanged in this
  observed update/tick. Do not add repricing as an undocumented migration feature.
- Splitting message confirmation from assignment acceptance risks marking a message
  read without staffing the shift, or staffing it twice. Give both entry points one
  acceptance transaction; don't independently reimplement the transition.
- Moving acceptance while legacy maintenance still processes all orgs requires
  compatible queue events and exactly one background owner. Routing changes HTTP
  only; they do not disable the legacy job for org 7. Double maintenance can repeat
  notifications or race offer expiry. An eventual handoff needs an explicit
  per-org job ownership mechanism, not just `routes.yaml`.
- Cancellation and other writers need serialization around a shift and its
  assignments. Separate autocommitted writes would expose half-updated staffing
  or messages; contention and replay behavior remain to be characterized.

## Open questions before customer cutover

- Determine the exact expiry cutoff, digest eligibility/preference precedence,
  and crash/retry semantics. One tick establishes effects, not reliable delivery.
- Crew defaults, nullable fields, repeated query keys, malformed/large values,
  and permitted methods are covered by the frozen characterization suite.
  Concurrent modification between list count and page retrieval remains untested.
- Establish date boundaries, daylight-saving ambiguity/nonexistent times, and
  HTML escaping rules before migrating scheduling.
- Probe duplicate offers, overbooking, concurrent confirm/accept/cancel, and
  error-path transaction rollback. These have not been validated.
- Determine actual authentication/authorization and how org identity is trusted
  in production; the assessment supplies only `X-Org-Id`.
- The recording and schema are finite evidence, not a full production contract.
