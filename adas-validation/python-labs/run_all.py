"""Run every independent lab, keeping going after a failed script."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Assertions disabled: remove -O or -OO")
    results = []
    for script in sorted((ROOT / "scripts").glob("tc*.py")):
        print(f"\n=== {script.stem} ===", flush=True)
        run = subprocess.run([sys.executable, str(script)], cwd=ROOT)
        results.append({"script": script.stem, "exit_code": run.returncode})
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "suite_summary.json").write_text(json.dumps(results, indent=2))
    passed = sum(r["exit_code"] == 0 for r in results)
    print(f"\n{passed}/{len(results)} labs passed")
    sys.exit(int(passed != len(results)))
