"""Shared crew HTTP/DB probes and isolated fixtures for discovery and verification.

Stdlib-only by default; SHOWCALL_DATABASE_URL selects optional psycopg in the
isolated verification container. No requests or DB mutations occur on import.
"""
import http.client
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/characterization/crew_contract.json"
FUZZ_GOLDEN = ROOT / "tests/characterization/crew_fuzz_contract.json"
ORG, OTHER, EMPTY = 900071, 900072, 900073
FIRST, FOREIGN = 910001, 920001
TABLE_ORGS = {"tg_crew": "org", "venues": "company_no", "shifts": "org_id",
              "assignments": "org_id", "messages": "org", "callboard_queue": "org_id"}
BASE = os.getenv("SHOWCALL_CONTRACT_URL", "http://localhost:8091")


def db(sql):
    # The isolated Compose runner connects to its own Postgres over the test
    # network. Standalone stdlib recording retains the original Docker workflow.
    if database_url := os.getenv("SHOWCALL_DATABASE_URL"):
        import psycopg
        with psycopg.connect(database_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, prepare=False)
                rows = []
                while True:
                    if cursor.description:
                        rows.extend("|".join(json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                                             for value in row) for row in cursor.fetchall())
                    if not cursor.nextset():
                        break
                return "\n".join(rows).strip()
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-X", "-v", "ON_ERROR_STOP=1",
         "-U", "showcall", "-d", "showcall", "-At"],
        input=sql, text=True, capture_output=True, cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def fixtures():
    rows = []
    for i in range(1, 33):
        rows.append(dict(id=910000+i, org=ORG, org_name="Contract org",
                         user_name=f"crew-{i:02}@contract.example", display_name=f"Name {33-i:02}",
                         password="DO-NOT-EXPOSE", rate="24.50", is_lead="N", notes=f"note {i}",
                         prefs_blob='{"sms":"Y","ui_rows":3,"digest":"N"}', created=1700000000))
    rows[0].update(display_name="Z first", rate="31.00", is_lead="Y")
    rows[1].update(org_name=None, display_name=None, rate=None, is_lead=None, notes=None,
                   prefs_blob=None, created=None)
    rows[2].update(user_name="zoë+测试@contract.example", display_name="Zoë 🎭 <lead> & \"crew\"",
                   notes="<script>alert('x')</script> & \"quoted\"\nnext\t\\end", prefs_blob="{broken", rate="15.55")
    rows[3].update(user_name="", display_name="", rate="0", is_lead=" ", notes="", prefs_blob="")
    rows[4].update(user_name="duplicate@contract.example", rate="-2.35", is_lead="y", prefs_blob="[]")
    rows[5].update(user_name="duplicate@contract.example", rate="999999.99", is_lead="X")
    rows[6].update(rate="27.335", prefs_blob='{"nested":{"a":[1,true,null]}}')
    rows.append(dict(rows[0], id=FOREIGN, org=OTHER, org_name="Foreign org", user_name="foreign@contract.example"))
    # Physical insertion order differs from ID/name order on purpose.
    return list(reversed(rows))


def database_state():
    # Crew is compared across all orgs. Other tables are scoped to test orgs so
    # real legacy maintenance of the seeded assignments doesn't make tests flaky.
    selects = []
    for table, column in TABLE_ORGS.items():
        where = "" if table == "tg_crew" else f" WHERE {column} IN ({ORG},{OTHER},{EMPTY})"
        selects.append(f"'{table}', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM {table} t{where})")
    return json.loads(db("SELECT jsonb_build_object(" + ",".join(selects) + ");"))


def request(path, org=ORG, query=None, method="GET", body=None, extra_headers=None):
    headers = {"X-Org-Id": str(org)} if org is not None else {}
    headers.update(extra_headers or {})
    return dict(path=path, query=[list(pair) for pair in (query or [])], method=method, headers=headers, body=body)


def send(spec, base=None, include_transport=False, host=None):
    url = urlsplit(base or BASE)
    if url.scheme != "http" or url.path not in ("", "/"):
        raise ValueError("Use an http://host:port base without a path")
    path = spec["path"]
    if "raw_query" in spec:
        path += "?" + spec["raw_query"]
    elif spec["query"]:
        path += "?" + urlencode([tuple(pair) for pair in spec["query"]])
    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=10)
    try:
        if "header_pairs" in spec:
            pairs = list(spec["header_pairs"])
            if host is not None and not any(name.lower() == "host" for name, value in pairs):
                pairs.append(["Host", host])
            connection.putrequest(spec["method"], path, skip_host=any(name.lower() == "host" for name, value in pairs))
            for name, value in pairs:
                connection.putheader(name, value)
            if spec["body"] is not None:
                connection.putheader("Content-Length", str(len(spec["body"].encode("latin-1"))))
            connection.endheaders(spec["body"].encode("latin-1") if spec["body"] is not None else None)
        else:
            headers = dict(spec["headers"])
            if host is not None:
                headers.setdefault("Host", host)
            connection.request(spec["method"], path, body=spec["body"], headers=headers)
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        # Allow is an unordered method set; its order varies between Flask
        # processes. All other selected headers and body bytes are exact.
        selected = {key: value for key, value in headers.items()
                    if key not in {"date", "server", "connection", "keep-alive", "transfer-encoding", "allow"}}
        if "allow" in headers:
            selected["allow"] = sorted(v.strip() for v in headers["allow"].split(","))
        captured = dict(status=response.status, headers=selected, body=response.read().decode("utf-8"))
        return (captured, response.getheaders()) if include_transport else captured
    finally:
        connection.close()



class CrewFixture:
    @classmethod
    def install_fixture(cls):
        cls.installed = False
        # Session-independent transactions use exact reserved orgs/IDs. Never
        # delete stale fixtures automatically or touch a colliding user's rows.
        cls.preexisting_crew = json.loads(db("SELECT jsonb_agg(to_jsonb(t) ORDER BY id) FROM tg_crew t;"))
        payload = literal(json.dumps(fixtures()))
        db(f"""BEGIN;
            SELECT pg_advisory_xact_lock({ORG});
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM tg_crew WHERE org IN ({ORG},{OTHER},{EMPTY})
                    OR id BETWEEN 910001 AND 910032 OR id={FOREIGN}) THEN
                    RAISE EXCEPTION 'Reserved fixture IDs/orgs occupied; inspect before cleanup';
                END IF;
            END $$;
            INSERT INTO tg_crew SELECT * FROM jsonb_populate_recordset(NULL::tg_crew, {payload}::jsonb);
            COMMIT;""")
        cls.installed = True
        cls.before = database_state()


    @classmethod
    def cleanup_fixture(cls):
        if getattr(cls, "installed", False):
            db(f"DELETE FROM tg_crew WHERE (org={ORG} AND id BETWEEN 910001 AND 910032) OR (org={OTHER} AND id={FOREIGN});")
            cls.installed = False
            remaining = json.loads(db("SELECT jsonb_agg(to_jsonb(t) ORDER BY id) FROM tg_crew t;"))
            if remaining != cls.preexisting_crew:
                raise AssertionError("Non-fixture crew changed during the suite")


