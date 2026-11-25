import re
from common import DATA, run_cases

RULES = {"DISK": r"no space left", "BUILD": r"compile error",
         "TIMEOUT": r"timed out|timeout"}

def classify(text):
    for label, pattern in RULES.items():
        if re.search(pattern, text, re.I):
            return label
    return "UNKNOWN"

def check(data):
    filename, expected = data
    actual = classify((DATA / filename).read_text(encoding="utf-8"))
    assert actual == expected, f"Expected {expected}, got {actual}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc19_jenkins_logs", [
        ("disk", ("jenkins_disk.txt", "DISK"), None),
        ("compiler", ("jenkins_build.txt", "BUILD"), None),
        ("timeout", ("jenkins_timeout.txt", "TIMEOUT"), None),
        ("unknown", ("jenkins_unknown.txt", "UNKNOWN"), None),
    ], check))
