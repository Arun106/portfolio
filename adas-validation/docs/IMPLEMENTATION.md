# ADAS ECU verification automation — implementation and consulting guide

Prepared for Arun Arun. Reference implementation: 9 October 2026.

## What is implemented

A runnable synthetic AEB ECU, 14 illustrative software requirements, 14 test specifications and 22 linked test cases; binary BLF/DLT captures; DBC signal decoding; temporal assertions; evidence hashes; JUnit and Xray-compatible JSON; three-release regression demonstration; Jira Cloud suite mapping and defect collection; Jenkins pipeline; Prometheus exporter; provisioned Grafana dashboard; animated portfolio presentation.

The demo runs on an ordinary Linux computer. It does not claim that a production ECU was built, flashed, exercised on a real HIL bench or certified. Commercial vendor tools and a real ECU need the adapters described below. No live Jenkins/Jira/Grafana service was accessed during creation. Docker configuration is supplied but container startup needs validation on the target host.

## 1. Traceability model and DOORS import

The stable external IDs are:

`ADAS-SWR-002 → ADAS-TS-002 → ADAS-TC-003 → release / run_id → capture.blf + capture.dlt → verdict`.

Consult test_cases.csv for authoritative IDs. These external IDs are custom attributes, not DOORS-generated Absolute Numbers. Do not overwrite DOORS internal IDs.

Import requirements.csv into a new formal module in DOORS Classic using its spreadsheet import function. Map object_heading to Object Heading, object_text to Object Text and requirement_id to an External Requirement ID attribute. Create attributes for parent ID, baseline, safety goal, ASIL, verification method and status. Import test specifications and cases into separate modules, then resolve the external IDs and create actual link-module relationships. The CSV contains ID references; CSV import alone does not create native DOORS links. Export a review baseline or ReqIF for downstream consumption. DOORS Next has different import/update/link mapping rules; use the project's existing artifact types and imported native identifiers.

The synthetic parent ADAS-SYS-001 and safety-goal DEMO-SG-01 are placeholders. Establish a real item definition and approved parent artifacts before creating native links. Tables are drafted for review, not copied from an OEM.

The runner rejects duplicate IDs, orphan links, mismatched requirement/spec links, uncovered requirements/specifications and unknown suite selections. Change requests must retain IDs, version the changed text and record impact on specifications, cases, software, calibrations and evidence.

## 2. Example functional scope

This AEB demonstration has warning and braking thresholds, operating-speed boundaries, feature disablement, driver override, invalid-input handling, degradation, threat clearance and output heartbeat.

The CAN contract is data/adas.dbc: Scene 0x100 is HIL stimulus; Output 0x200 is ECU response. Speed is km/h, TTC is seconds, State is 0=disabled/1=enabled/2=degraded. Inputs change at 200 ms; captures last 500 ms. Brake response deadline is 100 ms. These thresholds are educational assumptions. The model is not a realistic perception, vehicle-dynamics or brake-controller model.

Tests cover equivalence classes, selected boundaries, negative states and fault flags. Additional production tests should cover sensor timeout, plausibility, hysteresis, message E2E/CRC, counter rollover, ignition states, power interruption, diagnostic-session effects, calibration variability, bus load, multi-ECU arbitration, braking dynamics and broader scenario/ODD boundaries.

## 3. ISO 26262 and intended-function safety

ISO 26262-6 covers development at the software level; Part 4 concerns the system level and Part 8 supporting processes. This implementation demonstrates requirements-based evidence and traceability, useful within a safety lifecycle. It does not demonstrate compliance with every clause.

ASIL is left TBD. The safety team must perform item definition and HARA, classify hazardous events and derive safety goals, functional/technical safety requirements and software safety requirements. An AEB label does not determine an ASIL. Software requirements inherit a justified allocation, including any permitted decomposition.

Required project work products include the safety plan, approved requirements and architecture baselines, verification plan and methods, test specifications, independent reviews where applicable, configuration/change records, qualification/confidence assessment for tools as applicable, anomaly disposition, verification reports and the safety case. Determine exact methods, rigor and independence from the licensed standard and project safety plan.

Requirement coverage is not statement/branch/MC/DC coverage. Model and code coverage need instrumentation and the applicable software-unit/integration verification activities. Python framework tests do not establish ECU structural coverage.

ADAS also needs intended-function validation and scenario analysis; ISO 21448/SOTIF addresses relevant insufficiencies of intended functionality. Passing CAN-output assertions is insufficient to show that the vehicle function is safe in its ODD. Validate simulation fidelity and correlate HIL results with controlled vehicle evidence.

## 4. Executable architecture

| Layer | Implementation | Responsibility |
|---|---|---|
| Requirements/catalog | data/*.csv | Stable IDs, reviewable acceptance criteria |
| Runner | framework/run.py | Trace checks, suite selection, evidence collection and reports |
| ECU stand-in | framework/simulator.py | Synthetic behavior independent of CSV deadline oracle |
| Bus interface | data/adas.dbc, framework/logs.py | Raw binary CAN and decoded engineering values |
| Verdict engine | framework/oracle.py | Timing, stability, counters, completeness checks |
| HIL orchestration | framework/hardware.py | Reviewed build/preflight/flash/identity/capture/teardown commands |
| Test management | framework/jira.py | Read mapped suite links, collect paginated unique defects |
| CI | Jenkinsfile | Checkout, framework verification, bench lock, regression and evidence |
| Reporting | monitoring/ | Prometheus metrics and Grafana dashboards |

For mixed benches, put an ASAM XIL/vendor adapter beneath the runner, keeping engineering units and signal names independent of bench implementation. Time-critical stimulus and sampling must run in the real-time simulator or vendor execution engine. Jenkins and ordinary Python scheduling are not real-time control.

## 5. Run locally

From the repository:

```bash
cd adas-validation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python -m framework.run --release R1.0
.venv/bin/python -m framework.run --release R1.1
# R1.1 intentionally exits 1 because the timing regression is detected.
.venv/bin/python -m framework.run --release R1.2
```

R1.0: 22 PASS, 14/14 requirements verified. R1.1: 17 PASS, 5 FAIL, 10/14 verified. R1.2: 22 PASS, 14/14 verified. This is simulated behavior observed from generated logs. These release names are demo scenarios, not actual software shipped.

Each run produces a unique timestamp/UUID directory. Reports include release, commit environment value, requirement/spec/test IDs, latency, reason and SHA-256 hashes of evidence. Jenkins supplies GIT_COMMIT. A local run is explicitly local-uncommitted.

Replay already captured evidence:

```bash
.venv/bin/python -m framework.run --release ECU-2026.10 --mode replay --capture-root /path/to/captures
```

Required directory layout: captures/ADAS-TC-001/capture.blf and capture.dlt, repeated for each executed test. A capture-root manifest.json must identify the release, firmware_sha256 and per-test/per-log hashes. Generate it on the bench immediately after a fresh capture using framework.capture_manifest --root captures --release ECU-2026.10 --firmware /path/to/verified-image.bin. The runner checks identity and hashes before replay. The hash binds the image file to the evidence manifest; the bench must separately confirm that image is actually executing on the ECU. Captures must use the supplied DBC and documented DLT profile. An arbitrary OEM BLF/DLT needs corresponding decoder/profile adapters and reviewed signal mappings.

## 6. Test-logic validation technique

Separate stimulus, ECU behavior and acceptance criteria. The simulator defines ECU rules; the CSV defines desired values and deadlines. Passing the model is only a framework demonstration, not an independent validation of real product requirements.

The oracle locates the stimulus timestamp in DLT, checks CAN capture alignment and sample continuity, finds first expected output, compares observed latency with the deadline, and checks the output remains stable after the deadline. Counter tests detect heartbeat discontinuity. No requirement is verified unless all linked test cases were executed and passed.

Framework tests deliberately introduce a slow release, missing/truncated captures, sampling gaps and unstable outputs; they also test unknown suite IDs, partial-suite coverage, Jira pagination deduplication and the reporting exporter. Extend with mutations of comparison operators and thresholds, endian/scale errors, clock drift, dropped frames, output stuck-at faults, incorrect stimuli, extra transitions and exact-deadline rounding. For production, independently review the oracle against the specification, replay golden captures from a separate trusted measurement setup, and version toolchains and decoder databases.

PASS means the declared assertions were satisfied by the supplied evidence. FAIL indicates behavioral assertion failure; ERROR indicates unreadable/missing/unsupported evidence, capture-quality failure or mismatched recorded stimulus. Neither FAIL nor ERROR permits the Jenkins release gate to succeed. Initial and applied input values are stored in the case catalog and checked against the decoded Scene frames.

## 7. Logs and correlation

| Evidence | Typically captured by | What it supports |
|---|---|---|
| BLF / ASC | CANoe/CAN logging tools | CAN/CAN FD bus traffic; DBC/ARXML decoding |
| DLT | Instrumented ECU application/daemon plus DLT client | Application state, events and diagnostic traces |
| MF4/MDF | Measurement/HIL/calibration tool | Synchronized bus, analog, plant and internal measurements |
| PCAP/PCAPNG | Network tap/Wireshark/tcpdump | Ethernet, SOME/IP, DoIP and transport analysis |
| UDS diagnostic trace | Diagnostic tester | DTCs, sessions, NRCs, ECU software identity |
| XCP/A2L measurement | Calibration/measurement tool | Internal ECU variables and timing correlation |
| UART/serial, syslog, QNX logs | Platform-specific collector | Boot, reset, OS and driver failures |
| HIL execution/flash report | Bench and flashing tools | Applied scenario, fault injection, flashing result and identity |

The ECU normally emits bus frames and application messages; the logger creates BLF/MF4 containers. DLT is available only if instrumented and accessible. Treat absent logs as a collection/configuration issue, not a passing result.

The included DLT encoder/decoder supports a narrow DLT V1 storage/verbose-string profile: ECU1, ADAS/AEB1, big-endian arguments and timestamp. It is not a universal DLT parser and has not been validated with every vendor reader. Real non-verbose DLT requires message dictionaries/FIBEX as appropriate.

Production evidence needs a common clock/correlation strategy, PTP or bench timebase where available, capture channel identity, software/calibration hashes, DBC/ARXML/A2L/FIBEX versions, power and network configuration, dropped-frame counters, timestamp uncertainty and run metadata. The demo's synthetic timestamps and fixed time alignment must be replaced with measured synchronization.

## 8. Jenkins integration with your setup

The supplied Linux agent label is azure-docker-agent, matching your previous lab setup. This has not been verified against your current controller. Python 3.10+ and venv support are required; CANoe typically runs on a separately configured Windows bench agent. Modify labels and command adapters to match the bench OS.

Create a Pipeline from SCM using your portfolio repository and script path adas-validation/Jenkinsfile. Run MODE=demo, RELEASE=R1.0 initially. Install/enable Pipeline, Git, JUnit, Credentials Binding and Lockable Resources plugins. Define lock resource adas-hil-bench-01 for hardware mode. All bench jobs must use that resource.

Prepare a reporting directory on the Jenkins execution host owned by its actual agent OS user:

```bash
sudo install -d -o <agent-user> -g <agent-group> /srv/adas/artifacts
```

Replace angle-bracket placeholders. Jenkins atomically publishes run directories there; Grafana mounts it read-only. If monitoring runs on another host, use an authenticated artifact transport or shared volume and preserve atomic publication; local paths alone do not synchronize remote hosts.

For push-triggered builds, configure GitHub webhook delivery to Jenkins and the corresponding multibranch/SCM trigger, restricted to trusted branches. Webhook registration is a controller/repository setup step; it is not performed by this Jenkinsfile. A full software build needs an actual firmware repository/toolchain, separate from this portfolio repository. Pass the immutable built image to the bench pipeline and verify its SHA-256 and ECU-reported identity. A portfolio commit alone is not an ECU firmware build.

The HIL config is an operator-controlled JSON file on the agent, referenced by ADAS_HIL_CONFIG. Each value is an argv array for build, preflight, flash, verify_identity, capture_and_execute and teardown. Commands are trusted bench scripts, not strings supplied by Jira/webhook content. They receive ADAS_RELEASE in the environment. Missing configuration stops execution; teardown runs even after failure.

Preflight must verify ignition/power, emergency stop, firmware/bench compatibility, licensing and logger readiness. Flash must use an OEM-approved tool such as the project's ODIS/UDS/DoIP/vendor process, then prove image identity and calibration. Capture adapter must reset state per test and produce files in artifacts/hil-captures/<test-id>/ plus the capture manifest. The orchestrator deletes the previous capture directory before a fresh hardware execution; the runner checks release and log hashes.

Jenkins advantages: versioned orchestration, automatic push/nightly runs, distributed Linux/Windows agents, serial bench allocation, repeatable regression, credentials management, JUnit trends, archived evidence and explicit release gates. Costs: plugin maintenance, bench/license constraints, stale workspaces, flaky infrastructure and asynchronous tool failures. Never silently rerun failures until they become passes. Record attempts, retain first-failure evidence and distinguish product failures from infrastructure failures.

## 9. Jira suite selection and Xray

Create reviewed Test issues and replace the illustrative ADAS-101…ADAS-122 keys in test_cases.csv with actual keys. A suite issue links to these Test issues. The runner reads issue links, intersects them with the local approved mapping and saves selected-suite.json. This generic mapping is not Xray's native Test Set membership API. If using native Xray Test Sets/Plans, implement the installed Cloud GraphQL or Data Center API adapter.

Store Jenkins credentials: adas-jira-url as secret text (HTTPS base URL), adas-jira as username/password (email/API token). Only Jira-enabled stages require them. Set JIRA_SUITE to the suite key; leave it empty for full regression.

Jira does not execute a HIL suite by itself. A Jira Automation rule or Xray workflow can call a secured Jenkins endpoint, passing the approved suite key and immutable release identifier; Jenkins fetches mapped cases and runs the bench. Configure endpoint authorization, CSRF/API authentication and controller-side parameter validation. No Jira automation rule was created here.

The runner emits xray-results.json using linked testKey fields; Cloud import is POST to https://xray.cloud.getxray.app/api/v2/import/execution using a bearer token obtained from the Cloud authentication API. Data Center uses its own REST endpoint/authentication. Import is deliberately not sent automatically: demo keys must first be mapped to actual Test issues and the tenant verified. Keep network failures visible and retain the payload for retry. Include run metadata and evidence attachments via the tenant's supported API.

Bug collection uses Jira Cloud enhanced POST /rest/api/3/search/jql, all pages, deduplicated issue keys and Affects Version. It does not create defects. Jira version naming must match the release parameter. Set JIRA_REPORTING=true for a live snapshot.

## 10. Grafana reporting

Provisioned dashboard: ADAS ECU | Release verification & defects. Panels compare verdict counts, pass rate, executed and verified requirement coverage, full-regression flag, unique reported bugs, severity/lifecycle categories and bug snapshots over collection time.

Bug counts come from distinct Jira Bug issue keys with Affects Version equal to the tested release. Fix Version describes where remediation is planned and is not used for attribution. A bug can affect multiple releases, so counts cannot be summed across releases to obtain unique global defects. Priority is used as severity proxy; map your actual Severity custom field in projects that use one.

No bug snapshot means unknown, not zero. Demo snapshots are marked source=demo; live Jira snapshots source=jira. Select source=jira and mode=replay for real captures. Five failed tests in R1.1 correspond to one illustrative timing defect, showing why failures and bugs differ.

Start on your Docker host:

```bash
cd adas-validation/monitoring
export GRAFANA_ADMIN_PASSWORD='<choose-strong-password>'
export ADAS_ARTIFACT_DIR=/srv/adas/artifacts
docker compose up -d
```

For local demo runs, omit ADAS_ARTIFACT_DIR to use ../artifacts. Grafana is http://localhost:3000, username arun; use an SSH tunnel for a remote host. The compose file binds Grafana to loopback, leaving public exposure to your existing authenticated reverse proxy. Image tags are explicit demo baselines; review current supported/security-patched versions and pin approved digests for rollout.

Prometheus scrapes exporter:8080 every 15 seconds. The exporter selects the latest completed run for each release, preventing duplicate counts when a release is rerun. It reads current Jira defect snapshots. Prometheus stores observations from its collection time; it does not reconstruct earlier test history from JSON timestamps. For audit/history analytics, persist a run-level store alongside archived evidence and dashboard that separately. Control release-label cardinality and retention.

## 11. Framework selection — engineering recommendation

These are representative options, not every available framework. Recommendations are engineering judgments based on product, team and installed bench/toolchain.

| Framework/tool | Strong fit | Main advantage | Constraint / selection test |
|---|---|---|---|
| pytest + python-can/cantools | Python-skilled teams; custom signal/log analysis | Transparent assertions, parameterization, inexpensive CI, reusable libraries | Team owns adapters, timing, qualification assessment and reporting |
| Robot Framework + Python libraries | Mixed technical/business teams; readable system scenarios | Keyword-based suites and approachable reports | Keep complex signal logic in Python; avoid keyword sprawl |
| CANoe + vTESTstudio/CAPL | CAN/Ethernet/diagnostics-heavy ECU tests | Close integration with network simulation and ECU test execution | Licenses, Windows setup, vendor toolchain and project signal databases |
| dSPACE AutomationDesk | dSPACE or XIL-compatible HIL/SiL benches | Bench/fault-injection ecosystem and cross-stage reuse | Packages, licenses and real-time model configuration |
| tracetronic ecu.test | Heterogeneous automotive tools/benches | Multi-tool automation and Jenkins integration | Evaluate supported tool versions, licenses and adapters |
| Simulink Test + Requirements Toolbox + Coverage | Model-based control software | Model harnesses, requirement links and coverage analysis | Model/toolbox ownership; correlate model and target behavior |
| ASAM XIL | Interface abstraction across compatible benches | Vendor-neutral test-to-bench API | An interface standard, not a complete runner or safety approval |

For your demonstration: use pytest for transparent traceability/log verdicts, then add CANoe/vTESTstudio for a Vector-oriented network bench or AutomationDesk for a dSPACE plant/fault bench. Use ASAM XIL when supported to limit bench coupling. Choose ecu.test where many vendor tools must be coordinated. Jenkins schedules the selected engine; Grafana reports its results.

Supplement lower levels with unit-test frameworks appropriate to ECU language and toolchain, model/code coverage and static analysis. Web/UI tools are useful for diagnostic portals but do not replace real-time ECU testing. Purchase decisions require a representative proof of concept on your actual bench, signal set and worst-case scenarios.

## 12. Rollout plan and acceptance

1. Agree product scope, item/safety responsibilities, reviewed baselines, signal interface, bench ownership and evidence policy.
2. Pilot a small set of reviewed nominal/boundary/fault cases; validate temporal oracles on independent good/bad captures.
3. Integrate one bench with build/flash/identity/capture/teardown; prove emergency handling, reset and clock correlation.
4. Run repeatability and adverse-condition trials. Investigate flaky outcomes and separate product defects from infrastructure.
5. Connect Jira/Xray with approved mappings; enable Jenkins push/nightly schedules and full regression gates.
6. Provision Grafana with labelled demo/real sources, verify bug attribution and agree dashboard ownership.
7. Expand scenarios and test levels, establish review/qualification activities and retain release safety evidence.

Acceptance: all links resolvable; all selected cases explicitly accounted for; immutable image identity; complete synchronized evidence; known-bad faults detected; no skipped case counted as pass; full safety-relevant regression before release; independently reviewed reports and documented anomaly disposition. Impact-based smoke testing accelerates feedback but does not replace the agreed full-release verification.

## 13. Manager demonstration script

Open the portfolio lab. Select R1.0 and play the pipeline. Inspect a requirement, its specification and linked test verdict. Select R1.1 to show a 140 ms response exceeding the 100 ms deadline; five related test failures map to one illustrative defect. Select R1.2 to show re-verification. Open the release comparison and Grafana deployment instructions. Explain that the same log oracle can consume real bench captures after the vendor adapters and safety review are completed.

## Primary references

- ISO 26262-6:2018: https://www.iso.org/standard/68388.html
- IBM DOORS Classic CSV import: https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.1?topic=modules-importing-spreadsheets
- ASAM XIL: https://www.asam.net/standards/detail/xil/
- Vector vTESTstudio: https://www.vector.com/en/product/vteststudio/
- dSPACE AutomationDesk: https://www.dspace.com/en/ltd/home/products/sw/test_automation_software/automationdesk.cfm
- tracetronic Jenkins integration: https://www.tracetronic.com/products/extras/
- Simulink Test: https://www.mathworks.com/products/simulink-test.html
- Robot Framework user guide: https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html
- python-can BLF support: https://python-can.readthedocs.io/en/stable/file_io.html
- COVESA DLT: https://covesa.github.io/dlt-daemon/
- Jira Cloud search: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/
- Xray import: https://docs.getxray.app/display/XRAYCLOUD/Import+Execution+Results
- Jenkins credentials: https://www.jenkins.io/doc/book/using/using-credentials/
- Jenkins locks: https://www.jenkins.io/doc/pipeline/steps/lockable-resources/
- Grafana provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/
- Prometheus configuration: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
