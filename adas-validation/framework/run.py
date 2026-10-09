import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from .simulator import simulate
from .oracle import evaluate

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    with (ROOT/"data"/name).open(newline="") as f:
        return list(csv.DictReader(f))

def validate_traceability():
    reqs, specs, cases = load("requirements.csv"), load("test_specifications.csv"), load("test_cases.csv")
    def index(rows,key):
        result={r[key]:r for r in rows}
        if len(result)!=len(rows) or not all(result):
            raise ValueError("empty/duplicate IDs: "+key)
        return result
    ri, si, ci = index(reqs,"requirement_id"), index(specs,"spec_id"), index(cases,"test_id")
    for s in specs:
        if s["requirement_id"] not in ri: raise ValueError("orphan specification")
    for c in cases:
        if c["spec_id"] not in si or c["requirement_id"]!=si[c["spec_id"]]["requirement_id"]:
            raise ValueError("inconsistent requirement/test link")
        if float(c["deadline_ms"])<0: raise ValueError("negative deadline")
    if set(ri)-{c["requirement_id"] for c in cases}: raise ValueError("uncovered requirement")
    if set(si)-{c["spec_id"] for c in cases}: raise ValueError("uncovered specification")
    return reqs,specs,cases

def run(release, mode="demo", capture_root=None, selected=None, output=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", release): raise ValueError("invalid release identifier")
    reqs,specs,cases = validate_traceability()
    if selected is not None:
        unknown = set(selected)-{c["test_id"] for c in cases}
        if unknown or not selected: raise ValueError("empty/unknown test selection")
        cases = [c for c in cases if c["test_id"] in selected]
    if mode=="demo" and release not in ("R1.0","R1.1","R1.2"): raise ValueError("unknown demo release")
    capture_manifest=None
    if mode=="replay":
        if capture_root is None:raise ValueError("replay requires capture-root")
        capture_manifest=json.loads((Path(capture_root)/"manifest.json").read_text())
        if capture_manifest.get("release")!=release:raise ValueError("capture release mismatch")
        if not re.fullmatch("[0-9a-f]{64}",capture_manifest.get("firmware_sha256","")):
            raise ValueError("capture manifest must identify immutable firmware")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"-"+uuid.uuid4().hex[:8]
    out=Path(output or ROOT/"artifacts")/release/run_id
    out.mkdir(parents=True)
    results=[]
    for c in cases:
        folder=out/c["test_id"]; folder.mkdir()
        if mode=="demo":
            simulate(c,release,folder)
        else:
            if capture_root is None: raise ValueError("replay requires capture-root")
            source=Path(capture_root)/c["test_id"]
            for name in ("capture.blf","capture.dlt"):
                if (source/name).exists():
                    digest=hashlib.sha256((source/name).read_bytes()).hexdigest()
                    if capture_manifest.get("captures",{}).get(c["test_id"],{}).get(name)!=digest:
                        raise ValueError("capture hash mismatch: "+c["test_id"]+"/"+name)
                    shutil.copyfile(source/name,folder/name)
        result=evaluate(c,folder)
        evidence = {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()}
        results.append(dict(c,**result,evidence=evidence))
    verdicts={v:sum(r["verdict"]==v for r in results) for v in ("PASS","FAIL","ERROR")}
    passed={r["requirement_id"] for r in results if r["verdict"]=="PASS"}
    covered={r["requirement_id"] for r in results}
    verified={rid for rid in covered if all(r["verdict"]=="PASS" for r in results if r["requirement_id"]==rid)}
    # A subset cannot claim full requirement verification.
    full_cases=load("test_cases.csv")
    complete={rid for rid in covered if {c["test_id"] for c in full_cases if c["requirement_id"]==rid} <= {r["test_id"] for r in results}}
    verified &= complete
    summary=dict(release=release,run_id=run_id,mode=mode,commit=os.getenv("GIT_COMMIT","local-uncommitted"),
        timestamp=datetime.now(timezone.utc).isoformat(),verdicts=verdicts,total=len(results),
        requirement_total=len(reqs),requirement_covered=len(covered),requirement_verified=len(verified),
        full_regression=len(results)==len(full_cases),results=results)
    if capture_manifest is not None:summary["capture_manifest"]=capture_manifest
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    with (out/"traceability.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["requirement_id","spec_id","test_id","release","run_id","verdict","latency_ms","reason"])
        w.writeheader()
        for r in results: w.writerow({**{k:r[k] for k in ("requirement_id","spec_id","test_id","verdict","latency_ms","reason")},"release":release,"run_id":run_id})
    suite=ET.Element("testsuite",name="ADAS-"+release,tests=str(len(results)),failures=str(verdicts["FAIL"]),errors=str(verdicts["ERROR"]))
    for r in results:
        t=ET.SubElement(suite,"testcase",classname="adas."+r["requirement_id"],name=r["test_id"])
        props=ET.SubElement(t,"properties")
        for key in ("requirement_id","spec_id","jira_key"):
            ET.SubElement(props,"property",name=key,value=r[key])
        if r["verdict"]!="PASS": ET.SubElement(t,"failure" if r["verdict"]=="FAIL" else "error",message=r["reason"])
    ET.ElementTree(suite).write(out/"junit.xml",encoding="utf-8",xml_declaration=True)
    xray={"info":{"summary":f"ADAS {release} {run_id}","description":f"{mode} evidence; commit {summary['commit']}"},
        "tests":[{"testKey":r["jira_key"],"status":"PASSED" if r["verdict"]=="PASS" else "FAILED" if r["verdict"]=="FAIL" else "TODO",
                  "comment":r["reason"]+"; "+r["test_id"]} for r in results]}
    (out/"xray-results.json").write_text(json.dumps(xray,indent=2))
    print(json.dumps({k:summary[k] for k in ("release","run_id","verdicts","requirement_verified")}))
    return summary,out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--release",required=True);p.add_argument("--mode",choices=["demo","replay"],default="demo")
    p.add_argument("--capture-root");p.add_argument("--suite-file");p.add_argument("--output")
    args=p.parse_args()
    selected=json.loads(Path(args.suite_file).read_text())["test_ids"] if args.suite_file else None
    summary,_=run(args.release,args.mode,args.capture_root,selected,args.output)
    return 1 if summary["verdicts"]["FAIL"] or summary["verdicts"]["ERROR"] else 0

if __name__=="__main__":sys.exit(main())
