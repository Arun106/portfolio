import logging
from dataclasses import dataclass
from common import TestError, run_cases

class TestBenchError(TestError):
    pass

@dataclass
class Bench:
    power: bool
    network: bool
    can: bool

    def verify(self):
        failed = [k for k, v in vars(self).items() if not v]
        if failed:
            logging.getLogger("tc17_bench_health").critical("Bench unavailable: %s", failed)
            raise TestBenchError(str(failed))

def check(bench):
    bench.verify()

if __name__ == "__main__":
    raise SystemExit(run_cases("tc17_bench_health", [
        ("healthy", Bench(True, True, True), None),
        ("network down", Bench(True, False, True), TestBenchError),
    ], check))
