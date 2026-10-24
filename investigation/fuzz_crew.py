"""Bounded, repeatable HTTP fuzz discovery against the legacy wave 1 reads.

python3 investigation/fuzz_crew.py
Captures once; refuses to overwrite its existing frozen corpus.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import crew_support as contract
import time

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261024
CORPUS = contract.FUZZ_GOLDEN
REPORT = ROOT / "investigation/crew-fuzz-report.json"
LOG = ROOT / "investigation/evidence/crew-fuzz-http.jsonl"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def generate():
    rng = random.Random(SEED)
    result, seen = [], set()
    def add(category, request):
        key = digest(request)
        if key not in seen:
            seen.add(key)
            result.append(dict(id=f"{len(result):04}", category=category, request=request))

    numeric = ["", " ", "\t", "\r\n", "0", "-0", "+0", "-1", "1", "2", "25", "32", "33",
               "0002", "+2", " 2 ", "1_0", "0x10", "1e2", "2.0", "NaN", "Infinity", "true", "null",
               "2147483647", "2147483648", "-2147483649", "9223372036854775807", "9223372036854775808",
               "١", "１２", "²", "\x00", "1 OR 1=1", "1'", '1"', "%31", "\\1", "1/2"]
    for parameter in ("page", "per_page", "crew_id"):
        endpoint = "show" if parameter == "crew_id" else "list"
        for value in numeric + ["9"*4300, "9"*4301, "9"*5000]:
            add("value-boundary-"+parameter, contract.request(f"/callboard/crew/{endpoint}", query=[(parameter, value)]))
    for endpoint in ("list", "show"):
        path = f"/callboard/crew/{endpoint}"
        valid = [["crew_id", str(contract.FIRST)]] if endpoint == "show" else []
        for org in ("000900071", "900071\t", "\t900071", "900071  ", "900071,900072", "900071, 900072", "0xDBB E7", "²", "9"*5000):
            add("org-header", contract.request(path, org=org, query=valid))
        for pairs in [ [["X-Org-Id", str(contract.ORG)], ["X-Org-Id", str(contract.OTHER)]],
                       [["X-Org-Id", str(contract.OTHER)], ["X-Org-Id", str(contract.ORG)]],
                       [["X-Org-Id", str(contract.ORG)], ["x-org-id", str(contract.ORG)]],
                       [["X-Org-Id", ""], ["X-Org-Id", str(contract.ORG)]] ]:
            item = contract.request(path, query=valid)
            item["header_pairs"] = pairs
            add("duplicate-org-header", item)
        for method in ("TRACE", "BREW"):
            add("unusual-method", contract.request(path, query=valid, method=method))
        for content_type, body in [("application/x-www-form-urlencoded", "crew_id=920001&org=900072"),
                                   ("application/json", "{invalid"), ("text/plain", "null")]:
            add("get-body", contract.request(path, query=valid, body=body, extra_headers={"Content-Type": content_type}))
        for headers in ({"Accept": "application/xml"}, {"Accept-Encoding": "gzip"},
                        {"If-None-Match": '"anything"'}, {"Range": "bytes=0-2"}):
            add("response-negotiation", contract.request(path, query=valid, extra_headers=headers))
        parameter = "crew_id" if endpoint == "show" else "page"
        value = str(contract.FIRST) if endpoint == "show" else "2"
        raw_values = [f"{parameter}={value}", f"{parameter}", f"{parameter}=", f"{parameter}[]=1",
                      f"{parameter}=+{value}", f"{parameter}=%2B{value}", f"{parameter}=%00",
                      f"{parameter}=%FF", f"{parameter}=%C0%AF", f"{parameter}=%", f"{parameter}=%GG",
                      f"{parameter}={value};{parameter}=bad", f"{parameter}=bad&{parameter}={value}",
                      f"{parameter}=&{parameter}={value}", f"%{ord(parameter[0]):02x}{parameter[1:]}={value}"]
        for raw in raw_values:
            item = contract.request(path)
            item["raw_query"] = raw
            add("raw-query", item)
        for changed in (path.replace("crew", "%63rew"), path.replace("/crew/", "/crew%2F"),
                        path.replace("/crew/", "//crew/"), path.replace("/crew/", "/crew/./"),
                        path+"%2F", path+";anything", path.upper()):
            add("raw-path", contract.request(changed, query=valid))
        for org in (None, "oops", str(contract.OTHER)):
            add("error-precedence", contract.request(path, org=org, query=[[parameter, "bad"]]))

    # Random combinations mix known-valid values with invalid/malicious-looking
    # values. Fixed seed + persisted requests make every discovery replayable.
    before_random = len(result)
    while len(result) < before_random+600:
        endpoint = rng.choice(("list", "show"))
        if endpoint == "list":
            query = [["page", rng.choice(numeric)], ["per_page", rng.choice(numeric)]]
            if rng.random() < .35:
                query.append([rng.choice(("page", "per_page")), rng.choice(("", "1", "0", "bad"))])
        else:
            query = [["crew_id", rng.choice([str(contract.FIRST+i) for i in range(32)]+numeric+[str(contract.FOREIGN)])]]
            if rng.random() < .35:
                query.append(["crew_id", rng.choice((str(contract.FIRST), str(contract.FOREIGN), "bad", ""))])
            query.append(["unused", "".join(rng.choices("ab09&%+'雪", k=rng.randrange(1, 12)))])
        org = rng.choice([contract.ORG]*6+[contract.OTHER, contract.EMPTY, None, "oops", "0900071", "+900071"])
        add("seeded-random-"+endpoint, contract.request(f"/callboard/crew/{endpoint}", org=org, query=query,
            method=rng.choice(["GET"]*12+["HEAD", "OPTIONS", "POST"])))
    for value in ("910_001", hex(contract.FIRST), oct(contract.FIRST), bin(contract.FIRST), "+000910001", "9__10001"):
        add("valid-id-format-followup", contract.request("/callboard/crew/show", query=[["crew_id", value]]))
    for query in ([["page", "bad-page"], ["per_page", "bad-size"]], [["page", "1"], ["per_page", "bad-size"]]):
        add("pagination-error-precedence", contract.request("/callboard/crew/list", query=query))
    return result


def main(extend=False):
    if not extend and (CORPUS.exists() or LOG.exists() or REPORT.exists()):
        raise SystemExit("Fuzz evidence already exists; preserve it and review changes before a new capture")
    prior = json.loads(CORPUS.read_text()) if extend else None
    cases = generate()
    if prior:
        if len(cases) <= len(prior["cases"]):
            raise SystemExit("Append-only extension requires additional cases")
        for old, new in zip(prior["cases"], cases):
            if {key: value for key, value in old.items() if key != "response_sha256"} != new:
                raise SystemExit(f"Previously frozen fuzz input changed: {old['id']}")
    baseline_sha = hashlib.sha256(contract.GOLDEN.read_bytes()).hexdigest()
    captured_at = datetime.now(timezone.utc).isoformat()
    responses, logs, outcomes, statuses = {}, [], Counter(), Counter()
    started = time.monotonic()
    try:
        contract.CrewFixture.install_fixture()
        for index, case in enumerate(cases):
            before = time.monotonic()
            response, headers = contract.send(case["request"], include_transport=True)
            if prior and index < len(prior["cases"]):
                old = prior["cases"][index]
                if response != prior["responses"][old["response_sha256"]]:
                    raise AssertionError(f"Previously frozen fuzz response drifted: {old['id']}")
            response_sha = digest(response)
            responses[response_sha] = response
            case["response_sha256"] = response_sha
            logs.append(dict(id=case["id"], category=case["category"], response_sha256=response_sha,
                captured_at=datetime.now(timezone.utc).isoformat(), elapsed_ms=round((time.monotonic()-before)*1000, 3),
                raw_response_headers=headers))
            statuses[str(response["status"])] += 1
            try:
                payload = json.loads(response["body"])
                outcome = payload.get("result", "json-without-result")
            except (ValueError, AttributeError):
                outcome = "empty-body" if not response["body"] else "non-json"
            outcomes[outcome] += 1
            if (index+1) % 25 == 0:
                if contract.database_state() != contract.CrewFixture.before:
                    raise AssertionError(f"DB side effect in batch ending at {case['id']}")
            if (index+1) % 100 == 0:
                print(f"Captured {index+1}/{len(cases)}", flush=True)
        if contract.database_state() != contract.CrewFixture.before:
            raise AssertionError("DB side effect at end of capture")
        # Verify every captured response a second time before freezing evidence.
        for case in cases:
            if contract.send(case["request"]) != responses[case["response_sha256"]]:
                raise AssertionError(f"Non-repeatable response: {case['id']}")
        if contract.database_state() != contract.CrewFixture.before:
            raise AssertionError("DB side effect during repeatability pass")
        if hashlib.sha256(contract.GOLDEN.read_bytes()).hexdigest() != baseline_sha:
            raise AssertionError("Original characterization baseline changed")
        data = dict(source="http://localhost:8091", source_image="ghcr.io/pressw-llc/showcall-callboard:r129e453a77",
            seed=SEED, captured_at=captured_at, fixture_sha256=digest(contract.fixtures()),
            original_contract_sha256=baseline_sha, cases=cases, responses=responses)
        CORPUS.write_text(json.dumps(data, indent=2, ensure_ascii=True)+"\n")
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a" if extend else "w") as stream:
            stream.write("".join(json.dumps(row)+"\n" for row in logs))
        report = dict(captured_at=captured_at, seed=SEED, cases=len(cases), repeated_requests=len(cases),
            unique_responses=len(responses), http_statuses=dict(statuses), outcomes=dict(outcomes),
            categories=dict(Counter(case["category"] for case in cases)),
            db_checks="Every 25 requests and after each full pass; crew globally, all six tables for fixture orgs",
            original_contract_sha256=baseline_sha, elapsed_seconds=round(time.monotonic()-started, 3))
        REPORT.write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report, indent=2))
    finally:
        contract.CrewFixture.cleanup_fixture()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extend", action="store_true", help="Append new inputs, requiring every existing input/response to stay unchanged")
    main(parser.parse_args().extend)
