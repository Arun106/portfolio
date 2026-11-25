import subprocess
import sys
import re
from common import TestError, run_cases

class FlashingError(TestError):
    pass

def check(data):
    code, message = data
    # Safe fake flasher: does not touch hardware.
    result = subprocess.run([sys.executable, "-c",
        f"print({message!r}); raise SystemExit({code})"],
        capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        raise FlashingError(f"Flasher exit {result.returncode}")
    assert re.search(r"^FLASH_OK$", result.stdout, re.M), result.stdout

if __name__ == "__main__":
    raise SystemExit(run_cases("tc07_flashing", [
        ("success", (0, "FLASH_OK"), None),
        ("tool error", (1, "FLASH_FAIL"), FlashingError),
        ("missing marker", (0, "UNKNOWN"), AssertionError),
    ], check))
