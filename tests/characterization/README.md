# Wave 1: frozen legacy crew contract

These tests were written and captured **before** implementing any Encore crew
endpoint. Their reference is the running, supplied Callboard image
`ghcr.io/pressw-llc/showcall-callboard:r129e453a77`, accessed only over HTTP.
The suite uses the allowed database for fixtures and side-effect checks.

## Run

Start the supplied stack, then run from the repository root:

```sh
python3 tests/characterization/test_crew_contract.py
```

No pip installs are needed: this uses Python's standard library and the running
Postgres container's `psql`. It requires Docker/Compose access and access to local
HTTP ports. A stopped service or unavailable database is a **failure**, not a skip.
The transport, database adapter, and fixture lifecycle are shared with discovery
through `investigation/crew_support.py`; the HTTP request/response expectations
remain in the two unchanged JSON corpora beside this test driver.
Standard discovery also runs the full matrix:

```sh
python3 -m unittest discover -s tests/characterization -v
```

## What is locked

`crew_contract.json` contains the original, unchanged 171 request/response pairs.
`crew_fuzz_contract.json` adds 828 frozen fuzz cases. Verification runs both plus
two behavioral tests, for **1,001 tests**. The recorded-traffic test additionally
exercises all 13 crew GET requests in `traffic/traffic.jsonl`.

The fuzz corpus includes 600 fixed-seed random combinations plus targeted numeric,
encoding, duplicate-header, raw-path, body, method, and error-precedence cases.
See [the detailed compatibility notes](../../investigation/LEGACY_CREW_BEHAVIOR.md)
for successful, failing, and surprising results with individual evidence IDs.

| Coverage | Cases |
| --- | --- |
| Pagination and ordering | 32 deliberately reverse-inserted crew records; default page size, 42 page/size combinations, empty org, second org, empty/invalid/huge/signed/whitespace inputs, repeated keys, ignored filters |
| Detail | Every fixture row; missing, invalid, zero, negative, foreign, nonexistent, overflowing, signed, padded, duplicate, and injection-like IDs |
| Tenant boundary | Missing/empty/malformed/zero/negative/leading-zero/padded org headers, both directions of cross-org detail access, query/body attempts to override the org header, lowercase header name |
| Stored values | Nulls, empty strings, Unicode/emoji, HTML and quotes, multiline/backslash notes, duplicate usernames, malformed/nested preferences, null/zero/negative/max rates, numeric rounding, nonstandard lead flags |
| Wire and routing | HTTP status, exact UTF-8 body bytes including JSON formatting/newline, content type/length, other selected headers; GET/HEAD/OPTIONS/POST/PUT/PATCH/DELETE; trailing slash, extra suffix, path casing, Accept header and JSON GET body |
| Live behavior | A committed fixture change becomes visible through both reads after an initial read; replay of the real frontend's crew reads against current seed-org data |
| Side effects | After **every test**, all crew rows across all orgs and all six tables for the reserved orgs are compared with the fixture baseline |

All non-transport response headers are compared, including unexpected additional
ones. `Date`, `Server`, `Connection`, `Keep-Alive`, and `Transfer-Encoding` are
excluded. `Allow` is compared as a sorted method set because its order varies
across Flask process starts. Bodies are not JSON-normalized, and malformed inputs
are not filtered out of the compatibility contract. The raw fuzz HTTP log retains
all response headers, including excluded ones.

The fuzz replay pins incoming `Host` to its captured `localhost:8091`, including
when targeting Encore on another port. Identical Host input makes the frozen
absolute redirect URL/HTML comparable without normalizing their contents.

The fixture and request matrix are fingerprinted/compared with the recording.
Changing either without deliberately updating the reviewed baseline fails setup.

## Fixture safety and independence

- Reserved orgs: **900071**, **900072**, and empty **900073**.
- Explicit crew IDs: **910001–910032**, plus **920001** in the second org.
- An atomic collision check refuses to overwrite existing rows. Explicit IDs
  avoid advancing the seed data's serial sequence.
- Fixtures are inserted before the suite and removed afterward, including when
  assertions fail. Existing seeded crew rows are checked again after cleanup.
- The visibility test changes only fixture notes and restores them in `finally`.
- No database reset, legacy container inspection, route change, or application
  implementation is performed. No password fields are in the recorded responses;
  each successful GET additionally checks for accidental password disclosure.
- Use one suite at a time. An interrupted/killed process can leave fixture rows;
  the next run fails the collision check instead of silently deleting them.

The background job can still mutate **seeded assignments/messages/queue** during
a run. The side-effect check compares those five non-crew tables only for reserved
orgs, where there is no background work. It therefore does **not** prove absence
of writes to unrelated seeded scheduling rows. Crew is compared globally. Do not
edit seeded crew concurrently with this suite.

## Baseline review: notable behavior

- Default page size is **25**, regardless of the fixture's `prefs.ui_rows=3`.
- Results are ID-ordered despite reverse insertion and reversed display names.
- `per_page=0` returns all rows; negative sizes preserve slicing-like behavior.
- First repeated query value wins.
- A null display name stays JSON null, while null notes/preferences become `""`;
  a null rate becomes `""`, whereas a zero rate becomes `"0.00"`.
- Lead flags other than uppercase `Y` serialize as `N` in these fixtures.
- Preferences are returned verbatim, including malformed JSON; only detail
  includes `prefs`. Password, organization name, and creation time aren't exposed.
- Missing/malformed IDs can expose Postgres error strings with HTTP 200. Wrong
  methods and missing routes similarly return JSON errors with HTTP 200.
- `HEAD` has an empty body and the corresponding GET's content length.
  `OPTIONS` has an empty HTML body and allows GET, HEAD, OPTIONS.

## Updating the baseline and later parity

The baseline is already captured. Normal runs never rewrite it. If new evidence
requires a deliberate update, review the diff from this explicit command:

```sh
python3 tests/characterization/test_crew_contract.py --record --replace
```

Do not rewrite existing expected results to accommodate a replacement. The fuzz
discovery script refuses to overwrite its corpus. To add newly designed fuzz
inputs, append them in `investigation/fuzz_crew.py` and explicitly run
`python3 investigation/fuzz_crew.py --extend`. That operation requires every
previously recorded fuzz request and response to remain unchanged and repeats
every response before saving the enlarged corpus.

Recording is restricted to `http://localhost:8091` so an incomplete replacement
cannot become its own oracle. After the legacy wrappers exist, run the same frozen
contract against Encore (the `/v3` API gets its own deliberate contract):

```sh
python3 tests/characterization/test_crew_contract.py --base http://localhost:8092
```

The repository-owned isolated equivalent is `python3 scripts/verify --backend
encore` (or `legacy` / `gateway`). It uses the same golden files, a fresh database,
and the environment-configurable HTTP/Postgres adapter; see `../README.md`.
Use `python3 scripts/verify --backend both` to run the identical full suite against
legacy and then Encore, with a separate fresh database/report for each. Both runs
execute all cases by default and neither records replacement expectations.

The final isolated `python3 scripts/verify --backend both` run passed this
unchanged direct contract against legacy and Encore in separately seeded stacks:
1,084 testcase elements per backend (1,097 in JUnit's suite counter because it
also counts 13 unittest subtests). This establishes bounded direct-wrapper
compatibility for the frozen corpus; the gateway ingress/cutover contract is
verified separately. It does not establish production authentication or
exhaustive behavior for all possible inputs.
