import json
import shutil
from pathlib import Path
import pytest
from framework.run import validate_traceability,run
from framework.simulator import simulate
from framework.oracle import evaluate
from framework.logs import read_blf,read_dlt,write_blf
from framework import jira
from monitoring.exporter import metrics

def case(scenario="brake"):
    return next(c for c in validate_traceability()[2] if c["scenario"]==scenario and c["signal"]=="Brake")

def test_baseline_and_regression_and_fix(tmp_path):
    good,_=run("R1.0",output=tmp_path)
    bad,_=run("R1.1",output=tmp_path)
    fixed,_=run("R1.2",output=tmp_path)
    assert good["verdicts"]=={"PASS":22,"FAIL":0,"ERROR":0}
    assert bad["verdicts"]["FAIL"]==5
    assert fixed["verdicts"]==good["verdicts"]
    assert good["requirement_verified"]==14
    assert bad["requirement_verified"]==10

def test_blf_and_dlt_are_binary_and_decodable(tmp_path):
    simulate(case(),"R1.0",tmp_path)
    assert (tmp_path/"capture.blf").read_bytes().startswith(b"LOGG")
    assert (tmp_path/"capture.dlt").read_bytes().startswith(b"DLT\x01")
    assert len(read_blf(tmp_path/"capture.blf"))==102
    assert read_dlt(tmp_path/"capture.dlt")[1]==(.2,"STIMULUS brake")

def test_missing_capture_never_passes(tmp_path):
    assert evaluate(case(),tmp_path)["verdict"]=="ERROR"

def test_truncated_dlt_never_passes(tmp_path):
    simulate(case(),"R1.0",tmp_path)
    path=tmp_path/"capture.dlt";path.write_bytes(path.read_bytes()[:-1])
    assert evaluate(case(),tmp_path)["verdict"]=="ERROR"

def test_capture_gap_never_passes(tmp_path):
    simulate(case(),"R1.0",tmp_path)
    rows=read_blf(tmp_path/"capture.blf")
    write_blf(tmp_path/"capture.blf",[r for r in rows if not .3<=r[0]<=.4])
    assert evaluate(case(),tmp_path)["verdict"]=="ERROR"

def test_incorrect_stimulus_never_passes(tmp_path):
    simulate(case(),"R1.0",tmp_path)
    rows=read_blf(tmp_path/"capture.blf")
    for t,name,signals in rows:
        if name=="Scene" and t>=.2:signals["TTC"]=4
    write_blf(tmp_path/"capture.blf",rows)
    assert evaluate(case(),tmp_path)["verdict"]=="ERROR"

def test_transient_unintended_braking_is_failure(tmp_path):
    c=case("warning")
    simulate(c,"R1.0",tmp_path)
    rows=read_blf(tmp_path/"capture.blf")
    for t,name,signals in rows:
        if name=="Output" and t==.22:signals["Brake"]=1
    write_blf(tmp_path/"capture.blf",rows)
    assert evaluate(c,tmp_path)["verdict"]=="FAIL"

def test_replay_manifest_binds_release_and_log_hash(tmp_path):
    from framework.capture_manifest import create
    root=tmp_path/"captures";folder=root/case()["test_id"];folder.mkdir(parents=True)
    simulate(case(),"R1.0",folder)
    firmware=tmp_path/"firmware.bin";firmware.write_bytes(b"synthetic firmware identity")
    create(root,"R1.0",firmware)
    obj,_=run("R1.0",mode="replay",capture_root=root,selected=[case()["test_id"]],output=tmp_path/"out")
    assert obj["verdicts"]["PASS"]==1
    (folder/"capture.blf").write_bytes(b"altered")
    with pytest.raises(ValueError,match="hash mismatch"):
        run("R1.0",mode="replay",capture_root=root,selected=[case()["test_id"]],output=tmp_path/"out")

def test_unstable_signal_never_passes(tmp_path):
    simulate(case(),"R1.0",tmp_path)
    rows=read_blf(tmp_path/"capture.blf")
    for t,name,signals in rows:
        if name=="Output" and t>.4:signals["Brake"]=0
    write_blf(tmp_path/"capture.blf",rows)
    assert evaluate(case(),tmp_path)["verdict"]=="FAIL"

def test_subset_does_not_claim_full_coverage(tmp_path):
    obj,_=run("R1.0",selected=[case()["test_id"]],output=tmp_path)
    assert obj["full_regression"] is False
    assert obj["requirement_verified"]==0

def test_unknown_suite_id_rejected(tmp_path):
    with pytest.raises(ValueError):run("R1.0",selected=["UNKNOWN"],output=tmp_path)

def test_jira_pagination_deduplicates(monkeypatch):
    pages=iter([{"issues":[{"key":"ADAS-7"}],"nextPageToken":"next","isLast":False},
                {"issues":[{"key":"ADAS-7"},{"key":"ADAS-8"}],"isLast":True}])
    monkeypatch.setattr(jira,"request",lambda *args:next(pages))
    assert len(jira.bugs("ADAS","R1.0")["issues"])==2

def test_jira_suite_maps_only_reviewed_tests(monkeypatch):
    monkeypatch.setattr(jira,"request",lambda *args:{"fields":{"issuelinks":[
        {"outwardIssue":{"key":"ADAS-101"}},{"inwardIssue":{"key":"OTHER-1"}}]}})
    obj=jira.suite("ADAS-1")
    assert obj["test_ids"]==["ADAS-TC-001"]
    assert obj["unmapped_linked_issues"]==["OTHER-1"]

def test_metrics_latest_run_and_bug_counts(tmp_path):
    run("R1.0",output=tmp_path);run("R1.0",output=tmp_path)
    path=tmp_path/"bugs";path.mkdir()
    issue={"key":"ADAS-7","fields":{"priority":{"name":"High"},"status":{"statusCategory":{"key":"new"}}}}
    (path/"R1.0.json").write_text(json.dumps({"release":"R1.0","source":"jira","issues":[issue,issue]}))
    text=metrics(tmp_path)
    assert text.count('adas_test_cases{release="R1.0",mode="demo",verdict="PASS"}')==1
    assert 'adas_bugs_reported{release="R1.0",source="jira"} 1' in text
