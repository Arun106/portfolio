from common import run_cases

def check(samples):
    assert samples, "No CAN samples"
    for index, frame in enumerate(samples):
        speed = frame["speed_kmh"]
        assert 0 <= speed <= 250, f"Sample {index}: {speed}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc03_can_range", [
        ("normal", [{"speed_kmh": 0}, {"speed_kmh": 120}], None),
        ("range fault", [{"speed_kmh": 251}], AssertionError),
        ("empty", [], AssertionError),
    ], check))
