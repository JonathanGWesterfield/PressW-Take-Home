# Scoping

We chose the first wave from observed coupling, rather than endpoint names.
Acceptance, confirmation, cancellation and maintenance share scheduling/message
state; crew list/show only read existing crew data in our probes. We froze their
wire behavior before implementing Encore, then used the same tests against both
backends. Two reads gave us a complete migration and rollback boundary without
transferring a writer or background job. [The seam map](SEAMS.md) gives the
observations behind that decision.

- **Scope committed:** two read operations, initially for org 7:
  `GET /callboard/crew/list` and `GET /callboard/crew/show`, plus modern
  `GET /v3/crew` and `GET /v3/crew/{crew_id}`. One tenant-scoped retrieval
  service reads existing `tg_crew`; separate adapters own legacy wire behavior
  and the intentional modern contract. The unchanged direct corpus passes
  against both backends. I1 (`05bd1c0`) demonstrated both reads
  moving to Encore, rolling back to Callboard and returning to Encore on the
  same gateway instance. The active configuration leaves canonical org 7
  on Encore for those two prefixes; R1 independently accepts this bounded local
  result. [GitHub run 40125062976](https://github.com/JonathanGWesterfield/PressW-Take-Home/actions/runs/40125062976)
  passed all three automatic checks and evidence uploads at `31758ea`. Later
  documentation/IDE commits are outside that run; exercised code is unchanged.
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
  `/v3` route. Moving only reads avoids a reverse data migration. The first live route
  publisher caused errors on the Mac/Colima share; a corrected Linux-view
  publisher passed sampled cutover/rollback checks. Use the tested
  [Linux-view publisher](../tasks/D2-rollout-configuration.md) on this deployment.

Before submission, make the repo private, grant the invite contacts access,
record actual kit-delivery timing and label post-window work, and publish/verify
the final revision. The planned required-check/PR gate is not enabled: GitHub
reported `main` unprotected. These are separate from the observed CI success;
[trade-offs and evidence](TRADEOFFS.md) distinguish what was demonstrated from
what remains.
