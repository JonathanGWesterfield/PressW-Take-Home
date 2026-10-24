# Callboard maintenance: full replay and database comparison

Observation date: 2026-10-24. All human-readable times below are America/Chicago (CDT, UTC−05:00). Status: final.

## Result

After replaying **all 51 supplied requests covering all 13 recorded method/path pairs**, we captured the database before cleanup, waited without further API writes, and queried it afterward. The visible maintenance transition **removed three ACCEPT queue events and inserted five DIGEST messages**. It changed no existing messages, assignments, crew, venues, or shifts in this interval. In particular, it did not recalculate pay, lead assignments, or open slots, and no additional offers expired.

This is an observed behavioral description of the black box, not recovered source code. The earlier investigation separately observed old-offer expiry; a quiet or already-clean database is not a reason to assume maintenance has stopped.

## Experiment and provenance

The development stack was already running, with a nonpristine database from earlier investigation. No database reset, route change, legacy binary inspection, or direct SQL writes were used for this experiment.

1. An initial full 51-request replay at about 1:04 PM found the recorded acceptance/confirmation IDs already processed, leaving no queue work. With explicit approval, assignments **185, 186, 187** were accepted through the API at 1:06:19–1:06:20 PM. SQL snapshots around each acceptance showed O→A, $154.00 pay, shift open slots 5→4, lead assignment selection, and queue rows **14, 15, 16**. These are **API effects**, not maintenance effects.
2. Following the instruction to replay the entire recording before taking the cleanup baseline, **all 51 requests were replayed again in their supplied order** from **1:07:34 PM to 1:07:46 PM** through the gateway. Every response identifies Callboard as the backend. No endpoints were substituted with only three offer calls.
3. Direct SQL queries captured all six tables before and after every replayed request. A separate authoritative **post-replay / pre-cleanup snapshot** was taken at **1:08:03 PM** (18:08:03.335112 UTC). It contained the three queued acceptance events from the explicitly approved preparation above. The hardcoded accept IDs in the supplied recording did not create those events.
4. No further API writes were sent by this experiment. A background observer queried all six tables approximately every 10 seconds. The maintenance effect first appeared between **1:08:47.777 and 1:08:58.008 PM**; the five new messages carry `sent=1792865337`, or **1:08:57 PM**. That timestamp is a message field, not proof of the precise job start time.
5. A separate direct SQL **after-cleanup snapshot** was taken at **1:09:06 PM** (18:09:06.697499 UTC). The authoritative comparison is this snapshot minus step 3, excluding replay/acceptance effects.
6. A follow-up snapshot was taken at **1:14:11 PM** to check the subsequent window. The follow-up direct SQL snapshot at **1:14:11 PM** is identical to the first after-cleanup snapshot across all six tables. Queue count remains 0, digest count remains 13, and no duplicate digests or further expiry were observed. This spans the next expected five-minute execution window; unchanged data does not independently prove a no-op job executed.

## Supplied request coverage and immediate effects

All 51 responses were HTTP 200, but HTTP success is not business success. There were eight JSON application failures: the foreign-org crew read, three recorded accepts, three recorded confirmations, and the already-cancelled shift. The other 12 POSTs reported success. Three roster reads returned HTML.

| Recorded endpoint | Calls | Immediate DB effect of the final full replay |
| --- | ---: | --- |
| GET `/callboard/crew/list` | 9 | None observed |
| GET `/callboard/crew/show` | 4 | None observed; org 19/crew 1 returned `not found` |
| GET `/callboard/shift/list` | 9 | None observed |
| GET `/callboard/shift/show` | 4 | None observed |
| GET `/callboard/shift/roster_rows` | 3 | None observed; HTML responses |
| GET `/callboard/message/list` | 3 | None observed |
| POST `/callboard/crew/update` | 3 | No field changes: notes already matched the submitted value |
| POST `/callboard/shift/create` | 3 | Added shifts **68–70** |
| POST `/callboard/assignment/offer` | 3 | Added offered assignments **188–190** and CALLOUT messages **151,153,155** |
| POST `/callboard/assignment/accept` | 3 | All `not open`; no changes |
| POST `/callboard/message/confirm` | 3 | All `not open`; no changes |
| POST `/callboard/message/send` | 3 | Added NOTE messages **152,154,156** |
| POST `/callboard/shift/cancel` | 1 | `already cancelled`; no changes |

The replay therefore added three shifts, three assignments, and six messages. None of those additions is attributed to cleanup.

## Literal database verification

Snapshots were obtained with `docker compose exec -T db psql`, using `PGOPTIONS='-c default_transaction_read_only=on'` and `ON_ERROR_STOP=1`. Each snapshot is one SQL statement, so all six tables share a statement-level database snapshot. No HTTP payload was used as a substitute for database verification.

The exact executed SELECT is saved in `maintenance-snapshot.sql`. Its structure is:

```sql
SELECT json_build_object(
  'database_time', statement_timestamp(),
  'tables', json_build_object(
    'tg_crew', (SELECT coalesce(jsonb_agg(to_jsonb(t)-'password'
                      ORDER BY id), '[]'::jsonb) FROM tg_crew t),
    -- Same ordered aggregation for venues, shifts, assignments,
    -- messages, and callboard_queue.
    ...
  )
);
```

The abbreviated SQL above is explanatory; the saved `.sql` file contains the complete executable statement. Password fields are excluded from captures. Comparison maps rows by primary key and checks every captured field, including additions/deletions; this is stronger than comparing row counts alone.

| Table | Before cleanup | After cleanup | Complete-row comparison |
| --- | ---: | ---: | --- |
| `tg_crew` | 32 | 32 | All captured rows/fields identical |
| `venues` | 6 | 6 | All captured rows/fields identical |
| `shifts` | 70 | 70 | All captured rows/fields identical |
| `assignments` | 190 | 190 | All captured rows/fields identical |
| `messages` | 156 | 161 | 5 added |
| `callboard_queue` | 3 | 0 | 3 removed |

## Queue consumption and digest fan-out

The deleted queue rows were:

| Queue ID | Org | Payload assignment | Crew | Shift |
| --- | ---: | ---: | ---: | ---: |
| 14 | 3 | 185 | 13 | 20 |
| 15 | 7 | 186 | 14 | 40 |
| 16 | 12 | 187 | 15 | 50 |

Each had `kind=ACCEPT`. Their JSON payloads contain `assignment_id`, `crew_id`, and `shift_id`. No queue rows remained afterward; no other queue kind was exercised.

The inserted messages were:

| Message ID | Org | Recipient | Exact body |
| --- | ---: | --- | --- |
| 157 | 3 | 1 (M. Kowalski) | `Crew acceptances: O. Fitzgerald for Strike — Meridian Hall` |
| 158 | 3 | 17 (L. Marchetti) | `Crew acceptances: O. Fitzgerald for Strike — Meridian Hall` |
| 159 | 7 | 18 (L. Marchetti) | `Crew acceptances: O. Fitzgerald for Strike — The Beacon Room` |
| 160 | 12 | 3 (M. Kowalski) | `Crew acceptances: O. Fitzgerald for Strike — Ovation Center` |
| 161 | 12 | 19 (L. Marchetti) | `Crew acceptances: O. Fitzgerald for Strike — Ovation Center` |

Every new message has `kind=DIGEST`, `read=N`, `assignment_id=null`, `shift_title=null`, and the same `sent` timestamp. They summarize accepted crew work; they are not messages confirming another acceptance, and no assignment was accepted by this cleanup step.

All five recipients had `is_lead=Y` and `prefs.digest=Y` in the pre-cleanup snapshot. Org 7 crew 2 had `is_lead=N` and `digest=Y` and received none. Crew 17–19 had `sms=N` yet received digests, so SMS permission did not suppress these stored DIGEST messages. Org 19 had leads but no queued event and received no digest. This supports per-org, lead-targeted digest fan-out in the tested state. It does **not** isolate the effect of `digest=N`, missing/invalid preferences, or every possible lead flag.

## What is known about the maintenance behavior

The observed responsibilities are coupled across scheduling, queue events, messaging, and recipient crew state:

- **Earlier expiry evidence:** the 11:19 AM investigation changed 82 old offers from O to E, removed eight queued accepts, and created three digests. Old offers were approximately 30 days old; the exact cutoff was not established. Fresh offers survived that run.
- **Current repeat evidence:** three known ACCEPT events produced five per-recipient digest rows and were removed. Current accepted assignments stayed accepted, their $154.00 pay stayed unchanged, and shifts retained their post-acceptance staffing/lead values.
- **Aggregation:** the earlier eight-event run grouped four events per org into semicolon-separated summaries; this run had one event per participating org. That supports aggregation rather than one message per event. Ordering, truncation, duplicate event handling and source-field selection remain unproven.
- **Expiry in this run:** assignment counts by status were unchanged: A=71, E=82, O=34, X=3. Newly offered assignments 188–190 remained O. There is no basis to claim this cleanup expired every offer or recalculated all staffing.
- **Next-window observation:** The follow-up direct SQL snapshot at **1:14:11 PM** is identical to the first after-cleanup snapshot across all six tables. Queue count remains 0, digest count remains 13, and no duplicate digests or further expiry were observed. This spans the next expected five-minute execution window; unchanged data does not independently prove a no-op job executed.

These effects do not establish internal SQL order, a single transaction boundary for the job, locking behavior, retry/crash recovery, or exactly-once processing. Polling can miss changes that occur and revert between samples. Stored messages do not prove external email/SMS delivery. No claimed job execution is inferred solely from an unchanged snapshot.

## Migration implications

Wave 1 remains two read-only crew endpoints. Legacy retains writes, queue production/consumption and maintenance; Encore reads current committed shared data. The observed job did not change crew rows in either documented busy run, which supports this boundary without proving all possible maintenance behavior.

Later acceptance/confirmation migrations must preserve the ACCEPT event contract or digests can disappear despite matching immediate API responses. Moving a worker without handing off ownership can duplicate/lose effects. HTTP route rollback does not disable legacy maintenance or undo messages/data changes. Establish per-org worker ownership, expiry policy, recipient rules and retry semantics before transferring those writers/jobs.

## Evidence files

The completed observer ran for 620.1 seconds and saved 62 successful database samples, with 0 query errors. After the authoritative pre-cleanup baseline, only one sample interval contained changes: the queue removal and digest insertion described above. No further changes were observed through 1:15:13 PM.

- `maintenance-complete-replay.json`: all 51 requests/responses, per-request SQL differences, and complete start/end snapshots.
- `maintenance-fresh-accepts.json`: explicitly approved preparation, complete SQL snapshots and effects for all three acceptances.
- `cleanup-before.json`, `cleanup-after-first.json`, `cleanup-after-second.json`: authoritative complete snapshots, excluding passwords.
- `cleanup-after-first-diff.json`, `cleanup-after-second-diff.json`: exact changes relative to the pre-cleanup baseline.
- `maintenance-after-replay-20261024T180453Z.jsonl`: timestamped sampling baseline and per-sample differences; includes replay/preparation effects before the authoritative baseline, which must not be confused with later maintenance.
- `maintenance-snapshot.sql`: exact read-only snapshot query. Raw captures are retained locally; `investigation/evidence/maintenance-followup-20261024.jsonl` contains complete authoritative snapshots, the exact SQL, all 51 replay summaries, and the observed cleanup delta. A copy is available as `maintenance-evidence.jsonl` with this writeup.

No commits or pushes were performed for this observation. Server data remains changed by the explicitly requested replays and approved acceptances; it has not been reset.
