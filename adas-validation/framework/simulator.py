"""Synthetic ECU model, independent of CSV oracle acceptance limits."""
from .logs import write_blf, write_dlt

def simulate(case, release, folder):
    scenario = case["scenario"]
    initial = dict(Speed=50, TTC=5, Valid=1, Override=0, Enabled=1, Fault=0)
    changed = dict(initial)
    changed.update({
        "warning": {"TTC":2}, "brake":{"TTC":1},
        "speed_low":{"Speed":4,"TTC":1}, "speed_min":{"Speed":5,"TTC":1},
        "speed_max":{"Speed":130,"TTC":1}, "speed_high":{"Speed":131,"TTC":1},
        "ttc_boundary":{"TTC":1.5}, "ttc_above":{"TTC":1.501},
        "disabled":{"Enabled":0,"TTC":1}, "invalid":{"Valid":0,"TTC":1},
        "override":{"Override":1,"TTC":1}, "fault":{"Fault":1,"TTC":1},
        "clear":{"TTC":4}, "heartbeat":{}, "healthy":{}
    }[scenario])
    if scenario in ("override","clear"):
        initial["TTC"] = 1
    event = .2
    delay = .14 if release == "R1.1" and scenario in ("brake","speed_min","speed_max","ttc_boundary") else .04
    def ecu(inputs):
        eligible = inputs["Enabled"] and inputs["Valid"] and not inputs["Override"] and not inputs["Fault"] and 5 <= inputs["Speed"] <= 130
        return dict(Brake=int(bool(eligible and inputs["TTC"] <= 1.5)),
            Warning=int(bool(eligible and inputs["TTC"] <= 2.5)),
            State=2 if inputs["Fault"] or not inputs["Valid"] else 1 if inputs["Enabled"] else 0,
            Counter=0)
    samples = []
    for index in range(51):
        t = round(index*.01, 5)
        inp = changed if t >= event else initial
        out = ecu(changed if t >= round(event+delay, 5) else initial)
        out["Counter"] = index % 256
        samples.extend([(t,"Scene",inp),(t,"Output",out)])
    write_blf(folder/"capture.blf", samples)
    write_dlt(folder/"capture.dlt", [(0,"BOOT_OK"),(event,f"STIMULUS {scenario}"),
        (event+delay,"FAULT" if scenario in ("fault","invalid") else "STATE_UPDATED"),(.5,"CAPTURE_END")])
