# Trade-offs

- **Built vs. scoped:** two legacy crew reads for org 7 and two modern v3 reads
  share one tenant-scoped retrieval service. Callboard keeps every write and
  maintenance job; schema/data ownership is unchanged. Direct compatibility,
  ingress, legacy-write visibility and config-only rollback passed locally,
  followed by R1's independent acceptance. Three GitHub jobs/uploads also passed
  for `31758ea`; later documentation/IDE commits are outside that CI run.
- **Specific trade-offs and why:** shared `tg_crew` avoids replication and a second
  writer, while retaining the DB as a common failure domain. One ordered query
  followed by adapter pagination keeps page/total consistent at fixture scale
  and preserves negative legacy slicing, at O(tenant crew count) memory. Bound
  raw IDs let PostgreSQL retain its observed conversion behavior without SQL
  interpolation. Separate adapters preserve legacy wire quirks while v3 uses
  positive ASCII-decimal IDs, page sizes 1–100, 422 validation, common missing/
  foreign 404s, nullable two-decimal money strings and boolean lead flags. Preferences remain
  raw text because some stored values are invalid JSON; I do not silently repair it.
- **What I'd do next with more time:** finish private sharing, timing disclosure
  and final-revision publication/verification; enable required PRs and the three
  named checks. Before moving writers, characterize acceptance/confirmation/
  cancellation transactions, contention, expiry, digest recipients and worker
  handoff. Wave 2 describes coupled behavior to investigate, not a commitment to
  migrate all those endpoints at once.
- **Known issues or unhandled cases:** compatibility evidence is bounded; it does
  not establish exhaustive HTTP parsing, concurrency or crash/retry behavior.
  Gateway HEAD/OPTIONS, duplicate-header forwarding and redirect behavior remain
  intentionally unchanged. There is no last-known-good YAML fallback.
  The initial host-side route rename caused **28 HTTP 500s** on Colima before
  recovery. The corrected Linux-view publisher passed a repeat rehearsal with
  **58 successful samples**, unchanged gateway identity and exact crew-state
  restoration. Use the [tested runbook](../tasks/D2-rollout-configuration.md).
  This preserves the failure rather than claiming universal zero disruption.
- **Post-window commits, if any:** kit delivery time is not recorded. The roughly
  11:14 America/Chicago stack start is an investigation timestamp, not the timer
  start. The candidate must supply actual timing and label post-window work
  before submission; Git timestamps do not establish that classification.

## Why I took this path

I investigated before choosing the wave: offers, acceptance, confirmation,
cancellation and maintenance crossed table boundaries. I then froze **171 original
and 828 fuzz responses before porting**. The same independent expectations run
against legacy and Encore, so a cleaner but incompatible wrapper cannot pass by
changing its own oracle. Parser errors, nulls, pagination and HTTP-200 failures
are preserved, not repaired.

Direct parity alone did not establish frontend parity: the gateway normalizes
some inputs and handles methods differently. I therefore tested ingress against
its own all-legacy baseline, asserted the selected backend, made a real legacy
HTTP update and checked subsequent Encore reads, then rehearsed rollback. Keeping
one writer/job owner made that rollback a routing operation without reverse data
migration. AI-assisted discovery, implementation and independent review were used
as encouraged by the brief.

## Evidence and its limits

| Boundary | Demonstrated result | Evidence |
| --- | --- | --- |
| Direct legacy / Encore | Same frozen expectations; each full target passed 1,084 tests locally. | [I1 reports and provenance](../tasks/I1-integration-rehearsal.md) |
| Gateway / modern | Gateway target passed 81 tests locally, including mixed routing, modern reads, write visibility and rollback. | [Test guide](../tests/README.md) |
| Development cutover | Corrected org-7 cutover → rollback → Encore reapply used the same gateway instance; crew/schema restored. | [Compact I1 evidence](../investigation/evidence/i1-integration-20261024.jsonl) |
| GitHub CI | Three automatic verification/upload jobs succeeded at `31758ea`; three nonexpired artifacts were listed. | [Run 40125062976](https://github.com/JonathanGWesterfield/PressW-Take-Home/actions/runs/40125062976) / [recorded metadata](../investigation/evidence/github-actions-20261024.jsonl) |
| Independent review | R1 accepted bounded local Wave 1; no implementation blocker remained. | [Verdict and correction loop](../tasks/R1-independent-review.md) |

Local direct JUnit suite counters are 1,097 because 13 unittest subtest increments
are included; there are 1,084 testcase elements. Remote artifact metadata and
upload success were checked without downloading/recounting ZIP contents.
Application/test/workflow bytes match the CI revision; later commits are not
represented by its SHA. [Detailed verification notes](../investigation/WAVE1_VERIFICATION.md)
retain report identities, commands and deployment evidence.

GitHub reported the repo public and `main` unprotected. Private reviewer access,
required-check/PR enforcement, timing disclosure and verification of the final
published revision remain. A green push run does not prove PR enforcement or
reproduce the Colima deployment. Shared DB availability, production authentication
and later-wave job/transaction guarantees remain explicit limits.
