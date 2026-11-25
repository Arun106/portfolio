from common import TestError, run_cases

class VoltageError(TestError):
    pass

def check(voltage):
    # Runtime validation is never dependent on assert.
    if not 9 <= voltage <= 16:
        raise VoltageError(f"{voltage} V outside 9-16 V")
    assert 9 <= voltage <= 16, "Accepted invalid voltage"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc02_voltage", [
        ("below", 8.99, VoltageError),
        ("lower boundary", 9, None),
        ("nominal", 12, None),
        ("upper boundary", 16, None),
        ("above", 16.01, VoltageError),
    ], check))
