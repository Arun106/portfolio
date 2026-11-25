from common import TestError, run_cases

class RecoveryError(TestError):
    pass

def check(states):
    assert states[0] == (0, "RESET"), "Reset not observed"
    for elapsed_ms, state in states:
        if elapsed_ms > 3000:
            break
        if state == "READY":
            return
    raise RecoveryError("ECU did not recover by 3000 ms")

if __name__ == "__main__":
    raise SystemExit(run_cases("tc10_reset_recovery", [
        ("recovered", [(0, "RESET"), (2000, "READY")], None),
        ("late", [(0, "RESET"), (4000, "READY")], RecoveryError),
        ("no reset", [(0, "READY")], AssertionError),
    ], check))
