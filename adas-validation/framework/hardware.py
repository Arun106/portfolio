"""Trusted bench-side adapter contract. No default firmware build or flash command."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument("--release",required=True);a=p.parse_args()
    path=os.environ.get("ADAS_HIL_CONFIG")
    if not path:raise SystemExit("HIL blocked: set ADAS_HIL_CONFIG to reviewed bench-side JSON")
    cfg=json.loads(Path(path).read_text())
    required=("build","preflight","flash","verify_identity","capture_and_execute","teardown")
    if any(not isinstance(cfg.get(k),list) or not cfg[k] or not all(isinstance(x,str) for x in cfg[k]) for k in required):
        raise SystemExit("Every adapter must be a nonempty argv list")
    # Environment passes the release without shell interpolation.
    env=dict(os.environ,ADAS_RELEASE=a.release)
    capture_root=Path("artifacts/hil-captures")
    if capture_root.exists():shutil.rmtree(capture_root)
    try:
        for stage in required[:-1]:
            subprocess.run(cfg[stage],check=True,timeout=600,env=env)
        manifest=json.loads((capture_root/"manifest.json").read_text())
        if manifest.get("release")!=a.release:
            raise ValueError("captured release identity mismatch")
        if not isinstance(manifest.get("firmware_sha256"),str) or len(manifest["firmware_sha256"])!=64:
            raise ValueError("missing firmware identity hash")
    finally:
        subprocess.run(cfg["teardown"],check=True,timeout=60,env=env)
if __name__=="__main__":main()
