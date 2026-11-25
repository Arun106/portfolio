import re
from common import run_cases

def check(data):
    actual, expected = data
    assert re.fullmatch(r"\d+\.\d+\.\d+", actual), "Bad format"
    assert actual == expected, f"Expected {expected}, got {actual}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc06_software_version", [
        ("correct", ("2.4.1", "2.4.1"), None),
        ("old release", ("2.3.1", "2.4.1"), AssertionError),
        ("bad format", ("v2.4", "2.4.1"), AssertionError),
    ], check))
