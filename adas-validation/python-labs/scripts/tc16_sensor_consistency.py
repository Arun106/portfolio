from common import run_cases

def check(data):
    first, second = data
    assert len(first) == len(second) and first, "Stream length mismatch"
    for i, (a, b) in enumerate(zip(first, second)):
        assert abs(a - b) <= 0.5, f"Mismatch at sample {i}: {a}, {b}"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc16_sensor_consistency", [
        ("consistent", ([1, 2], [1.2, 2.3]), None),
        ("deviation", ([1, 2], [1, 3]), AssertionError),
        ("length fault", ([1, 2], [1]), AssertionError),
    ], check))
