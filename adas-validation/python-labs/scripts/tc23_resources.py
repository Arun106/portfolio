from types import SimpleNamespace
from unittest.mock import patch
import psutil
from common import run_cases

def check(data):
    cpu, ram = data
    with patch("psutil.cpu_percent", return_value=cpu), \
         patch("psutil.virtual_memory", return_value=SimpleNamespace(percent=ram)):
        actual_cpu = psutil.cpu_percent(interval=0.1)
        actual_ram = psutil.virtual_memory().percent
    assert actual_cpu <= 85, f"CPU utilization {actual_cpu}%"
    assert actual_ram <= 90, f"RAM utilization {actual_ram}%"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc23_resources", [
        ("normal", (40, 60), None),
        ("CPU overload", (95, 60), AssertionError),
        ("RAM overload", (40, 95), AssertionError),
    ], check))
