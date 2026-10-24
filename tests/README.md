# Repository verification

Run from the repository root with Docker Engine/Desktop (or Colima), Docker
Compose v2+, and Python 3 available. No local virtualenv or host ports are needed:

```sh
python3 scripts/verify                      # legacy baseline: full suite
python3 scripts/verify --backend encore     # same frozen cases, new wrappers
python3 scripts/verify --backend gateway    # same cases, dedicated migration routes
python3 scripts/verify --backend both       # same full suite: legacy, then Encore
```

`both` runs sequentially, with a separate fresh database/Compose project and report
directory for each backend. The test code, fixture data, frozen expectations and
pytest options are identical; only the selected backend URL changes. Both runs
are attempted even if the first has test failures, and the command succeeds only
if both pass. Interruption stops further runs after cleanup. Sequential execution
avoids fixture interference and competing stack resource use.

In `both` mode all cases run by default (`--maxfail=0`), so partial implementations
produce a complete failure report. Override after `--` for focused investigation.
The default single-backend command remains `legacy`, including the current CI
gate; manual CI runs can select `both`. Encore currently lacks crew wrappers, so
`both` should report legacy PASS and Encore FAIL until implementation is complete.

These shared assertions test the original `/callboard/crew/list` and `/show`
paths on either backend. The modern `/v3` API has its own intentional contract;
it must not replace the frozen legacy expectations.

The tests, fixtures, Compose topology, command and CI workflow live in this repo.
Each invocation creates temporary **runtime resources** under a unique
`showcall-verify-*` Compose project: its own network, services, and fresh seeded
Postgres in tmpfs. It publishes no host ports, never uses the development database,
and removes only its own resources after success, failure, timeout or handled
SIGINT/SIGTERM. Separate backend invocations therefore begin with equivalent
fixtures, including for writes. Do not run multiple writers against one instance.
Docker images/build cache persist for faster later runs. A forced SIGKILL or
Docker daemon failure cannot be handled: use the project identity in its report
to clean up that specific project (replace NAME with its recorded identity):

```sh
SHOWCALL_REPORT_DIR="$PWD/test-results/NAME" docker compose -f tests/compose.yml -p NAME down --volumes --remove-orphans
```

The runner builds Python 3.12 test/application images, waits for Postgres plus
bounded HTTP readiness, then runs pytest with live/write flags. Pytest executes
serially. Failures return nonzero, including startup/cleanup failure; a failing
test status survives teardown. Results are in ignored `test-results/<project>/`:
JUnit XML when pytest runs, owned-service logs, project/backend identity and exit
code. Startup readiness failures also save `readiness-error.txt`.

## What the gate proves

The default `legacy` gate runs unit tests, all existing 1,001 frozen crew
characterization tests (171 original cases, 828 fuzz replays, two behavioral
tests), three stack smoke tests, and two bounded Hypothesis crew properties. Exact
legacy response assertions include status, relevant headers, raw UTF-8 bodies,
HTTP-200 application failures and scoped DB invariance. Existing corpora are never
recorded or rewritten during verification. Raw/malformed requests retain the
existing stdlib transport so HTTPX cannot normalize away fuzz inputs. Existing
standalone recording remains supported; see `characterization/README.md`.

`--backend` changes the shared crew contract and property target; smoke tests
still check all three running services. `gateway` mounts `tests/routes.yaml`,
which sends **all crew orgs to Encore**, including the reserved fixture orgs.
Production/development routing is untouched. Encore currently has no crew wrappers,
so both `encore` and `gateway` contract runs are expected to **fail** until these
are implemented. No unsupported cases are skipped and no Encore response is used
as a new oracle. Gateway headers/protocol differences remain visible contract
failures and must be deliberately addressed during migration. A green legacy
baseline does not prove new-backend or gateway parity.

Fixtures use reserved orgs/IDs with collision checks and fixed timestamps. They
are installed and removed around suites, and committed HTTP/SQL effects are
checked explicitly; rolling back a pytest connection cannot undo service writes.
Fresh isolated databases are discarded after each invocation. Current tests mostly
exercise read endpoints with fixture SQL writes. New mutating HTTP scenarios must
reset owned fixture state between backends/scenarios and assert the resulting DB
state. The five-minute legacy maintenance job can mutate seeded scheduling rows;
ordinary crew tests compare all crew and only fixture-org scheduling rows. There
is no deterministic legacy clock control. Maintenance transitions, scheduling
write sequences, concurrency and broader endpoint coverage remain unimplemented.

Hypothesis exploration uses 30 deterministic examples per property by default,
without a stored example database. The pagination property includes negative
pages/sizes and the zero-size "all" behavior. The detail property applies decimal,
padded, signed, hex, octal, binary, and underscore ID forms to all 32 fixture rows
across owned/foreign/empty orgs, comparing full responses with the existing golden
data. This also exercises the recorded null, preferences, money, Unicode, and
lead-flag representations without inventing cleaner expectations.
Set `SHOWCALL_FUZZ_EXAMPLES=100 python3 scripts/verify` to expand the budget.
Save minimized discoveries as named regression cases with explicit,
reviewed known-answer expectations. The immutable fuzz corpus remains the fixed
regression suite; Schemathesis is deferred until `/v3` OpenAPI is useful.

Additional pytest selectors/options can follow `--`, for investigation only:

```sh
python3 scripts/verify --backend legacy -- -m 'unit or smoke'
python3 scripts/verify --backend encore -- --maxfail=5
```

The default gate includes all tests and stops after the first failing case;
the full matrix runs when it passes. Use `-- --maxfail=0` to continue after failures.
Do not use reduced selections as evidence that the full gate passed.

## Before main

`.github/workflows/verify.yml` runs the same default legacy command on pull
requests targeting main and main pushes, always uploading reports/logs. Manual
workflow runs accept any of the three targets. Configure a GitHub branch ruleset
for main to require the **Repository verification** check and PRs, disallowing
bypasses/direct pushes as appropriate. Workflow YAML alone does not protect main;
this task does not change remote rules. Before migration cutover, also require
successful Encore and migrated-gateway contract runs (add those targets to the
required CI jobs once wrappers exist). Until then CI validates the test
infrastructure and legacy baseline only.

## Local pytest and the existing investigation stack

```sh
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m pytest -m unit
.venv/bin/python -m pytest --e2e -m smoke
.venv/bin/python -m pytest --e2e --run-writes --backend legacy
```

Ordinary pytest does not start/reset a stack. Live tests require `--e2e`; fixture
and HTTP writes additionally require `--run-writes`. Defaults are legacy `8091`,
gateway `8080`, Encore `8092`; override with `--legacy-url`, `--gateway-url`,
`--encore-url` or their uppercase environment equivalents. `--backend` applies
those URLs to the existing unittest adapter too. The standalone adapter still
uses `docker compose exec db psql` unless `SHOWCALL_DATABASE_URL` explicitly
selects a Postgres connection via psycopg. Its standalone `--base` remains valid.
Never point write suites at a shared stack while another investigator is writing.

- `unit/`: isolated source/runner tests.
- `e2e/`: HTTP smoke/property tests using pytest and HTTPX.
- `characterization/`: immutable golden contracts and raw fuzz replay.

Mark new fixture/HTTP writers `pytest.mark.mutates_db`; directory discovery marks
characterization writes conservatively. Flags are selection guards, not network
firewalls. Preserve HTML/bytes and relevant headers, supply `X-Org-Id` explicitly,
and check payload errors even when HTTP status is 200. The challenge permits
HTTP and database observation; binary extraction/reverse engineering is outside
its stated boundary.
