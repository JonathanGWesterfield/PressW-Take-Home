# D2: prepare rollout configuration and rollback

- **Owner:** `/root/e1_implementer` (review: `/root/e1_reviewer`)
- **Status:** Prepared and independently approved; ready for I1 live rehearsal
- **Dependencies:** Agree fixture contract with D1; live application is coordinated by I1
- **Last updated:** 2026-10-24; verify current working tree at task start

## Working context

This is the interview-sized Wave 1 migration in PressW-Take-Home. Move only org 7's legacy crew list/show reads to Encore, with modern v3 reads sharing retrieval. Callboard retains every write and maintenance job against the shared database. Read the [design](../templates/WAVE1_DESIGN.md), [assessment brief](../README.md), [seam map](../SEAMS.md), and [coordination index](README.md). The working tree already contains substantial implementation; inspect it and saved results before making changes. Preserve unrelated edits and frozen corpora.

## Ownership

Own `docker-compose.yml`, `proxy/routes.yaml`, rollout fixtures under `tests/routes/` after agreement with D1, and this task file. Do not independently change shared runner files or restart/reconfigure the running stack.

## Task

1. Inspect existing configuration changes; identify what is already complete.
2. Prepare a containing-directory route mount and matching `ROUTES_FILE`, so validated atomic route-file replacement is visible to the gateway. Avoid the single-file mount's stale-inode hazard and partial in-place YAML writes.
3. Prepare canonical org 7 overrides for `/callboard/crew/list` and `/callboard/crew/show`, retaining the legacy default. Do not accidentally move crew/update or other orgs.
4. Keep `legacy.yaml` and `mixed-org7.yaml` fixture names stable for D1. Agree any fixture changes before publishing them.
5. Specify whether modern clients use Encore directly or an explicit `/v3/crew` gateway route. Legacy rollback must not send v3 requests to unsupported Callboard paths.
6. Record exact preparation, cutover and rollback commands/config changes for I1. Topology preparation may require one restart while all routing is legacy; cutover and rollback afterward must be config-only.

## Acceptance checklist

- [x] Compose and route configuration validate locally.
- [x] The mixed fixture selects only canonical org-7 read prefixes (including suffixes, per existing prefix semantics); live proof is I1 work.
- [x] Atomic config publication and rollback procedure are concrete and exercised against a temporary target.
- [x] Callboard retains write/job ownership and shared DB schema is unchanged.
- [x] I1 has stable fixtures and the runbook below for live rehearsal; actual deployment evidence remains pending.

## Agent output

Update this section as work proceeds. Record exact commands/results and artifact paths; distinguish existing evidence from fresh verification.

### Progress log

- Read the assessment, seam map, full design and D1/index context. Adopted the existing directory mount and unchanged fixture interface; no topology operation or live route publication performed.

### Changes made

- Retained the existing `./proxy:/srv/routes:ro` containing-directory bind and `ROUTES_FILE=/srv/routes/routes.yaml`. This keeps atomic replacement visible without giving the gateway write access.
- Replaced the unsafe broad crew-prefix example in `proxy/routes.yaml` with the two canonical quoted-org read prefixes. Effective routes remain all-legacy. Clarified direct modern access in Compose/route comments.
- Fixtures remain byte-for-byte unchanged: `legacy.yaml` and `mixed-org7.yaml`, matching D1's publisher calls. No shared database/schema, application, runner, write or job ownership change.

### I1 preparation and publication runbook

Run from the repository root. Commands below are prepared for I1; D2 did not execute live operations. `.venv/bin/python` must have PyYAML (`tests/requirements.txt`). Do not reset the database or restart backends for cutover/rollback.

1. Inspect `docker compose config` and `docker compose ps`. While the effective routes are still all-legacy, deploy the directory-mount topology once if the running gateway has the old single-file mount:

   ```sh
   docker compose config --quiet
   docker compose up -d --no-deps --build --force-recreate gateway
   docker compose exec -T gateway python -c 'import os; from pathlib import Path; p = Path(os.environ["ROUTES_FILE"]); assert str(p) == "/srv/routes/routes.yaml"; print(p.read_text())'
   ```

   I1 must confirm the directory mount is read-only using `docker inspect` on `docker compose ps -q gateway`. This preparation recreation is allowed before cutover; capture gateway identity **after** preparation. If the existing deployment already has the reviewed topology and current gateway code, recreation is unnecessary.

2. Save the exact existing route bytes and baseline identity/responses. This guard prevents this whole-file fixture from dropping unrelated routing rules; if it fails, stop and merge/review a candidate that preserves those rules:

   ```sh
   mkdir -p test-results
   D2_BACKUP_DIR=$(mktemp -d "$PWD/test-results/d2-rollout.XXXXXX")
   export D2_BACKUP_DIR
   .venv/bin/python - <<'PY'
   import os
   from pathlib import Path
   import yaml
   source = Path("proxy/routes.yaml")
   table = yaml.safe_load(source.read_bytes())
   assert set(table) == {"routes"}
   assert set(table["routes"]) == {"/callboard/"}
   rule = table["routes"]["/callboard/"]
   assert set(rule) <= {"default", "orgs"}
   assert rule["default"] == "callboard" and not rule.get("orgs")
   Path(os.environ["D2_BACKUP_DIR"], "routes-before.yaml").write_bytes(source.read_bytes())
   PY
   curl -fsS http://localhost:8080/gateway/healthz > "$D2_BACKUP_DIR/health-before.json"
   curl -fsS -D "$D2_BACKUP_DIR/list-before.headers" -H 'X-Org-Id: 7' 'http://localhost:8080/callboard/crew/list' > "$D2_BACKUP_DIR/list-before.json"
   curl -fsS -D "$D2_BACKUP_DIR/show-before.headers" -H 'X-Org-Id: 7' 'http://localhost:8080/callboard/crew/show?crew_id=2' > "$D2_BACKUP_DIR/show-before.json"
   ```

   These response captures support live investigation; HTTP 200 alone is not parity or business-success proof. I1 owns controlled write visibility, exact response/header comparisons and scoped DB checks. Crew 2 is seeded org 7, not a disposable new record.

3. Define a validated atomic publisher in the same shell. It validates allowed shape/backends, writes/fsyncs a temporary file **inside `proxy/`**, then atomically replaces `routes.yaml`; it never truncates the live file in place:

   ```sh
   publish_d2_routes() {
     .venv/bin/python - "$1" <<'PY'
   import os
   from pathlib import Path
   import sys
   import tempfile
   import yaml
   payload = Path(sys.argv[1]).read_bytes()
   table = yaml.safe_load(payload)
   assert isinstance(table, dict) and set(table) == {"routes"}
   assert isinstance(table["routes"], dict) and table["routes"]
   for prefix, rule in table["routes"].items():
       assert isinstance(prefix, str) and prefix.startswith("/")
       assert isinstance(rule, dict) and set(rule) <= {"default", "orgs"}
       assert rule.get("default") in {"callboard", "encore"}
       orgs = rule.get("orgs", {})
       assert isinstance(orgs, dict)
       assert all(isinstance(org, str) and backend in {"callboard", "encore"} for org, backend in orgs.items())
   target = Path("proxy/routes.yaml")
   temporary = None
   try:
       with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".routes-", suffix=".yaml", delete=False) as stream:
           temporary = Path(stream.name)
           stream.write(payload)
           stream.flush()
           os.fsync(stream.fileno())
       os.chmod(temporary, 0o644)
       os.replace(temporary, target)
   finally:
       if temporary is not None:
           temporary.unlink(missing_ok=True)
   PY
   }
   ```

4. After combined gates pass, cut over using `publish_d2_routes tests/routes/mixed-org7.yaml`. Capture the same org-7 list/show and require `X-Served-By: encore` with compatible bodies. Verify noncanonical orgs (`07`, padded), other orgs, crew/update, scheduling and messaging remain Callboard-served using D1/I1's guarded scenarios. Prefix suffixes such as `list/extra` also select Encore and must retain compatible errors; configuration is not method/exact-path filtering. Modern callers use `http://localhost:8092/v3/crew` with `X-Org-Id: 7`, never a gateway fallback.

5. Roll back with `publish_d2_routes "$D2_BACKUP_DIR/routes-before.yaml"`. Require both reads return Callboard-served compatible responses again. Capture `/gateway/healthz` after cutover and rollback and compare `instance_id` with `health-before.json`; any change invalidates the no-restart demonstration. Do not use `docker compose up`, restart, or rebuild between steps 4 and 5. Modern requests remain direct Encore and are not rolled back to unsupported Callboard v3 paths. Keep the final all-legacy routes until I1 chooses the submission cutover state.


### Validation and evidence

- Fresh `docker compose config --quiet` → exit 0 (configuration validation only; no services started/restarted).
- Fresh `.venv/bin/python -m pytest tests/unit/test_gateway_routing.py tests/unit/test_verification_runner.py -q` → **25 passed in 0.30s**. Covers actual selector boundaries, atomic rename reload, first duplicate-header routing, directory-mount configuration, owned runner cleanup/status semantics. No containers or network requests.
- Fresh bounded `.venv/bin/python` inline assertions loaded both fixtures and the actual `proxy/app.py` selector with a stub HTTP client: **98 decisions passed** (two fixture states × seven paths × seven org/header states). Verified canonical `7` only, both read prefixes/suffixes, nonmigrated writes and modern gateway fallback. Structural assertions require exactly the existing three mixed prefixes and canonical quoted-org overrides; no fixture edit was needed.
- Extracted the `publish_d2_routes` shell function verbatim from this task record and ran it via `bash -c` in a temporary directory containing a fake `proxy/` target: mixed cutover bytes matched, rollback restored exact original bytes, invalid backend was rejected with target unchanged, and no temporary publisher file remained. This tests the documented file operation, **not** the live mount or live gateway reload.
- `git diff --check -- docker-compose.yml proxy/routes.yaml tasks/D2-rollout-configuration.md tests/routes` → exit 0.
- No live route changes, restart, database reset, full matrix, cutover or rollback were performed by D2. I1 still must prove the actual deployment mount, routing responses and stable gateway instance. No fresh live artifact exists from this configuration task.

### Review feedback and corrections

| Finding / source | Correction | Recheck / disposition |
| --- | --- | --- |
| Coordinator pre-review: unsafe example and precise publication prerequisites. | Replaced broad crew example with both canonical read prefixes, linked the exact task path, guarded backup against unrelated rule fields, and left final deployment state to I1. | Scoped whitespace and effective all-legacy YAML assertions passed. |
| `/root/e1_reviewer`: independent implementation/runbook review. | No new actionable findings. | Approved after Compose config, 25 focused tests (0.33s), and independent extracted-publisher cutover/exact rollback/invalid-backend/unknown-field rejection + cleanup checks. Live mount/reload/rehearsal remains I1 work. |

### Handoff

- Changed files: `docker-compose.yml` (modern/legacy access comments; adopted prior directory-mount implementation), `proxy/routes.yaml` (comments only), and this task record. Package also adopts the existing untracked `tests/routes/legacy.yaml` and `tests/routes/mixed-org7.yaml` fixtures; their bytes were unchanged by D2.
- Integration requests / dependencies: D1 fixture names and contents preserved, with existing publisher interface inspected. I1 must run full gates, prepare live mount/code topology once while all-legacy, then execute the runbook and capture actual config-only cutover/rollback evidence.
- Remaining risks or blockers: prefix matching also routes invalid method/suffix requests to the selected backend; wrapper fidelity handles their errors. Atomic replacement requires the running directory mount, which D2 cannot prove from source. No last-known-good parser fallback exists. Modern clients remain direct and independent of legacy rollback.
- Final status and reviewer reference: `/root/e1_reviewer` independently approved the prepared configuration/runbook; ready for I1. Ready for the dedicated D2 commit by the coordinator; no commit was created by the implementer.
