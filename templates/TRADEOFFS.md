# Trade-offs

- **Built vs. scoped:** Wave 1 now has shared tenant-scoped retrieval, modern
  crew reads (`69438b9`), legacy-compatible list/show wrappers and verification
  support (`4ff8a3c`), gateway acceptance (`b1716ae`), a directory-mounted route publication
  runbook (`3c39025`), and three named CI gates (`c46b810`). The unchanged
  characterization corpus passes locally against both backends. The gateway
  suite checks its distinct ingress behavior, mixed routing, legacy HTTP-write
  visibility, read-side database invariants, and config-only rollback in an
  isolated stack. I1 also demonstrated actual org-7 cutover, rollback and final
  Encore reapply with the same gateway instance, after correcting a failed
  publication attempt. R1 independently accepts the bounded local Wave 1
  result; remote CI execution and required-check enforcement remain unverified.
- **Specific trade-offs and why:** two reads over shared `tg_crew` avoid a
  second writer, replication and job handoff. One ordered query plus in-memory
  pagination keeps page/total aligned at fixture scale with O(tenant crew count)
  memory. Both adapters call the shared service directly. Legacy preserves
  pagination quirks, error precedence and exact captured wire output; bound raw
  IDs retain PostgreSQL conversion behavior without SQL interpolation. Modern
  v3 deliberately uses positive ASCII-decimal IDs, page sizes 1–100, 422
  validation, common missing/foreign 404s, nullable two-decimal money strings,
  boolean lead flags and nullable raw preferences (some stored text is invalid
  JSON). It rejects duplicate/unknown parameters and duplicate tenant headers.
  No new authentication or preferences cleanup is implied. AI-assisted discovery,
  implementation and review were used, as permitted by the brief.
- **What you'd do next with more time:** retain the I1 rollout/recovery evidence
  and corrected deployment publisher, then run the three checks on GitHub and
  configure required PR checks for `main`:
  **Direct legacy and modern**, **Direct Encore and modern**, and **Gateway
  ingress and mixed routing**. Workflow YAML alone does not enforce them.
  Later waves need acceptance/confirmation/cancellation transaction ownership,
  concurrent-write probes, expiry policy, digest recipient rules and worker
  handoff; these are outside the two-read migration.
- **Known issues or unhandled cases:** no exhaustive equivalence claim is made
  for malformed HTTP, concurrent mutations or unobserved legacy behavior.
  Gateway HEAD/OPTIONS remain 405 even where direct legacy permits them;
  redirects and duplicate-header forwarding retain observed ingress behavior.
  Atomic route publication needs the containing-directory bind mount and
  verified host-to-container visibility. I1's first host-side rename exposed a
  transient missing route file in Colima and caused 28 HTTP 500s before recovery.
  The corrected publisher validates and atomically replaces the file from a
  temporary Linux-view container; the gateway mount remains read-only. The
  repeated rehearsal sampled 58 successful requests across cutover, rollback,
  write/restore and final Encore reapply. This is evidence for the corrected
  procedure, not a zero-disruption claim for the failed attempt or every future
  filesystem/interleaving. No last-known-good YAML fallback exists.
  Maintenance stays on Callboard; observations do not prove job transaction
  order, crash/retry safety or external message delivery. Local evidence below
  supersedes old collection/header-construction failures in earlier artifacts;
  remote Actions execution and branch enforcement remain unverified.
- **Post-window commits, if any:** the kit delivery time is not recorded in the
  repo. The approximately 11:14 America/Chicago stack start was an investigation
  timestamp, not the assessment start. Git timestamps cannot establish which
  commits were within the four-hour window. The candidate must supply that
  delivery time and label post-window work before submission; this writeup does
  not infer either compliance or an overrun. Wrapper/support code is committed
  as `4ff8a3c`; I1 rehearsal evidence and the final route configuration are
  committed as `05bd1c0`. This documentation records those verified local results.

## Verification evidence

These are saved I1 local runs of the combined tree, inspected for this writeup;
E2 did not start containers or rerun the stack. Reports are ignored local
artifacts, not remote CI results. Each directory contains `run.txt`,
`exit-code.txt`, `junit.xml` and timestamped `compose.log`. I1 ran
`python3 scripts/verify --backend both` for the first two stages below; the
individual commands reproduce the same target gates.

| Full command | Saved report under `test-results/` | Result |
| --- | --- | --- |
| `python3 scripts/verify --backend legacy` | `showcall-verify-814fd83dd4ff/` | Exit 0; 1,084 pytest test cases; no failures/errors/skips |
| `python3 scripts/verify --backend encore` | `showcall-verify-a4e3b870b5e4/` | Exit 0; same 1,084 test cases; no failures/errors/skips |
| `python3 scripts/verify --backend gateway` | `showcall-verify-66349a73c416/` | Exit 0; 81 test cases; no failures/errors/skips |

The direct JUnit suites report `tests=1097`, but each contains 1,084
`testcase` elements: unittest subtest counters add 13. These are not 13
additional pytest methods. The gateway report has 81 entries and counter 81.
Direct targets run the frozen corpus, properties, units, modern and ingress
checks; gateway mode selects its ingress/mixed suite plus units, smoke and
modern checks. Frozen response files are not changed to accommodate Encore.
See [test instructions](../tests/README.md), [I1](../tasks/I1-integration-rehearsal.md)
for live artifacts and final state, and [R1](../tasks/R1-independent-review.md)
for the independent local acceptance verdict. E2's document review is not R1
approval.

The compact [I1 evidence](../investigation/evidence/i1-integration-20261024.jsonl)
records the failed publication, correction, full gate identities, live routing
phases and final config hash. Raw local evidence is in `test-results/i1-live-final/`:
`summary.json`, `publication.jsonl`, `continuous-ingress.json`, phase responses,
gateway identities and DB comparisons. Crew rows and schema matched before/after;
a temporary legacy notes update was visible through wrapper/v3 list/detail and
was restored exactly. Captured noncrew tables were unchanged in this rehearsal;
that does not mean maintenance is disabled. Only the gateway was recreated for
preparation, before the baseline; its instance/container stayed unchanged during
cutover, rollback and reapply. The active route table selects Encore only for
canonical org `7` on the two read prefixes; all writes/jobs stay legacy. Use the
corrected `publish_d2_routes` procedure in [D2](../tasks/D2-rollout-configuration.md)
to publish `tests/routes/legacy.yaml` for rollback, without restart. Modern
clients remain direct Encore. R1 accepted the bounded local result; remote
enforcement remains pending.
