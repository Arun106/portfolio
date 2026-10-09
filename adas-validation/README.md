# ADAS ECU validation lab

Runnable portfolio reference for requirements → test specifications → test cases → BLF/DLT evidence → release verdicts → Jira defects → Grafana.

Start with [the implementation guide](docs/IMPLEMENTATION.md). The CSV catalog is illustrative and has no OEM provenance or approved ASIL assignment.

```bash
cd adas-validation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python -m framework.demo
```

The demo generator runs baseline, deliberately regressed and fixed synthetic releases. Normal CI uses framework.run, which exits nonzero on any failed or erroneous case. Jira connectivity, real HIL adapters and Grafana containers require target-host configuration; they are not live in this repository.

- Portfolio walkthrough: index.html
- Requirements / specifications / cases: data/*.csv
- Jenkins SCM script path: adas-validation/Jenkinsfile
- Grafana: monitoring/compose.yml and provisioning
- Real bench capture orchestration: framework/hardware.py
- Evidence replay: framework/run.py --mode replay
