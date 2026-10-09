"""Jira Cloud: mapped suite selection and unique bug snapshots. No issue creation."""
import argparse
import base64
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from .run import load

def request(path,payload=None):
    base=os.environ["JIRA_URL"].rstrip("/")
    if urlsplit(base).scheme!="https": raise ValueError("Jira URL must use HTTPS")
    token=base64.b64encode((os.environ["JIRA_EMAIL"]+":"+os.environ["JIRA_TOKEN"]).encode()).decode()
    req=Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization":"Basic "+token,"Content-Type":"application/json","Accept":"application/json"})
    with urlopen(req,timeout=30) as response:return json.load(response)

def suite(key):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*-\d+",key):raise ValueError("invalid suite key")
    # Explicit Jira issue links to Test issues, mapped to local reviewed test IDs.
    issue=request("/rest/api/3/issue/"+key+"?fields=issuelinks")
    linked={link[direction]["key"] for link in issue["fields"]["issuelinks"]
        for direction in ("inwardIssue","outwardIssue") if direction in link}
    mapping={c["jira_key"]:c["test_id"] for c in load("test_cases.csv")}
    selected=sorted(mapping[k] for k in linked if k in mapping)
    if not selected:raise ValueError("suite has no mapped Test issues")
    return {"suite_key":key,"test_ids":selected,"unmapped_linked_issues":sorted(linked-set(mapping))}

def bugs(project,release):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*",project):raise ValueError("invalid project")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}",release):raise ValueError("invalid release")
    # Affects Version is the release where the bug is observed; Fix Version means remediation.
    jql=f'project = {project} AND issuetype = Bug AND affectedVersion = "{release}"'
    result={};token=None
    while True:
        body={"jql":jql,"maxResults":100,"fields":["priority","status","versions","fixVersions"]}
        if token:body["nextPageToken"]=token
        page=request("/rest/api/3/search/jql",body)
        for issue in page.get("issues",[]):result[issue["key"]]=issue
        next_token=page.get("nextPageToken")
        if page.get("isLast",False) or not next_token:break
        if next_token==token:raise ValueError("Jira pagination did not advance")
        token=next_token
    return {"release":release,"source":"jira","jql":jql,"issues":list(result.values())}

def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=["suite","bugs"])
    p.add_argument("--key");p.add_argument("--project");p.add_argument("--release");p.add_argument("--out",required=True)
    a=p.parse_args()
    obj=suite(a.key) if a.action=="suite" else bugs(a.project,a.release)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_suffix(".tmp");temp.write_text(json.dumps(obj,indent=2));temp.replace(dest)
if __name__=="__main__":main()
