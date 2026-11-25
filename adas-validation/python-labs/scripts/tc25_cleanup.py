from unittest.mock import Mock
from common import TestError, run_cases

class InjectedFailure(TestError):
    pass

def execute(bench, fail):
    bench.reserve()
    try:
        if fail:
            raise InjectedFailure("Injected test failure")
    finally:
        bench.release()

def check(fail):
    bench = Mock()
    try:
        execute(bench, fail)
    finally:
        bench.reserve.assert_called_once()
        bench.release.assert_called_once()

if __name__ == "__main__":
    raise SystemExit(run_cases("tc25_cleanup", [
        ("success cleanup", False, None),
        ("failure cleanup", True, InjectedFailure),
    ], check))
