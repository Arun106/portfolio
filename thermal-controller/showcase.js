const stages = [
  ['Checkout', 'Git / Jenkins', 'Repository source', 'Checks out SCM, records the exact revision and assigns the build version.', 'Revision file and versioned candidate identity.', 'Stops when source checkout or version setup fails.', 'Jenkinsfile'],
  ['Build & analyse', 'Docker · CMake · Ninja · cppcheck', 'Checked-out source', 'Builds the builder stage, compiles the C++17 application and runs configured static analysis.', 'Compiled test binary and clean analysis result.', 'Compilation or cppcheck failure blocks the run.', 'Dockerfile'],
  ['Module tests & host gate', 'CTest · pytest · Robot · policy gate', 'Builder image and host reports', 'Runs the complete host suite and evaluates reports against the release policy.', 'JUnit XML, summary, triage and metrics reports.', 'Critical failures, missing reports/modules, errors, insufficient tests or ≤90% stop qualification.', 'scripts/gate.py'],
  ['Build runtime image', 'Docker', 'Qualified source', 'Builds the runtime candidate and saves it for later scanning.', 'Versioned local runtime image and image archive.', 'Image build failure stops publication.', 'Dockerfile'],
  ['Security gate', 'Trivy', 'Runtime image archive', 'Scans the candidate image for vulnerabilities.', 'Archived JSON vulnerability report.', 'HIGH or CRITICAL findings fail the stage.', 'Jenkinsfile'],
  ['Publish candidate', 'Docker Hub', 'Scanned runtime image', 'Pushes the versioned candidate and records its immutable digest.', 'Registry digest, version file and checksum.', 'Registry or credential failure prevents approval.', 'Jenkinsfile'],
  ['Manual approval', 'Jenkins input', 'Reports, security result and digest', 'Pauses for a reviewer to authorize progression.', 'Approved candidate decision.', 'Timeout or rejection prevents deployment.', 'Jenkinsfile'],
  ['Deploy & verify', 'Ansible · Docker', 'Approved immutable digest', 'Pulls the digest and verifies the candidate on the lab Docker host.', 'Deployment log and verified release.', 'Deployment failure prevents target qualification.', 'ansible/deploy.yml'],
  ['QEMU candidate tests', 'SSH · Ansible · pytest · Robot', 'Versioned binary, checksum and SSH credentials', 'Transfers to the QEMU Linux guest, verifies it, runs target suites and applies the QEMU gate.', 'QEMU reports, binary checksum and test evidence.', 'Transfer, target test or gate failure leaves the active candidate unchanged.', 'scripts/run_qemu_ci.sh'],
  ['Activate candidate', 'Ansible', 'Qualified QEMU candidate', 'Activates only after QEMU qualification succeeds.', 'Activation log for the selected candidate.', 'Activation failure is reported; a test gate alone is not activation proof.', 'ansible/activate-qemu.yml'],
  ['Publish observability', 'Jenkins post · Pushgateway · Prometheus · Grafana', 'Available host/QEMU metrics reports', 'Publishes each available result source after the pipeline, when a Pushgateway URL is configured.', 'Separate host and QEMU monitoring series.', 'Publication failure is warned without hiding the build evidence.', 'Jenkinsfile']
].map(([title, tool, input, action, output, failure, file]) => ({title, tool, input, action, output, failure, url:`https://github.com/Arun106/embedded-sensor-platform/blob/main/${file}`}));

const buttons = [...document.querySelectorAll('[data-stage]')];
const panel = document.getElementById('stage-detail');
const count = document.getElementById('step-count');
const play = document.getElementById('play');
let current = 0;
let timer = null;

// The original draft contains the ten Jenkins stages. Monitoring is a real
// post-action, so add the eleventh selectable step without replacing the page.
if (buttons.length < stages.length) {
  const button = document.createElement('button');
  button.className = 'stage'; button.dataset.stage = String(stages.length - 1);
  button.setAttribute('aria-pressed', 'false');
  button.innerHTML = '<span class="stage-no">11</span><i class="fas fa-chart-bar" aria-hidden="true"></i><strong>Publish observability</strong>';
  document.querySelector('.pipeline').append(button);
  buttons.push(button);
}

function show(index) {
  current = index;
  buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
  const stage = stages[index];
  panel.replaceChildren();
  const heading = document.createElement('h3'); heading.textContent = `${String(index + 1).padStart(2, '0')} / ${stage.title}`;
  const detail = document.createElement('p'); detail.innerHTML = `<strong>Tool:</strong> ${stage.tool}<br><strong>Input:</strong> ${stage.input}<br><strong>Action:</strong> ${stage.action}<br><strong>Output:</strong> ${stage.output}<br><strong>Failure:</strong> ${stage.failure}`;
  const link = document.createElement('a'); link.href = stage.url; link.textContent = 'Inspect implementation ↗'; link.target = '_blank'; link.rel = 'noopener noreferrer';
  panel.append(heading, detail, link);
  count.textContent = `Stage ${index + 1} of ${stages.length}`;
}
function stop() { clearInterval(timer); timer = null; play.textContent = 'Play walkthrough'; }
buttons.forEach((button, index) => button.addEventListener('click', () => { stop(); show(index); }));
play.addEventListener('click', () => {
  if (timer) return stop();
  show(0); play.textContent = 'Pause walkthrough';
  timer = setInterval(() => { if (current === stages.length - 1) stop(); else show(current + 1); }, 3000);
});
if (matchMedia('(prefers-reduced-motion: reduce)').matches) play.hidden = true;
show(0);

document.querySelectorAll('[data-rate]').forEach(button => button.addEventListener('click', () => {
  const rate = Number(button.dataset.rate);
  document.querySelectorAll('[data-rate]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
  document.getElementById('sim-rate').textContent = `${rate}%`;
  document.getElementById('sim-status').textContent = rate < 95 ? 'Below threshold · real rule waits one minute' : 'Above the warning threshold';
  document.getElementById('sim-note').textContent = `Illustrative snapshot: ${rate} passed out of 100 synthetic cases.`;
  document.querySelector('.sim-readout').classList.toggle('warning', rate < 95);
}));
