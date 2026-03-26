const kpis = document.getElementById('kpis');
const statusBreakdown = document.getElementById('status-breakdown');
const environmentBreakdown = document.getElementById('environment-breakdown');
const moduleQuality = document.getElementById('module-quality');
const runsTable = document.getElementById('runs-table');
const activityMeta = document.getElementById('activity-meta');
const connectionStatus = document.getElementById('connection-status');
const seedRunButton = document.getElementById('seed-run');

function percent(value, total) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function kpiCard(label, value) {
  return `<div class="kpi"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function breakdownHtml(data, total, cssClass) {
  return Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => `
      <div class="breakdown-row">
        <div class="breakdown-label"><span>${label}</span><span>${value}</span></div>
        <div class="bar"><div class="fill ${cssClass(label)}" style="width:${percent(value, total)}%"></div></div>
      </div>
    `)
    .join('');
}

function render(summary) {
  const totals = summary.totals;
  const totalStatuses = Object.values(summary.status_counts).reduce((a, b) => a + b, 0);
  const totalEnvironments = Object.values(summary.environment_counts).reduce((a, b) => a + b, 0);

  kpis.innerHTML = [
    kpiCard('Total Runs', totals.runs),
    kpiCard('Total Test Cases', totals.cases),
    kpiCard('Pass Rate', `${totals.pass_rate}%`),
    kpiCard('Open Defects', totals.open_defects),
  ].join('');

  statusBreakdown.innerHTML = breakdownHtml(summary.status_counts, totalStatuses, (label) => {
    if (label === 'PASSED') return 'success';
    if (label === 'RUNNING') return 'info';
    if (label === 'SKIPPED') return 'warning';
    return 'danger';
  });

  environmentBreakdown.innerHTML = breakdownHtml(summary.environment_counts, totalEnvironments, () => 'info');

  moduleQuality.innerHTML = summary.module_quality
    .sort((a, b) => a.pass_rate - b.pass_rate)
    .map(item => `
      <div class="module-row">
        <div class="module-title">
          <span>${item.module}</span>
          <span>${item.pass_rate}% (${item.passed}/${item.total})</span>
        </div>
        <div class="bar"><div class="fill ${item.pass_rate >= 85 ? 'success' : item.pass_rate >= 70 ? 'warning' : 'danger'}" style="width:${item.pass_rate}%"></div></div>
      </div>
    `).join('');

  runsTable.innerHTML = summary.latest_runs.map(run => {
    const progress = percent(run.passed + run.failed, run.total);
    return `
      <tr>
        <td>${run.suite_name}</td>
        <td>${run.build_version}</td>
        <td>${run.environment}</td>
        <td><span class="status ${run.status}">${run.status}</span></td>
        <td>
          <div class="bar"><div class="fill ${run.status === 'FAILED' || run.status === 'BLOCKED' ? 'danger' : run.status === 'PASSED' ? 'success' : 'info'}" style="width:${progress}%"></div></div>
        </td>
      </tr>
    `;
  }).join('');

  activityMeta.textContent = `Last refreshed: ${new Date(summary.generated_at).toLocaleString()}`;
}

async function loadSummary() {
  const response = await fetch('/api/summary');
  const summary = await response.json();
  render(summary);
}

function connectSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.onopen = () => {
    connectionStatus.textContent = 'Live';
  };
  socket.onmessage = event => {
    const payload = JSON.parse(event.data);
    if (payload.summary) render(payload.summary);
  };
  socket.onclose = () => {
    connectionStatus.textContent = 'Reconnecting…';
    setTimeout(connectSocket, 2000);
  };
  return socket;
}

async function createDemoRun() {
  const timestamp = Date.now();
  const payload = {
    suite_name: `Checkout Regression ${timestamp.toString().slice(-4)}`,
    environment: ['QA', 'UAT', 'STAGING'][Math.floor(Math.random() * 3)],
    build_version: `v2.${Math.floor(Math.random() * 9)}.${Math.floor(Math.random() * 20)}`,
    test_cases: [
      { name: 'Login with MFA', module: 'Auth', status: 'RUNNING', duration_ms: 0 },
      { name: 'Create new order', module: 'Checkout', status: 'RUNNING', duration_ms: 0 },
      { name: 'Apply coupon', module: 'Pricing', status: 'RUNNING', duration_ms: 0 },
      { name: 'Card payment flow', module: 'Payments', status: 'RUNNING', duration_ms: 0 },
      { name: 'Order history sync', module: 'Orders', status: 'RUNNING', duration_ms: 0 },
    ],
  };

  await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

seedRunButton.addEventListener('click', createDemoRun);
loadSummary();
connectSocket();
