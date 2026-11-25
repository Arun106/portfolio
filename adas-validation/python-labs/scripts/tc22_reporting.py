import csv
import json
from common import REPORTS, run_cases

def check(rows):
    assert rows and all(r["verdict"] in {"PASS", "FAIL"} for r in rows)
    json_path = REPORTS / "example_results.json"
    csv_path = REPORTS / "example_results.csv"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "verdict"])
        writer.writeheader()
        writer.writerows(rows)
    assert json.loads(json_path.read_text(encoding="utf-8")) == rows
    with csv_path.open(newline="", encoding="utf-8") as stream:
        assert list(csv.DictReader(stream)) == rows

if __name__ == "__main__":
    raise SystemExit(run_cases("tc22_reporting", [
        ("valid", [{"id": "TC01", "verdict": "PASS"},
                   {"id": "TC02", "verdict": "FAIL"}], None),
        ("invalid", [{"id": "TC03", "verdict": "MAYBE"}], AssertionError),
    ], check))
