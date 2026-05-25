/* ─── Config ─────────────────────────────────────────────────────────── */
const WS_URL = (() => {
  const params = new URLSearchParams(window.location.search);
  return params.get("ws") || `ws://${window.location.hostname}:${window.location.port || 8000}/ws`;
})();

const IS_GITHUB_PAGES = window.location.hostname.endsWith("github.io");
const MAX_FEED_ROWS    = 80;
const MAX_ALERT_ITEMS  = 40;
const MAX_CHART_POINTS = 40;
const BATCH_INTERVAL_MS = 600;   // push a batch every 600 ms in simulator
const SIM_BATCH_SIZE    = 18;

/* ─── DOM refs ───────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const wsStatus    = $("ws-status");
const feedBody    = $("feed-body");
const feedCount   = $("feed-count");
const alertsList  = $("alerts-list");
const alertCount  = $("alert-count");

const statTps     = $("stat-tps");
const statTotal   = $("stat-total");
const statFraud   = $("stat-fraud");
const statRate    = $("stat-rate");
const statBatches = $("stat-batches");
const statUptime  = $("stat-uptime");
const batchNum    = $("batch-num");
const batchRows   = $("batch-rows");

/* ─── Runtime state ──────────────────────────────────────────────────── */
let feedRowCount   = 0;
let alertItemCount = 0;
const tpsHistory   = [];
const typeCounts   = { PAYMENT: 0, CASH_OUT: 0, CASH_IN: 0, DEBIT: 0, TRANSFER: 0 };
const ruleCounts   = { HIGH_AMOUNT: 0, BALANCE_DRAIN: 0, TRANSFER_SPIKE: 0, DATASET_FRAUD: 0 };
let simStats = {
  total_processed: 0, total_fraud: 0, batches: 0,
  start_ts: Date.now(),
  rule_counts: { ...ruleCounts },
};

/* ═══════════════════════════════════════════════════════════════════════
   BROWSER SIMULATOR
   Generates PaySim-style transactions and applies fraud rules in JS.
   Used when WebSocket is unavailable (GitHub Pages, offline).
═══════════════════════════════════════════════════════════════════════ */

const TYPES_WEIGHTED = [
  ...Array(34).fill("PAYMENT"),
  ...Array(35).fill("CASH_OUT"),
  ...Array(14).fill("CASH_IN"),
  ...Array(9).fill("DEBIT"),
  ...Array(8).fill("TRANSFER"),
];
const CITIES = [
  "New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia",
  "San Antonio","San Diego","Dallas","San Jose","Austin","Jacksonville",
  "Denver","Seattle","Nashville","Portland","Miami","Atlanta","Boston","Detroit",
];
const MERCHANTS = [
  "Amazon","Walmart","Target","Costco","Home Depot","Best Buy","Kroger",
  "CVS","Walgreens","McDonald's","Starbucks","Apple","Netflix","Uber",
  "Shell","BP","Chase ATM","Wells Fargo ATM","Bank Transfer","Venmo",
];

let _simStep = 0;
const _balances = {};

function _rand(min, max) { return Math.random() * (max - min) + min; }
function _pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function _uuid() { return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2); }
function _account(prefix = "C") { return prefix + Math.floor(_rand(1e6, 9e6)); }

function _lognorm(mu, sigma) {
  // Box–Muller transform → lognormal
  const u = Math.random(), v = Math.random();
  const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  return Math.exp(mu + sigma * z);
}

function _simAmount(type, fraud) {
  if (fraud) return +_rand(150_000, 2_000_000).toFixed(2);
  if (type === "TRANSFER" || type === "CASH_OUT") return +_lognorm(9.5, 1.8).toFixed(2);
  if (type === "CASH_IN") return +_lognorm(8.5, 1.5).toFixed(2);
  return +_lognorm(5.0, 1.2).toFixed(2);
}

// Pre-generate a pool of 2 000 accounts
const _accounts = Array.from({ length: 2000 }, () => _account("C"));
const _mAccounts = Array.from({ length: 200 }, () => _account("M"));
_accounts.forEach(a => { _balances[a] = +_rand(1_000, 500_000).toFixed(2); });

function _fraudRules(tx) {
  const rules = [];
  const amt = tx.amount, type = tx.type, newBal = tx.new_balance_orig;
  if (amt > 200_000) rules.push("HIGH_AMOUNT");
  if ((type === "TRANSFER" || type === "CASH_OUT") && newBal === 0 && amt > 10_000) rules.push("BALANCE_DRAIN");
  if (type === "TRANSFER" && amt > 150_000) rules.push("TRANSFER_SPIKE");
  if (tx._ds_fraud) rules.push("DATASET_FRAUD");
  return rules;
}

function _simTimestamp(step) {
  const base = new Date(2024, 0, 1, 0, 0, 0);
  base.setHours(base.getHours() + Math.floor(step / 10));
  base.setMinutes((step % 10) * 6);
  return base.toISOString().replace("T", " ").slice(0, 19);
}

function generateSimBatch(size) {
  const txns = [], alerts = [];
  for (let i = 0; i < size; i++) {
    _simStep++;
    const type = _pick(TYPES_WEIGHTED);
    let fraud = false;
    if (type === "TRANSFER" && Math.random() < 0.08) fraud = true;
    if (type === "CASH_OUT"  && Math.random() < 0.04) fraud = true;

    const amount = _simAmount(type, fraud);
    const orig = _pick(_accounts);
    const dest = (type === "TRANSFER" || type === "CASH_OUT") ? _pick(_accounts) : _pick(_mAccounts);

    const oldBalOrig = _balances[orig] ?? 0;
    const newBalOrig = fraud ? 0 : Math.max(0, +(oldBalOrig - amount).toFixed(2));
    const oldBalDest = _balances[dest] ?? 0;
    const newBalDest = type !== "CASH_OUT" ? +(oldBalDest + amount).toFixed(2) : oldBalDest;

    _balances[orig] = newBalOrig;
    if (_balances[dest] !== undefined) _balances[dest] = newBalDest;

    const tx = {
      transaction_id: _uuid(),
      step: _simStep,
      type,
      amount,
      account_orig: orig,
      old_balance_orig: oldBalOrig,
      new_balance_orig: newBalOrig,
      account_dest: dest,
      old_balance_dest: oldBalDest,
      new_balance_dest: newBalDest,
      is_fraud: fraud ? 1 : 0,
      _ds_fraud: fraud,
      timestamp: _simTimestamp(_simStep),
      location: _pick(CITIES),
      merchant: _pick(MERCHANTS),
    };

    const rules = _fraudRules(tx);
    tx.fraud_rules  = rules;
    tx.is_flagged   = rules.length > 0;
    txns.push(tx);

    simStats.total_processed++;
    if (rules.length) {
      simStats.total_fraud++;
      alerts.push(tx);
      rules.forEach(r => { simStats.rule_counts[r] = (simStats.rule_counts[r] || 0) + 1; });
    }
  }
  simStats.batches++;
  const elapsed = (Date.now() - simStats.start_ts) / 1000;
  return {
    type: "batch",
    transactions: txns,
    alerts,
    stats: {
      ...simStats,
      elapsed_seconds: +elapsed.toFixed(1),
      rows_per_second: +(simStats.total_processed / Math.max(elapsed, 1)).toFixed(1),
      fraud_rate: +(simStats.total_fraud / Math.max(simStats.total_processed, 1) * 100).toFixed(2),
    },
  };
}

/* ═══════════════════════════════════════════════════════════════════════
   RENDERING
═══════════════════════════════════════════════════════════════════════ */
function fmtAmount(v) {
  return "$" + parseFloat(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtUptime(s) {
  const m = Math.floor(s / 60);
  return m > 0 ? `${m}m ${Math.floor(s % 60)}s` : `${Math.floor(s)}s`;
}
function shortId(uuid) { return uuid ? uuid.slice(0, 8) : "—"; }
function shortAccount(acc) { return acc ? acc.slice(0, 8) : "—"; }

function addFeedRows(transactions) {
  const frag = document.createDocumentFragment();
  for (const tx of transactions) {
    const tr = document.createElement("tr");
    if (tx.is_flagged) tr.classList.add("fraud-row");
    const time = tx.timestamp ? tx.timestamp.slice(11, 19) : "";
    tr.innerHTML = `
      <td>${time}</td>
      <td><span class="type-${tx.type}">${tx.type}</span></td>
      <td>${fmtAmount(tx.amount)}</td>
      <td>${shortAccount(tx.account_orig)}</td>
      <td>${shortAccount(tx.account_dest)}</td>
      <td>${tx.location || "—"}</td>
      <td>${tx.is_flagged ? '<span class="status-fraud">🚨 FRAUD</span>' : '<span class="status-ok">✔ OK</span>'}</td>
    `;
    frag.prepend(tr);
    feedRowCount++;
  }
  feedBody.prepend(frag);
  while (feedBody.children.length > MAX_FEED_ROWS) feedBody.removeChild(feedBody.lastChild);
  feedCount.textContent = `${Math.min(feedRowCount, MAX_FEED_ROWS)} rows`;
}

function addAlerts(alerts) {
  for (const tx of alerts) {
    const div = document.createElement("div");
    div.className = "alert-item";
    const rulesHtml = (tx.fraud_rules || []).map(r => `<span class="rule-badge">${r}</span>`).join("");
    div.innerHTML = `
      <div class="alert-id">${shortId(tx.transaction_id)}</div>
      <div class="alert-amount">${fmtAmount(tx.amount)}</div>
      <div class="alert-rules">${rulesHtml}</div>
      <div class="alert-meta">${tx.type} · ${tx.location || ""} · ${tx.timestamp ? tx.timestamp.slice(0, 16) : ""}</div>
    `;
    alertsList.prepend(div);
    alertItemCount++;
  }
  while (alertsList.children.length > MAX_ALERT_ITEMS) alertsList.removeChild(alertsList.lastChild);
  alertCount.textContent = `${alertItemCount} alerts`;
}

function updateStats(stats) {
  if (!stats) return;
  statTps.textContent     = stats.rows_per_second  != null ? stats.rows_per_second.toFixed(1) : "—";
  statTotal.textContent   = stats.total_processed  != null ? stats.total_processed.toLocaleString() : "—";
  statFraud.textContent   = stats.total_fraud       != null ? stats.total_fraud.toLocaleString() : "—";
  statRate.textContent    = stats.fraud_rate        != null ? stats.fraud_rate.toFixed(2) + "%" : "—";
  statBatches.textContent = stats.batches           != null ? stats.batches.toLocaleString() : "—";
  statUptime.textContent  = stats.elapsed_seconds   != null ? fmtUptime(stats.elapsed_seconds) : "—";
  batchNum.textContent    = stats.batches ?? 0;
}

let chartTick = 0;
function updateCharts(transactions, stats) {
  chartTick++;
  if (chartTick % 3 === 0 && stats?.rows_per_second != null) {
    tpsHistory.push(stats.rows_per_second);
    if (tpsHistory.length > MAX_CHART_POINTS) tpsHistory.shift();
    tpsChart.data.labels = tpsHistory.map((_, i) => i);
    tpsChart.data.datasets[0].data = tpsHistory;
    tpsChart.update();
  }
  for (const tx of transactions) {
    if (typeCounts[tx.type] !== undefined) typeCounts[tx.type]++;
  }
  typesChart.data.datasets[0].data = Object.values(typeCounts);
  typesChart.update();

  if (stats?.rule_counts) {
    Object.assign(ruleCounts, stats.rule_counts);
    rulesChart.data.datasets[0].data = Object.values(ruleCounts);
    rulesChart.update();
  }
}

function handleBatch(msg) {
  const txns   = msg.transactions || [];
  const alerts = msg.alerts       || [];
  const stats  = msg.stats        || null;
  if (txns.length)   addFeedRows(txns);
  if (alerts.length) addAlerts(alerts);
  if (stats)         updateStats(stats);
  if (txns.length)   updateCharts(txns, stats);
  if (stats?.batches != null) batchRows.textContent = txns.length;
}

/* ═══════════════════════════════════════════════════════════════════════
   CHARTS
═══════════════════════════════════════════════════════════════════════ */
const chartDefaults = {
  animation: false, responsive: true, maintainAspectRatio: true,
  plugins: { legend: { labels: { color: "#8b949e", font: { size: 11 } } } },
};
const tpsChart = new Chart($("chart-tps"), {
  type: "line",
  data: { labels: [], datasets: [{ label: "rows/sec", data: [],
    borderColor: "#58a6ff", backgroundColor: "rgba(88,166,255,0.08)",
    fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 }] },
  options: { ...chartDefaults, scales: {
    x: { display: false },
    y: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" } } } },
});
const typesChart = new Chart($("chart-types"), {
  type: "doughnut",
  data: { labels: Object.keys(typeCounts),
    datasets: [{ data: Object.values(typeCounts),
      backgroundColor: ["#58a6ff","#d29922","#3fb950","#8b949e","#bc8cff"], borderWidth: 0 }] },
  options: { ...chartDefaults, cutout: "60%" },
});
const rulesChart = new Chart($("chart-rules"), {
  type: "bar",
  data: { labels: Object.keys(ruleCounts),
    datasets: [{ label: "Detections", data: Object.values(ruleCounts),
      backgroundColor: ["#f85149","#d29922","#bc8cff","#ff7b72"], borderRadius: 4 }] },
  options: { ...chartDefaults, scales: {
    x: { ticks: { color: "#8b949e", font: { size: 10 } }, grid: { display: false } },
    y: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" } } },
    plugins: { legend: { display: false } } },
});

/* ═══════════════════════════════════════════════════════════════════════
   CONNECTION — WebSocket with simulator fallback
═══════════════════════════════════════════════════════════════════════ */
let simInterval = null;

function startSimulator() {
  if (simInterval) return;
  wsStatus.textContent  = "● Demo mode";
  wsStatus.className    = "badge badge-demo";
  simInterval = setInterval(() => {
    handleBatch(generateSimBatch(SIM_BATCH_SIZE));
  }, BATCH_INTERVAL_MS);
}

let ws, reconnectDelay = 1500, wsConnected = false;
// If on GitHub Pages, skip WebSocket attempt entirely
const skipWS = IS_GITHUB_PAGES || WS_URL === "";

if (skipWS) {
  startSimulator();
} else {
  // Try WebSocket; fall back to simulator after 4 s
  const fallbackTimer = setTimeout(() => {
    if (!wsConnected) {
      console.info("WebSocket unavailable — switching to simulator.");
      startSimulator();
    }
  }, 4000);

  function connect() {
    try { ws = new WebSocket(WS_URL); } catch { startSimulator(); return; }

    ws.onopen = () => {
      wsConnected = true;
      clearTimeout(fallbackTimer);
      if (simInterval) { clearInterval(simInterval); simInterval = null; }
      wsStatus.textContent = "● Connected";
      wsStatus.className   = "badge badge-online";
      reconnectDelay = 1500;
    };
    ws.onclose = () => {
      wsStatus.textContent = "● Reconnecting…";
      wsStatus.className   = "badge badge-offline";
      if (!simInterval) setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 15000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = ({ data }) => {
      let msg; try { msg = JSON.parse(data); } catch { return; }
      handleBatch(msg);
    };
  }
  connect();
}
