import logging
from common import TestError, run_cases

class SignalTimeoutError(TestError):
    pass

def check(frames):
    log = logging.getLogger("tc04_can_timeout")
    for attempt, frame in enumerate(frames[:3], start=1):
        log.debug("Attempt %s: %r", attempt, frame)
        if frame is not None:
            assert frame == "SPEED", "Wrong frame"
            return
        log.warning("No frame yet")
    raise SignalTimeoutError("Three attempts exhausted")

if __name__ == "__main__":
    raise SystemExit(run_cases("tc04_can_timeout", [
        ("immediate", ["SPEED"], None),
        ("retry", [None, "SPEED"], None),
        ("timeout", [None, None, None], SignalTimeoutError),
    ], check))
