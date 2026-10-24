# Scoping

Snapshot: 2026-10-24, HEAD `5f169dd` plus the existing uncommitted modern crew
implementation. This is a record of the current submission, not a claim that
wave 1 is complete.

- **Scope committed:** migrate only crew list/detail reads, initially for org 7:
  `GET /callboard/crew/list`, `GET /callboard/crew/show`, `GET /v3/crew`, and
  `GET /v3/crew/{crew_id}`. Keep one tenant-scoped retrieval service over existing
  `tg_crew`, with separate modern and compatibility adapters. Committed work is
  discovery, the [seam evidence](SEAMS.md), frozen legacy characterization,
  isolated verification infrastructure, and the [implementation design](WAVE1_DESIGN.md).
  The working tree now contains the repository/service, v3 routes, and tests;
  legacy wrappers and the org-7 route flip are still outstanding.
- **Scope cut:** no crew writes, scheduling/message writes, new schema, data copy,
  cache, or Encore maintenance worker. Acceptance, confirmation, cancellation,
  queue draining, and digest generation cross table and endpoint boundaries;
  moving one independently would risk inconsistent staffing or duplicate messages.
  I chose two reads to avoid transferring those ownership problems in wave 1.
  Search, cursor pagination, preferences repair, production authentication, and a
  general migration framework are deferred.
- **Assumptions made:** the supplied `X-Org-Id` represents trusted tenant context;
  production identity validation remains separate work. Both services can read
  the same committed Postgres rows while Callboard remains the sole writer/job
  owner. A tenant's crew fits in memory, so one ordered query supplies both page
  and total consistently within a request. The captured corpus is a bounded
  reference, not an exhaustive specification. No assumptions about expiry cutoff,
  digest preference precedence, or crash delivery guarantees are treated as facts.
- **Risks accepted:** the shared DB remains a shared failure domain, and an HTTP
  routing rollback cannot repair it. Compatibility includes parser errors, HTTP
  methods, encoded paths, redirects, and JSON bytes; ordinary FastAPI behavior
  cannot stand in for the wrapper. The current gateway compares org strings
  exactly and matches path prefixes, so `07` may stay legacy while `7` migrates,
  and suffixes of migrated prefixes must also behave compatibly. I accept the
  small read-side memory cost; I have not accepted customer cutover without
  direct parity, gateway/mixed-state checks, legacy-write visibility, and an
  observed config-only rollback. [Trade-offs](TRADEOFFS.md) records current gaps.
