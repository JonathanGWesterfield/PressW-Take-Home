# Trade-offs

- **Built vs. scoped:** the Git history shows investigation and a wave proposal
  (`7edec10`), frozen/fuzz characterization (`c0691e3`, `063439c`), an isolated
  runner (`2d7b17c`), identical legacy/Encore verification targets (`fe841dd`),
  and the detailed design (`5f169dd`). The uncommitted working tree adds modern
  crew reads and their repository/service/tests. This establishes a reference
  and part of the port; it does not yet satisfy the brief's legacy wrappers,
  org cutover, or demonstrated rollback. I spent more of the available work on
  discovery and repeatable evidence than on completing the cutover.
- **Specific trade-offs and why:** two reads over shared `tg_crew` avoid a second
  writer, data replication, and a background-job handoff. One ordered query and
  in-memory pagination keep page/total aligned at fixture scale, at O(tenant crew
  count) memory. Separate adapters preserve legacy quirks without making the new
  API inherit HTTP-200 failures, negative slicing, or database diagnostics.
  Modern v3 uses positive ASCII-decimal IDs, bounded page sizes, 422 validation,
  common owned/missing 404s, nullable two-decimal money strings, boolean lead flags,
  and raw nullable preferences because some stored text is invalid JSON.
  The unchanged golden corpus remains the oracle; adding an Encore target does
  not make that target pass. AI-assisted investigation and implementation were
  used, as the brief permits; the evidence and acceptance gates remain explicit.
- **What you'd do next with more time:** finish modern verification, implement the
  legacy adapter against the frozen corpus, then compare independently captured
  gateway expectations using the actual two-prefix/org-7 routing table. Verify a
  legacy HTTP update becomes visible on the next Encore read, check read-side DB
  invariance, and rehearse config-only rollback. Address the route-file mount and
  atomic publication hazard described in [the design](WAVE1_DESIGN.md) before
  cutover. Require passing legacy, Encore, modern, and mixed-ingress CI checks;
  workflow YAML alone does not establish remote branch protection. Only then
  investigate later-wave transactions, concurrency, expiry, and job ownership.
- **Known issues or unhandled cases:** there is no legacy adapter in the current
  source and `proxy/routes.yaml` still routes everything to Callboard. Existing
  `tests/routes.yaml` routes all crew orgs to Encore and is not a safe rollout
  configuration. Direct HEAD/OPTIONS and redirect-host behavior differ at the
  gateway boundary. No current mixed-state or rollback acceptance result exists.
  The recorded reference run `showcall-verify-97b2bcc6fa04` has JUnit reporting
  1,041 tests with zero failures/errors, while its JSONL manifest says 1,028
  passes; those counts need reconciliation before a final evidence summary.
  The later local run `showcall-verify-d9a76c84db3a` reports 1,044 tests and one
  failure: HTTPX rejects a non-ASCII header while constructing a v3 unit-test
  request, before the application handles it. The preceding run
  `showcall-verify-f1b0a15bb479` failed collection on duplicate test module names.
  These are saved local artifacts under ignored `test-results/`, not a fresh
  verification by this writeup. The source/tests may have advanced since those
  runs; no current all-green claim is made. Maintenance and write probes show
  effects, not proven atomicity, retry safety, or a complete production contract.
- **Post-window commits, if any:** the exact delivery/start time is not recorded
  in this repo, so I cannot reliably label commits as inside or outside the
  four-hour window from Git timestamps alone. The investigation's approximately
  11:14 America/Chicago stack-start time explicitly is not the assessment start.
  HEAD is `5f169dd` (13:04 America/Chicago); modern source/tests and these writeups
  are currently uncommitted. Reconcile the actual delivery time and label any
  post-window work before submission; do not infer that no overrun occurred.
