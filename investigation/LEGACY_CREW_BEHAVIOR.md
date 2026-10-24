# Wave 1 legacy crew behavior: preserve this contract

Scope: `GET /callboard/crew/list` and `GET /callboard/crew/show`, plus their
observable method/routing behavior. These findings describe the supplied
Callboard image `r129e453a77` and Postgres 16 in this assessment. They were
recorded **before implementing alternate endpoints**. The separately labeled
Slice C follow-up below adds later public-HTTP observations without changing
those frozen responses. Unexpected behavior is an
expected result for the legacy wrappers, not a request to fix Callboard.

## Evidence and reproduction

- [`../tests/characterization/crew_contract.json`](../tests/characterization/crew_contract.json):
  the original, unchanged 171-case recording. References below prefixed `C:` are
  case names in that file.
- [`../tests/characterization/crew_fuzz_contract.json`](../tests/characterization/crew_fuzz_contract.json):
  828 additional fuzz cases, including 600 seeded-random combinations. References
  prefixed `F:` are case IDs. Each case points to a deduplicated exact response
  using `response_sha256`; no response bodies are truncated or JSON-normalized.
- [`crew-fuzz-report.json`](crew-fuzz-report.json): seed, counts, outcomes, capture
  time, scope of DB comparisons, and the original baseline's SHA-256.
- [`evidence/crew-fuzz-http.jsonl`](evidence/crew-fuzz-http.jsonl): per-request timing
  and raw response headers, including volatile transport fields. Join by case ID
  and response hash to the frozen corpus for the request and full body. Earlier
  and appended capture passes are retained, distinguished by timestamps.

From the repository root:

```sh
python3 tests/characterization/test_crew_contract.py
```

This runs 171 original cases, 828 fuzz cases, and two behavioral tests: **1,001
tests**. The behavioral tests include all 13 recorded frontend crew GETs and
visibility of a committed fixture change through both endpoints.

## Successful reads and serialization

The test org has 32 crew rows with explicit IDs 910001–910032, inserted in reverse
order. A second org owns crew 920001. These fixtures isolate the contract from
earlier exploratory writes to seeded customers.

| Input or stored value | Observed response | Evidence |
| --- | --- | --- |
| Valid list with no parameters | Page 1, total 32, first 25 rows ordered by ascending ID. The first crew's `prefs.ui_rows=3` does not change the page size. | C:`list_default` |
| Second org / org with no rows | One owned crew / empty array and total 0, with normal success envelopes. | C:`list_other_org`, `list_empty_org` |
| Detail lookup | Only the owned row. `user_name` is exposed under `crew_name`, and raw `prefs_blob` under `prefs`. | C:`show_fixture_01` |
| List vs detail | Detail includes `prefs`; list does not. Neither exposes password, `org_name`, or `created`. | C:`list_default`, `show_fixture_01` |
| Monetary values | Strings: `31.00`, `0.00`, `-2.35`, `999999.99`. Inserted `27.335` is stored by the numeric column and returned as `27.34`. | C:`show_fixture_01`, `04`–`07` |
| Null display name | JSON `null`, rather than an empty string. | C:`show_fixture_02` |
| Null notes, preferences, rate | All return `""`; null rate is distinguishable from numeric zero, which returns `"0.00"`. | C:`show_fixture_02`, `04` |
| Null, space, lowercase `y`, or `X` lead flag | Returned as `N`; uppercase `Y` returns `Y`. | C:`show_fixture_01`–`06` |
| Empty username / duplicate usernames | Preserved; rows are not deduplicated. | C:`show_fixture_04`–`06` |
| Unicode, emoji, HTML, quotes, newlines, tabs, backslashes | Values survive the JSON encoding. Legacy escaping, field ordering, compact separators, and final newline are retained in the recorded body strings. | C:`show_fixture_03` |
| Malformed preferences `{broken`, JSON array `[]`, nested preferences | Returned as the stored string; detail does not parse or repair it. | C:`show_fixture_03`, `05`, `07` |
| Committed change to notes | Both a subsequent detail read and list read reflect it, after an initial read. | `test_committed_update_visible` |

## Pagination: accepted and rejected inputs

| Input | Observed behavior | Evidence |
| --- | --- | --- |
| Missing or empty `page` / `per_page` | Defaults apply: page 1, size 25. An empty first duplicate value also chooses its default. | C:`list_page_parse_0`, `list_per_page_parse_0`; F:0161 |
| `page=0`, negative page, or `page=-0` | Effective page 1. | C:`list_page_0_size_5`, `list_page_-3_size_5`; F:0005 |
| `per_page=0` or `-0` | All 32 rows, even when page is greater than 1. The requested page number is still returned. | C:`list_page_2_size_0`; F:0047 |
| `per_page=-3&page=1` | First 29 rows; negative slicing semantics are externally visible. | C:`list_page_1_size_-3` |
| Negative size on later pages | The tested combinations return empty arrays while total remains 32. Preserve individual recorded cases; do not substitute modern validation. | C:`list_page_2_size_-3`, `list_page_3_size_-1` |
| Page beyond the last | Empty crew array, unchanged total. | C:`list_page_100_size_5` |
| `page=1_0` | Accepted as page 10. | F:0016 |
| Arabic-Indic `page=١` / full-width `page=１２` | Accepted as pages 1 / 12. The same digit forms in `per_page` are also accepted. | F:0029, 0030, 0071, 0072 |
| Superscript `²`, whitespace-only, decimal `2.0`, exponent `1e2`, booleans, SQL-like strings | Rejected with a Python integer-conversion error in an HTTP 200 failure envelope. Exact errors vary with the input. | F:0001–0041 and 0042–0083 |
| Very large values | Captured at integer boundaries and 4,300/4,301/5,000 digits. Parsing beyond Python's 4,300-digit limit returns its conversion-limit error; this is not a pagination-limit response. | F:0039–0041, 0081–0083 |
| Invalid page and invalid size together | Page conversion error wins; with valid page, the size conversion error is returned. | F:0826, 0827 |

## Crew IDs: PostgreSQL parsing differs from pagination

| Input | Observed behavior | Evidence |
| --- | --- | --- |
| Valid ID belonging to another org / nonexistent ID | HTTP 200 `{"error":"not found","result":"fail"}`. The tested responses do not distinguish these conditions. | C:`show_id_parse_5`, `show_id_parse_6`, `show_foreign_inverse` |
| Missing `crew_id`, empty value, or `crew_id[]=1` | PostgreSQL error for empty integer input, including its context text, with HTTP 200. | C:`show_id_missing`; F:0196–0198 |
| Signed, zero-padded, or surrounding ASCII-space ID | Accepted when it resolves to an owned ID. | C:`show_id_parse_8`–`10`; F:0824 |
| `crew_id=910_001` | Resolves to crew 910001. | F:0820 |
| `crew_id=0xde2b1`, `0o3361261`, `0b11011110001010110001` | Hexadecimal, octal, and binary forms all resolve to crew 910001 in the supplied Postgres version. | F:0821–0823 |
| `crew_id=9__10001` | PostgreSQL integer syntax error, rather than the pagination parser's Python error. | F:0825 |
| Unicode decimal digits `١` and `１２` | Rejected by PostgreSQL integer parsing, despite being accepted for pagination. | F:0113, 0114 |
| Beyond signed 32-bit integer range | PostgreSQL range/conversion error is returned; it is not converted into `not found`. | F:0110–0112; full expected messages are in the corpus |
| Decoded NUL byte `%00` | HTTP 200 with `PostgreSQL text fields cannot contain NUL (0x00) bytes`. | F:0116, 0201 |
| SQL-like expressions or quotes | Treated as invalid integer input in these probes, with the corresponding exact error string. No DB changes were observed. | F:0117, 0118; randomized cases |

## Tenant header and input precedence

| Input | Observed behavior | Evidence |
| --- | --- | --- |
| Missing, blank, malformed, negative, plus-signed, or comma-separated org | `missing org`, with HTTP 200, in the tested cases. Numeric zero is a recognized org value but has no fixture records. | Original `list_org_*` and `show_org_*`; F:0130, 0131 |
| Org padded with leading zeroes or surrounding ASCII spaces/tabs | Accepted and resolves to org 900071 in these probes. | F:0126–0129, 0173–0176 |
| `X-Org-Id: ²` | Python integer conversion error, rather than `missing org`. Do not assume all invalid headers share one result. | F:0133, 0180 |
| Two org headers, even with identical values or differing header-name case | `missing org`; the supplied HTTP stack combines the values. Neither first-wins nor last-wins tenant selection matches this observation. | F:0135–0138, 0182–0185 |
| Lowercase `x-org-id` | Accepted as the same header. | C:`list_lowercase_org_header`, `show_lowercase_org_header` |
| Org in query or JSON body | Does not override the org header. | C:`list_query_org_ignored`, `show_query_org_ignored`, `*_json_body_ignored` |
| Bad/missing org plus bad page or bad ID | Org failure occurs first. A valid org exposes the subsequent parameter error. | F:0170–0172, 0217–0219 |

## Query decoding, paths, methods, and response negotiation

| Input | Observed behavior | Evidence |
| --- | --- | --- |
| Repeated `page`, `per_page`, or `crew_id` | First value wins, including an invalid or empty first value. | C:`list_duplicate_page`, `list_duplicate_size`, `show_duplicate_id_*`; F:0160, 0161, 0207, 0208 |
| Percent-encoded parameter names `%70age` / `%63rew_id` | Recognized as `page` / `crew_id`. | F:0162, 0209 |
| Raw `+` vs `%2B` before a valid number | Both tested forms are accepted, although query decoding produces a space vs a literal plus. | F:0152, 0153, 0199, 0200 |
| `%FF`, `%C0%AF`, `%`, `%GG` query values | Error strings retain those percent sequences in this HTTP stack. Do not silently replace them with Unicode replacement characters. | F:0155–0158, 0202–0205 |
| Semicolon in a query value | Part of the value, not a second query separator; causes the relevant numeric error. | F:0159, 0206 |
| Unknown `search`, `sort`, `crew_id` on list | Ignored in the tested requests. | C:`list_unknown_filters` |
| Encoded path segment `%63rew` or encoded separator `crew%2Flist` / `crew%2Fshow` | Decodes to the working endpoint. | F:0163, 0164, 0210, 0211 |
| Double slash `/callboard//crew/list` or `/show` | **HTTP 308**, HTML body, absolute `Location` redirect with query preserved. This is an exception to the usual HTTP 200 errors. | F:0165, 0212 |
| Dot segment, trailing slash (literal or encoded), extra suffix, semicolon suffix, changed path case | HTTP 200 JSON containing the framework's 404 error text. No redirect for the tested trailing slash. | Original `*_suffix_*`, `*_uppercase_path`; F:0166–0169, 0213–0216 |
| POST/PUT/PATCH/DELETE/TRACE/BREW on these read paths | HTTP 200 JSON containing the framework's 405 error text. | Original `*_method_*`; F:0139, 0140, 0186, 0187 |
| HEAD | Empty body; content type and length correspond to GET, including its success or error representation. | Original `*_method_HEAD`; randomized HEAD requests |
| OPTIONS | Empty HTML body, length 0, allows GET/HEAD/OPTIONS. | Original `*_method_OPTIONS`; randomized OPTIONS requests |
| GET with form, malformed JSON, or text body | Tested bodies do not replace query/header inputs or trigger JSON parsing errors. | F:0141–0143, 0188–0190 |
| XML/HTML Accept, gzip preference, conditional ETag, Range | The tested requests still return the ordinary complete JSON response; no observed XML conversion, compression, 304, or partial content. | Original `*_accept_html`; F:0144–0147, 0191–0194 |

## Slice C follow-up observations (2026-10-24)

These four additional requests were sent directly to Callboard while reviewing
the new compatibility adapter. Their request specifications, compared headers,
and full response bodies are retained in
[`slice-c-targeted-legacy-probes-20261024.jsonl`](evidence/slice-c-targeted-legacy-probes-20261024.jsonl).
They are new source observations, not Encore-generated expectations or edits to
the original frozen corpora.

| Input | Observed legacy response | Evidence case |
| --- | --- | --- |
| Org header `9_00071` | HTTP 200 `missing org`, despite Python `int()` accepting underscores for pagination. | `org_underscore` |
| Org header `-0` | HTTP 200 `missing org`; unsigned `0` remains an accepted empty tenant. | `org_negative_zero` |
| Latin-1 superscript org header `³` | HTTP 200 with Python's `invalid literal for int() with base 10: '³'` error, extending the previously recorded `²` case. | `org_superscript_three` |
| Double-slash detail path with multiple query parameters and percent-encoded quote/angle-bracket text | HTTP 308; Location retains the raw query's `&`, while both occurrences of the URL in redirect HTML escape it as `&amp;`. Percent-encoded text stays encoded. | `redirect_quoted` |

Focused compatibility regression tests cover these discoveries separately from
the unchanged original corpus. Org parsing therefore cannot simply reuse
pagination's `int()` acceptance rules, and redirect construction must preserve
both the Location value and its distinct HTML representation.

## What the fuzz run established, and its limits

The final corpus contains 828 distinct fuzz requests. Each was sent twice during
capture and produced the same compared response. There were 196 JSON successes,
555 JSON failures, 75 empty responses from method handling, and two HTML redirects.
HTTP status was 200 in 826 cases and 308 in two. All original 171 expected responses
remained unchanged; the append-only follow-up also required the first 820 fuzz
inputs and responses to remain unchanged.

During discovery, DB comparisons ran every 25 requests and after each pass. The
regression suite compares after every test. Crew rows are checked globally;
assignments, shifts, venues, messages, and queue rows are checked for the reserved
orgs only, so independent legacy maintenance of seeded scheduling data does not
cause false attribution. No compared data changed, and temporary crew rows were
removed. This does not prove absence of writes to unrelated seeded scheduling
tables, nor does it establish production authentication or comprehensive security.

Tests preserve exact status, all non-transport response headers, and full body
strings. `Date`, `Server`, connection/framing headers are excluded from parity;
their captured values remain in the raw log. `Allow` order is compared as a method
set because process ordering varies. The fuzz replay fixes the incoming `Host` to
the captured `localhost:8091` when targeting another backend port; this keeps
redirect input identical without rewriting the expected URL or HTML body.

Discovery used bounded values (at most 5,000 digits), raw-query/path mutations, and
a fixed random seed `20261024`. It did not exhaust all HTTP parser cases, change
legacy configuration, test crash recovery or concurrency, or inspect the legacy
container/binary. These are compatibility observations, not recommendations to
change the behavior. Additional evidence should append cases rather than replace
awkward responses with cleaner expectations.
