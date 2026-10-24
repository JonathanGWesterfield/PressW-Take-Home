# Legacy investigation

The stack first ran successfully at approximately 11:14 America/Chicago on
2026-10-24. An earlier attempt failed to mount files from Downloads in Colima.
Assessment timer start is controlled by the candidate, not this timestamp.

## Evidence

- `evidence/http.jsonl`: labeled requests and exact HTTP status, headers, and
  response body strings. Contains synthetic assessment data only.
- `evidence/db-timeline.json`: complete first snapshot plus all successive field
  changes, added rows, and deleted rows. Empty `changes` means every captured
  table was identical. Raw per-step snapshots remain local and ignored to avoid
  repeating the same baseline in Git. Password hashes are excluded.
- [`../SEAMS.md`](../SEAMS.md): conclusions, probe labels, proposed migration
  waves, intermediate-state risks, and open questions.
- [`LEGACY_CREW_BEHAVIOR.md`](LEGACY_CREW_BEHAVIOR.md): separate wave 1 compatibility
  notes with successful, failing, and unusual behavior linked to individual tests.
- [`crew-fuzz-report.json`](crew-fuzz-report.json): reproducible fuzz seed, counts,
  and outcomes; [`evidence/crew-fuzz-http.jsonl`](evidence/crew-fuzz-http.jsonl)
  retains timings and raw response headers. Exact requests and full response
  bodies are frozen in `tests/characterization/crew_fuzz_contract.json`.

Only public legacy HTTP and the allowed Postgres database were probed. The legacy
image/container contents were not accessed. The gateway and Encore health checks
returned `{"ok":true}`; all four Compose services were running.

## Reproduce a capture

From the repository root, with the stack running:

```sh
docker compose up --build -d
python3 investigation/probe.py --snapshot run2-before --recorded-reads
python3 investigation/probe.py --snapshot run2-after
python3 investigation/summarize.py
```

Python uses only its standard library; there are no local package dependencies.
Snapshot labels must be unique. HTTP evidence appends. The two snapshot labels
in this example intentionally differ from the initial investigation's labels.
The second invocation's field diff can include maintenance if a tick occurs
between snapshots; a read-only replay alone must not be blamed for that change.

For a custom request, import `probe` from `investigation.probe`. Each HTTP record
contains enough information to repeat its query/form against the running system.
The supplied traffic replay also works, but replaying all traffic includes writes.

Replay the complete frozen crew characterization/fuzz corpus with:

```sh
python3 tests/characterization/test_crew_contract.py
```

The 828 fuzz cases include 600 generated combinations from seed `20261024` and
targeted boundary/decoding/routing cases. All were observed twice during capture.
The discovery generator is `investigation/fuzz_crew.py`; it refuses to overwrite
evidence, while `--extend` accepts only appended cases and unchanged old results.
`crew_support.py` owns the reusable HTTP transport, database adapter, and fixture
lifecycle. Discovery imports it directly, so it does not depend on the test harness;
the characterization suite reuses it when testing either backend.

## State left by this investigation

The database is intentionally **not pristine**. HTTP probes changed org 7 crew 10's
notes, crew 2's rate to 32.17 and lead flag to N, created shift 61 and assignment
181, accepted assignments 62/65/83/181, sent a NOTE, and cancelled shift 30.
Maintenance expired 82 offers and drained the queue into three DIGEST messages.
Full details and exact IDs are recorded in the timeline. No route was changed.

Restore to a pristine database only when deliberately starting a fresh experiment;
the supplied `docker compose down -v` reset is destructive. Don't run it while
another experiment needs this state.

## Limits

One five-minute tick was observed. Expiry affected the remaining 30-day-old offers,
while the approximately 45-minute-old offers remained open; the exact cutoff was
not determined. No concurrency, retry-after-crash, external delivery, or production
authentication guarantees were established. Later migration waves need additional
investigation. Current captures characterize Callboard; they do not prove parity
for an Encore implementation, which has not been written yet.
