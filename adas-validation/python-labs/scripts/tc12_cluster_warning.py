from common import run_cases

def check(row):
    expected = row["ignition"] and not row["belt"]
    assert row["warning"] == expected, (
        f"Expected warning={expected}, observed={row['warning']}")

if __name__ == "__main__":
    def row(ignition, belt, warning):
        return dict(ignition=ignition, belt=belt, warning=warning)
    raise SystemExit(run_cases("tc12_cluster_warning", [
        ("off/unbelted", row(False, False, False), None),
        ("off/belted", row(False, True, False), None),
        ("on/belted", row(True, True, False), None),
        ("on/unbelted", row(True, False, True), None),
        ("missing warning", row(True, False, False), AssertionError),
    ], check))
