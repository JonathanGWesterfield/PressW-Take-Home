# Scoping

Evidence snapshot: 2026-10-24, through I1 commit `05bd1c0`. Direct/gateway
verification, actual cutover/rollback evidence, and the final org-7 route
configuration are saved and committed. R1 independently accepts the bounded
local Wave 1 result; remote CI execution and required-check enforcement remain
unverified release gates.
See [current evidence](TRADEOFFS.md) and [I1](../tasks/I1-integration-rehearsal.md).

- **Scope committed:** two read operations, initially for org 7:
  `GET /callboard/crew/list` and `GET /callboard/crew/show`, plus modern
  `GET /v3/crew` and `GET /v3/crew/{crew_id}`. One tenant-scoped retrieval
  service reads existing `tg_crew`; separate adapters own legacy wire behavior
  and the intentional modern contract. Shared reads/v3 (`69438b9`), rollout
  preparation (`3c39025`), CI gates (`c46b810`), and gateway acceptance
  (`b1716ae`) are committed. The wrapper/verification support is committed as
  `4ff8a3c` and passes the unchanged direct corpus. I1 (`05bd1c0`) demonstrated both reads
  moving to Encore, rolling back to Callboard and returning to Encore on the
  same gateway instance. The active configuration leaves canonical org 7
  on Encore for those two prefixes; R1 independently accepts this bounded local
  result, while remote release enforcement remains outstanding.
- **Scope cut:** no crew or scheduling/message writes, schema changes, data
  copy, cache, or Encore maintenance worker. Acceptance, confirmation,
  cancellation, queue draining, and digests share state across tables and
  endpoints; moving one independently risks staffing errors or duplicate/lost
  messages. Callboard keeps all writes/jobs, including the five-minute
  maintenance job. Search, cursor pagination, preferences repair, production
  authentication, and a general migration framework are deferred.
- **Assumptions made:** supplied `X-Org-Id` is trusted tenant context, not an
  authentication mechanism. Both backends read the same committed Postgres
  data while Callboard remains the sole writer/job owner. A tenant's crew fits
  in memory: one ordered query provides request-local list/page consistency.
  The frozen corpus and probes are bounded evidence, not complete equivalence.
  Unknown expiry cutoffs, recipient edge cases and retry guarantees remain
  unknown; they are not dependencies being transferred in this wave.
- **Risks accepted:** the database remains a shared failure domain; route
  rollback cannot repair it. Compatibility retains odd parsing, HTTP-200
  failures and database error text only in the legacy adapter. Gateway prefix
  selection and exact org strings remain unchanged: `07` can stay legacy while
  `7` migrates, and suffixes of the two prefixes also reach the wrapper.
  Modern clients use Encore directly on port 8092; the rollout adds no gateway
  `/v3` route. Moving only reads avoids a reverse data migration, but release
  still requires remote CI execution and required-check enforcement. The first live route
  publisher caused errors on the Mac/Colima share; a corrected Linux-view
  publisher passed sampled cutover/rollback checks. Remote CI execution/branch
  protection and the interview delivery
  time are not established by local tests.
