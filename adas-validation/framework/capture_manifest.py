"""Bench adapter helper: identify and hash freshly captured evidence."""
import argparse
import hashlib
import json
from pathlib import Path

def create(root,release,firmware):
    root=Path(root)
    manifest={"release":release,"firmware_sha256":hashlib.sha256(Path(firmware).read_bytes()).hexdigest(),
        "captures":{}}
    for path in root.glob("ADAS-TC-*"):
        manifest["captures"][path.name]={name:hashlib.sha256((path/name).read_bytes()).hexdigest()
            for name in ("capture.blf","capture.dlt") if (path/name).is_file()}
    if not manifest["captures"]:raise ValueError("no captures")
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2))
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--release",required=True);p.add_argument("--firmware",required=True)
    a=p.parse_args();create(a.root,a.release,a.firmware)
