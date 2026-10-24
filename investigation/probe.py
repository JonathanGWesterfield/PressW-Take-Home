"""Stdlib-only HTTP evidence and DB snapshots. Run from the repository root.

Does not access the legacy container: only its public HTTP port and Postgres.
"""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "investigation" / "evidence"
TABLES = ("tg_crew", "venues", "shifts", "assignments", "messages", "callboard_queue")


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def snapshot(label):
    # One statement gives all tables a consistent statement-level MVCC snapshot.
    sql = "SELECT json_build_object(" + ",".join(
        f"'{t}', (SELECT coalesce(jsonb_agg(to_jsonb(t) - 'password' ORDER BY id), '[]'::jsonb) FROM {t} t)"
        for t in TABLES
    ) + ");"
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "psql", "-U", "showcall", "-d", "showcall", "-At", "-c", sql],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    data = {"captured_at": timestamp(), "tables": json.loads(result.stdout)}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f"{label}.json"
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(label, {t: len(rows) for t, rows in data["tables"].items()})


def probe(label, path, org=7, query=None, form=None, method=None, base="http://localhost:8091"):
    method = method or ("POST" if form is not None else "GET")
    url = base + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    headers = {} if org is None else {"X-Org-Id": str(org)}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    raw = response.read().decode("utf-8", errors="replace")
    entry = {"label": label, "captured_at": timestamp(), "request": {"base": base, "method": method, "path": path, "org": org, "query": query, "form": form}, "response": {"status": response.status, "headers": dict(response.headers), "body": raw}}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with (EVIDENCE / "http.jsonl").open("a") as stream:
        stream.write(json.dumps(entry) + "\n")
    print(label, response.status, raw[:1600])
    return entry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot")
    parser.add_argument("--recorded-reads", action="store_true")
    args = parser.parse_args()
    if args.snapshot:
        snapshot(args.snapshot)
    if args.recorded_reads:
        for i, line in enumerate((ROOT / "traffic/traffic.jsonl").read_text().splitlines()):
            request = json.loads(line)
            if request["method"] == "GET":
                probe(f"recorded-{i}", request["path"], request["org"], request.get("query"))
