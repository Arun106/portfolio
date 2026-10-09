"""Generate three actual local demo executions and labelled illustrative defects."""
import json
from .run import ROOT,run

def main():
    summaries=[]
    for release in ("R1.0","R1.1","R1.2"):
        obj,path=run(release)
        summaries.append(obj)
        issues=[] if release!="R1.1" else [{"key":"DEMO-BUG-001","fields":{
            "priority":{"name":"High"},"status":{"name":"Resolved","statusCategory":{"key":"done"}},
            "versions":[{"name":"R1.1"}],"fixVersions":[{"name":"R1.2"}]}}]
        bugs=ROOT/"artifacts/bugs";bugs.mkdir(exist_ok=True)
        (bugs/(release+".json")).write_text(json.dumps({"release":release,"source":"demo","issues":issues},indent=2))
    (ROOT/"data/demo-results.json").write_text(json.dumps(summaries,indent=2))
if __name__=="__main__":main()
