"""Atomic run-directory publication for Grafana's read-only artifact volume."""
import argparse
import shutil
import uuid
from pathlib import Path
from .run import ROOT

def publish(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    for summary in (ROOT/"artifacts").glob("*/*/summary.json"):
        source=summary.parent
        dest=destination/source.parent.name/source.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():continue
        temp=dest.with_name("staging-"+uuid.uuid4().hex)
        shutil.copytree(source,temp);temp.rename(dest)
    for source in (ROOT/"artifacts/bugs").glob("*.json"):
        dest=destination/"bugs"/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_suffix(".tmp");shutil.copyfile(source,temp);temp.replace(dest)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--destination",required=True)
    publish(p.parse_args().destination)
