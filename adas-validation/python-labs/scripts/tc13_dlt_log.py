import re
from common import DATA, run_cases

PATTERN = re.compile(r"^\S+\s+(ERROR|FATAL)\b")

def check(filename):
    with (DATA / filename).open(encoding="utf-8") as stream:
        errors = [(i, line.strip()) for i, line in enumerate(stream, 1)
                  if PATTERN.search(line)]
    assert not errors, f"Errors: {errors}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc13_dlt_log", [
        ("clean", "dlt_clean.txt", None),
        ("error", "dlt_fault.txt", AssertionError),
        ("missing file", "missing.txt", FileNotFoundError),
    ], check))
