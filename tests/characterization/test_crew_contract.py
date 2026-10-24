"""Live black-box characterization of Callboard crew list/show; stdlib only.

Capture once: python3 tests/characterization/test_crew_contract.py --record
Verify:       python3 tests/characterization/test_crew_contract.py
Future parity: add --base http://localhost:8092 after wrappers exist.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
_support_spec = importlib.util.spec_from_file_location("crew_support", ROOT / "investigation/crew_support.py")
_support = importlib.util.module_from_spec(_support_spec)
_support_spec.loader.exec_module(_support)
GOLDEN, FUZZ_GOLDEN = _support.GOLDEN, _support.FUZZ_GOLDEN
ORG, OTHER, EMPTY = _support.ORG, _support.OTHER, _support.EMPTY
FIRST, FOREIGN = _support.FIRST, _support.FOREIGN
BASE = _support.BASE
fixtures, database_state, db, request = _support.fixtures, _support.database_state, _support.db, _support.request


def send(spec, base=None, **kwargs):
    return _support.send(spec, base=base or BASE, **kwargs)


def cases():
    result = {}
    def add(name, path="/callboard/crew/list", **kwargs):
        result[name] = request(path, **kwargs)

    add("list_default")
    add("list_other_org", org=OTHER)
    add("list_empty_org", org=EMPTY)
    for page in (-3, 0, 1, 2, 3, 100):
        for size in (-3, -1, 0, 1, 5, 25, 100):
            add(f"list_page_{page}_size_{size}", query=[("page", str(page)), ("per_page", str(size))])
    for param in ("page", "per_page"):
        for i, value in enumerate(("", " ", "oops", "1.0", "+2", "02", " 2 ", "2147483648", "-2147483648", "1; SELECT 1", "²")):
            add(f"list_{param}_parse_{i}", query=[(param, value)])
    for path_name in ("list", "show"):
        path = f"/callboard/crew/{path_name}"
        query = [("crew_id", str(FIRST))] if path_name == "show" else []
        for i, org in enumerate((None, "", "oops", "0", "-1", "+900071", "0900071", " 900071 ", "900071.0", "2147483648", "²")):
            add(f"{path_name}_org_{i}", path, org=org, query=query)
        for method in ("HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"):
            add(f"{path_name}_method_{method}", path, query=query, method=method)
        for suffix in ("/", "/extra"):
            add(f"{path_name}_suffix_{len(suffix)}", path+suffix, query=query)
        add(f"{path_name}_accept_html", path, query=query, extra_headers={"Accept": "text/html"})
        add(f"{path_name}_lowercase_org_header", path, org=None, query=query, extra_headers={"x-org-id": str(ORG)})
        add(f"{path_name}_json_body_ignored", path, query=query, body='{"org":900072,"crew_id":920001}', extra_headers={"Content-Type": "application/json"})
        add(f"{path_name}_query_org_ignored", path, query=query+[("org", str(OTHER)), ("org_id", str(OTHER))])
        add(f"{path_name}_uppercase_path", path.replace("crew", "Crew"), query=query)
    for i in range(1, 33):
        add(f"show_fixture_{i:02}", "/callboard/crew/show", query=[("crew_id", str(910000+i))])
    for i, value in enumerate(("", " ", "oops", "0", "-1", "999999", str(FOREIGN), "1.0", "+910001", "0910001", " 910001 ", "2147483648", "9223372036854775808", "1 OR 1=1", "1'", "²")):
        add(f"show_id_parse_{i}", "/callboard/crew/show", query=[("crew_id", value)])
    add("show_id_missing", "/callboard/crew/show")
    add("show_foreign_inverse", "/callboard/crew/show", org=OTHER, query=[("crew_id", str(FIRST))])
    add("show_empty_org", "/callboard/crew/show", org=EMPTY, query=[("crew_id", str(FIRST))])
    add("show_duplicate_id_valid_first", "/callboard/crew/show", query=[("crew_id", str(FIRST)), ("crew_id", str(FOREIGN))])
    add("show_duplicate_id_foreign_first", "/callboard/crew/show", query=[("crew_id", str(FOREIGN)), ("crew_id", str(FIRST))])
    add("list_duplicate_page", query=[("page", "2"), ("page", "1"), ("per_page", "3")])
    add("list_duplicate_size", query=[("per_page", "1"), ("per_page", "0")])
    add("list_unknown_filters", query=[("search", "nobody"), ("sort", "-rate"), ("crew_id", str(FOREIGN))])
    return result


class CrewContract(_support.CrewFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(GOLDEN.read_text())
        cls.requests = cases()
        fingerprint = hashlib.sha256(json.dumps(fixtures(), sort_keys=True).encode()).hexdigest()
        if cls.contract["fixture_sha256"] != fingerprint:
            raise AssertionError("Fixture changed; review before explicitly re-recording the contract")
        if {name: entry["request"] for name, entry in cls.contract["cases"].items()} != cls.requests:
            raise AssertionError("Request matrix changed; review before explicitly re-recording")
        cls.fuzz_contract = json.loads(FUZZ_GOLDEN.read_text())
        if cls.fuzz_contract["fixture_sha256"] != fingerprint:
            raise AssertionError("Fuzz fixture differs from the recorded fixture")
        cls.addClassCleanup(cls.cleanup_fixture)
        cls.install_fixture()


    def tearDown(self):
        self.assertEqual(database_state(), self.before, "Request changed DB rows: crew globally / six tables for fixture orgs")

    def test_committed_update_visible(self):
        initial = send(request("/callboard/crew/show", query=[("crew_id", str(FIRST))]))
        self.assertEqual(initial, self.contract["cases"]["show_fixture_01"]["response"],
                         f"Backend {BASE} is missing a compatible crew/show wrapper or its wire contract drifted")
        try:
            db(f"UPDATE tg_crew SET notes='changed after first read' WHERE id={FIRST};")
            show = json.loads(send(request("/callboard/crew/show", query=[("crew_id", str(FIRST))]))["body"])
            listing = json.loads(send(request("/callboard/crew/list"))["body"])
            self.assertNotEqual(show, json.loads(initial["body"]), "Live fixture change must be observable")
            self.assertEqual(show["data"]["notes"], "changed after first read")
            self.assertEqual(next(row for row in listing["data"]["crew"] if row["crew_id"] == FIRST)["notes"], "changed after first read")
        finally:
            db(f"UPDATE tg_crew SET notes='note 1' WHERE id={FIRST};")

    def test_recorded_frontend_reads(self):
        # Exercise the real recorded seed-org traffic against whatever committed
        # crew data currently exists, instead of freezing prior probe mutations.
        rows = self.before["tg_crew"]
        for line in (ROOT / "traffic/traffic.jsonl").read_text().splitlines():
            item = json.loads(line)
            if item["method"] != "GET" or not item["path"].startswith("/callboard/crew/"):
                continue
            with self.subTest(request=item):
                response = send(request(item["path"], org=item["org"], query=list((item["query"] or {}).items())))
                self.assertEqual(response["status"], 200)
                payload = json.loads(response["body"])
                if item["path"].endswith("/list"):
                    expected = [row["id"] for row in rows if row["org"] == item["org"]]
                    size = (item["query"] or {}).get("per_page", 25)
                    self.assertEqual(payload["data"]["total"], len(expected))
                    self.assertEqual([row["crew_id"] for row in payload["data"]["crew"]], expected[:size] if size else expected)
                else:
                    crew_id = item["query"]["crew_id"]
                    owned = any(row["id"] == crew_id and row["org"] == item["org"] for row in rows)
                    self.assertEqual(payload["result"], "ok" if owned else "fail")
                    if owned:
                        self.assertEqual(payload["data"]["crew_id"], crew_id)
                    else:
                        self.assertEqual(payload, {"error": "not found", "result": "fail"})


def attach_tests():
    for name in cases():
        def test(self, name=name):
            expected = self.contract["cases"][name]["response"]
            actual = send(self.requests[name])
            self.assertEqual(actual, expected, f"Wire contract drift in {name}")
            if self.requests[name]["method"] == "GET" and '"data"' in actual["body"]:
                payload = json.loads(actual["body"])
                values = payload["data"].get("crew", [payload["data"]])
                self.assertTrue(all(row["org"] == int(self.requests[name]["headers"].get("X-Org-Id", ORG)) for row in values))
                self.assertNotIn('"password"', actual["body"])
                self.assertNotIn("DO-NOT-EXPOSE", actual["body"])
        setattr(CrewContract, "test_contract_"+name, test)
    if FUZZ_GOLDEN.exists():
        corpus = json.loads(FUZZ_GOLDEN.read_text())
        for index, entry in enumerate(corpus["cases"]):
            def test_fuzz(self, index=index):
                entry = self.fuzz_contract["cases"][index]
                expected = self.fuzz_contract["responses"][entry["response_sha256"]]
                # Absolute redirect URLs echo the incoming Host. Hold that input
                # constant when comparing different backend ports.
                host = urlsplit(self.fuzz_contract["source"]).netloc
                self.assertEqual(send(entry["request"], host=host), expected, f"Fuzz contract drift: {entry['id']} ({entry['category']})")
            setattr(CrewContract, f"test_fuzz_{entry['id']}", test_fuzz)


attach_tests()


def record(replace=False):
    if BASE != "http://localhost:8091":
        raise SystemExit("Recording is restricted to the provided legacy service on localhost:8091")
    if GOLDEN.exists() and not replace:
        raise SystemExit("Contract already exists. Review changes before using --record --replace")
    # The recording uses the same fixture lifecycle as verification.
    try:
        CrewContract.install_fixture()
        entries = {name: {"request": spec, "response": send(spec)} for name, spec in cases().items()}
        if database_state() != CrewContract.before:
            raise AssertionError("Recording changed the database")
        data = dict(source=BASE, fixture_sha256=hashlib.sha256(json.dumps(fixtures(), sort_keys=True).encode()).hexdigest(), cases=entries)
        GOLDEN.write_text(json.dumps(data, indent=2, ensure_ascii=True)+"\n")
        print(f"Recorded {len(entries)} cases to {GOLDEN}")
    finally:
        CrewContract.cleanup_fixture()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--replace", action="store_true")
    args, remaining = parser.parse_known_args()
    BASE = args.base
    if args.record:
        record(args.replace)
    else:
        unittest.main(argv=[__file__]+remaining, verbosity=2)
