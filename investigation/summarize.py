"""Consolidate local DB snapshots into a lossless, smaller evidence timeline."""
import json
from pathlib import Path

DIRECTORY = Path(__file__).parent / "evidence"


def main():
    captures = []
    for path in DIRECTORY.glob("*.json"):
        if path.name == "db-timeline.json":
            continue
        capture = json.loads(path.read_text())
        captures.append((capture["captured_at"], path.stem, capture["tables"]))
    captures.sort()
    if not captures:
        raise SystemExit("No local snapshots; first run probe.py --snapshot NAME")
    at, label, previous = captures[0]
    timeline = {"baseline": {"label": label, "captured_at": at, "tables": previous}, "transitions": []}
    for at, label, current in captures[1:]:
        changes = {}
        for table, rows in current.items():
            old = {row["id"]: row for row in previous[table]}
            new = {row["id"]: row for row in rows}
            added = [row for key, row in new.items() if key not in old]
            removed = [row for key, row in old.items() if key not in new]
            updated = [
                {"id": key, "fields": {field: {"before": old[key].get(field), "after": value}
                    for field, value in row.items() if old[key].get(field) != value}}
                for key, row in new.items() if key in old and old[key] != row
            ]
            if added or removed or updated:
                changes[table] = {"added": added, "removed": removed, "updated": updated}
        timeline["transitions"].append({"from": timeline["transitions"][-1]["to"] if timeline["transitions"] else timeline["baseline"]["label"], "to": label, "captured_at": at, "changes": changes})
        print(label, {table: {kind: len(rows) for kind, rows in delta.items()} for table, delta in changes.items()})
        previous = current
    (DIRECTORY / "db-timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")


if __name__ == "__main__":
    main()
