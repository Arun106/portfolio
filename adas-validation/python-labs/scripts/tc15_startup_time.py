import time
from unittest.mock import patch
from common import run_cases

def measure_startup():
    start = time.monotonic()
    # In real code, trigger ECU and wait for ready here.
    return (time.monotonic() - start) * 1000

def check(seconds):
    with patch("time.monotonic", side_effect=[0.0, seconds]):
        elapsed_ms = measure_startup()
    assert 0 <= elapsed_ms <= 1500, f"Startup: {elapsed_ms:.1f} ms"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc15_startup_time", [
        ("fast", 1.2, None), ("boundary", 1.5, None),
        ("slow", 1.7, AssertionError),
    ], check))
