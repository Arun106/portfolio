"""Exports latest completed run per release and unique Jira bug snapshots."""
import json
import os
from pathlib import Path
from collections import Counter
from http.server import BaseHTTPRequestHandler,HTTPServer
ROOT=Path(os.environ.get("ARTIFACT_ROOT","artifacts"))

def metrics(root=ROOT):
    lines=[]
    def emit(name,labels,value):
        labeltext=",".join(k+"="+json.dumps(str(v)) for k,v in labels.items())
        lines.append(f"{name}{{{labeltext}}} {value}")
    latest={}
    for path in root.glob("*/*/summary.json"):
        obj=json.loads(path.read_text())
        if obj["release"] not in latest or obj["timestamp"]>latest[obj["release"]]["timestamp"]:latest[obj["release"]]=obj
    for release,obj in sorted(latest.items()):
        labels={"release":release,"mode":obj["mode"]}
        for verdict,count in obj["verdicts"].items():emit("adas_test_cases",dict(labels,verdict=verdict),count)
        for field in ("requirement_total","requirement_covered","requirement_verified"):
            emit("adas_"+field,labels,obj[field])
        emit("adas_full_regression",labels,int(obj["full_regression"]))
    for path in root.glob("bugs/*.json"):
        obj=json.loads(path.read_text());source=obj.get("source","unknown")
        unique={i["key"]:i for i in obj["issues"]}
        emit("adas_bug_snapshot_available",{"release":obj["release"],"source":source},1)
        emit("adas_bugs_reported",{"release":obj["release"],"source":source},len(unique))
        counts=Counter(((i["fields"].get("priority") or {}).get("name","Unspecified"),
            (i["fields"].get("status") or {}).get("statusCategory",{}).get("key","unknown")) for i in unique.values())
        for (severity,status),value in counts.items():emit("adas_bugs",{"release":obj["release"],"source":source,"severity":severity,"status":status},value)
    return "\n".join(lines)+"\n"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/metrics","/health"):self.send_error(404);return
        try:body=(metrics() if self.path=="/metrics" else "ok\n").encode()
        except Exception:self.send_error(503,"invalid artifact snapshot");return
        self.send_response(200);self.send_header("Content-Type","text/plain; version=0.0.4")
        self.end_headers();self.wfile.write(body)
if __name__=="__main__":HTTPServer(("0.0.0.0",8080),Handler).serve_forever()
