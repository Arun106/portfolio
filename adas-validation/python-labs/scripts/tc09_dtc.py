from common import run_cases

ALLOWED = {"U0001"}  # Example bench-specific allowlist.

def check(dtcs):
    active = {d["code"] for d in dtcs if d["active"]}
    unexpected = active - ALLOWED
    assert not unexpected, f"Unexpected active DTCs: {unexpected}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc09_dtc", [
        ("clean", [], None),
        ("allowed", [{"code": "U0001", "active": True}], None),
        ("fault", [{"code": "P0001", "active": True}], AssertionError),
    ], check))
