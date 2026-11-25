import subprocess
import sys
from common import TestError, run_cases

class BuildError(TestError):
    pass

def check(success):
    program = ("print('BUILD_OK')" if success else
        "import sys; print('compile error', file=sys.stderr); sys.exit(2)")
    result = subprocess.run([sys.executable, "-c", program],
        capture_output=True, text=True, timeout=5)
    if result.returncode:
        raise BuildError(result.stderr.strip())
    assert "BUILD_OK" in result.stdout, "Missing build marker"

if __name__ == "__main__":
    raise SystemExit(run_cases("tc18_build", [
        ("build success", True, None),
        ("compiler error", False, BuildError),
    ], check))
