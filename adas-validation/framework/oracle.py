"""Temporal assertions from recorded observations, with fail-closed evidence checks."""
import math
import json
from .logs import read_blf, read_dlt

def evaluate(case, folder):
    latency = None
    checking_evidence = True
    try:
        rows = read_blf(folder/"capture.blf")
        events = read_dlt(folder/"capture.dlt")
        outputs = [(t,s) for t,n,s in rows if n=="Output"]
        scene = [(t,s) for t,n,s in rows if n=="Scene"]
        assert len(outputs)>=2 and scene, "missing required CAN signals"
        assert all(math.isfinite(t) for t,_,_ in rows), "invalid timestamp"
        times = [t for t,_ in outputs]
        assert all(b>a for a,b in zip(times,times[1:])), "unordered/duplicate time"
        assert max(b-a for a,b in zip(times,times[1:])) <= .020001, "capture gap exceeds 20 ms"
        assert times[-1]>=.49 and times[0]<=.01, "incomplete capture window"
        stimulus = [(t,s) for t,s in events if s.startswith("STIMULUS ")]
        assert len(stimulus)==1 and stimulus[0][1] == "STIMULUS "+case["scenario"], "DLT stimulus mismatch"
        start = stimulus[0][0]
        assert abs(start-.2)<=.001, "DLT/CAN alignment mismatch"
        initial=json.loads(case["initial_inputs"])
        changed=json.loads(case["stimulus_inputs"])
        for t,signals in scene:
            expected_inputs=changed if t>=start else initial
            assert all(abs(signals[k]-v)<.000001 for k,v in expected_inputs.items()), "recorded stimulus differs from reviewed test inputs"
        assert any(t<start for t,_ in scene) and any(t>=start for t,_ in scene), "missing stimulus transition evidence"
        checking_evidence = False
        signal = case["signal"]
        expected = float(case["expected"])
        deadline = float(case["deadline_ms"])/1000
        if signal == "Counter":
            assert all((b["Counter"]-a["Counter"])%256==1 for (_,a),(_,b) in zip(outputs,outputs[1:])), "heartbeat counter discontinuity"
            latency=0
        else:
            window = [(t,s[signal]) for t,s in outputs if t>=start]
            match = next((t for t,v in window if v==expected),None)
            assert match is not None, f"{signal} never reached {expected}"
            latency = round((match-start)*1000,3)
            assert latency<=deadline*1000+.001, f"{signal} latency {latency} ms exceeds {deadline*1000:g} ms"
            # Deadline reached: remain stable for the rest of the capture.
            assert all(v==expected for t,v in window if t>=start+deadline), f"{signal} unstable after deadline"
        return dict(verdict="PASS",latency_ms=latency,reason="Temporal and evidence checks satisfied")
    except (AssertionError,ValueError,KeyError,OSError,StopIteration) as exc:
        # Failed behavior is FAIL; malformed/missing capture is ERROR.
        return dict(verdict="FAIL" if isinstance(exc,AssertionError) and not checking_evidence else "ERROR",
            latency_ms=latency,reason=str(exc))
