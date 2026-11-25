import logging
from statistics import mean
from common import run_cases

def check(timestamps_ms):
    assert len(timestamps_ms) >= 2, "Need at least two frames"
    intervals = [b - a for a, b in zip(timestamps_ms,
                                      timestamps_ms[1:])]
    logging.getLogger("tc05_can_cycle").debug(
        "Intervals %s; mean %.1f ms", intervals, mean(intervals))
    for delta in intervals:
        assert 95 <= delta <= 105, f"Cycle time {delta} ms"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc05_can_cycle", [
        ("nominal", [0, 100, 201, 300], None),
        ("late frame", [0, 100, 220], AssertionError),
        ("too short", [0], AssertionError),
    ], check))
