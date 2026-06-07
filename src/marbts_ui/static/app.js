const state = {
  overview: null,
  scenarios: [],
  selectedScenarioPath: "scenarios/baselines/rule_baseline.json",
  scenarioDetail: null,
  runs: [],
  selectedRun: null,
  reports: [],
  containerSpecs: [],
  currentRunResult: null
};

const $ = (selector) => document.querySelector(selector);
const THEME_STORAGE_KEY = "marbts.theme";

function storedTheme() {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "dark";
  } catch {
    return "dark";
  }
}

function applyTheme(theme) {
  const resolvedTheme = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = resolvedTheme;
  const toggle = $("#themeToggle");
  const label = $("#themeLabel");
  if (toggle) toggle.checked = resolvedTheme === "dark";
  if (label) label.textContent = resolvedTheme === "dark" ? "Dark" : "Light";
}

function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    return;
  }
}

function initTheme() {
  applyTheme(storedTheme());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function compactPath(path) {
  const value = String(path ?? "");
  if (value.length <= 44) return value;
  return value.slice(0, 18) + "..." + value.slice(-22);
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || response.statusText);
  }
  return payload;
}

function setBusy(button, busy, label) {
  if (!button) return;
  if (busy) {
    button.dataset.originalText = button.textContent;
    button.textContent = label || "Working";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

function renderMetricGrid(target, metrics) {
  target.innerHTML = metrics.map((metric) => `
    <div class="metric">
      <span class="label">${escapeHtml(metric.label)}</span>
      <span class="value">${escapeHtml(metric.value)}</span>
    </div>
  `).join("");
}

function renderOverview() {
  if (!state.overview) return;
  $("#projectRoot").textContent = state.overview.project_root;
  $("#overviewStats").innerHTML = [
    ["Scenarios", state.overview.scenario_count],
    ["Runs", state.overview.run_count],
    ["Metrics", state.overview.metric_count],
    ["Reports", state.overview.report_count]
  ].map(([label, value]) => `<span class="stat-chip"><strong>${value}</strong>${label}</span>`).join("");
}

async function loadOverview() {
  state.overview = await api("/api/overview");
  renderOverview();
}

async function loadScenarios() {
  const payload = await api("/api/scenarios");
  state.scenarios = payload.scenarios || [];
  if (!state.scenarios.some((item) => item.scenario_path === state.selectedScenarioPath) && state.scenarios[0]) {
    state.selectedScenarioPath = state.scenarios[0].scenario_path;
  }
  renderScenarioRows();
  fillScenarioSelects();
  await selectScenario(state.selectedScenarioPath);
}

function renderScenarioRows() {
  const filter = ($("#scenarioSearch").value || "").toLowerCase();
  const rows = state.scenarios.filter((item) => {
    const haystack = [
      item.scenario_id,
      item.version,
      item.source_group,
      item.scenario_path,
      ...(item.tags || [])
    ].join(" ").toLowerCase();
    return haystack.includes(filter);
  });
  $("#scenarioCount").textContent = `${rows.length} scenarios`;
  $("#scenarioRows").innerHTML = rows.map((item) => {
    const selected = item.scenario_path === state.selectedScenarioPath ? "selected" : "";
    const tags = (item.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
    return `
      <tr class="${selected}" data-scenario-path="${escapeHtml(item.scenario_path)}">
        <td><strong>${escapeHtml(item.scenario_id)}</strong><br><span class="muted">${escapeHtml(compactPath(item.scenario_path))}</span></td>
        <td>${escapeHtml(item.source_group)}</td>
        <td>${escapeHtml(item.node_count)}</td>
        <td>${escapeHtml(item.edge_count)}</td>
        <td><div class="tag-list">${tags}</div></td>
      </tr>
    `;
  }).join("");
  document.querySelectorAll("#scenarioRows tr").forEach((row) => {
    row.addEventListener("click", () => selectScenario(row.dataset.scenarioPath));
  });
}

function fillScenarioSelects() {
  const options = state.scenarios.map((item) => {
    const selected = item.scenario_path === state.selectedScenarioPath ? "selected" : "";
    return `<option value="${escapeHtml(item.scenario_path)}" ${selected}>${escapeHtml(item.scenario_id)} (${escapeHtml(item.source_group)})</option>`;
  }).join("");
  [
    "#runScenario",
    "#multiSeedScenario",
    "#matrixScenario",
    "#ablationScenario"
  ].forEach((selector) => {
    const element = $(selector);
    if (element) element.innerHTML = options;
  });
}

async function selectScenario(path) {
  if (!path) return;
  state.selectedScenarioPath = path;
  renderScenarioRows();
  fillScenarioSelects();
  const payload = await api(`/api/scenario?path=${encodeURIComponent(path)}`);
  state.scenarioDetail = payload;
  $("#scenarioTitle").textContent = payload.summary.scenario_id;
  $("#scenarioVersion").textContent = payload.summary.version;
  renderMetricGrid($("#scenarioMetrics"), [
    { label: "Nodes", value: payload.summary.node_count },
    { label: "Edges", value: payload.summary.edge_count },
    { label: "Vulnerabilities", value: payload.summary.vulnerabilities_count },
    { label: "Avg Security", value: payload.summary.average_security_level },
    { label: "Isolated", value: payload.summary.isolated_nodes },
    { label: "Initial Compromised", value: payload.summary.initial_compromised_nodes }
  ]);
  drawGraph($("#scenarioGraph"), payload.graph);
}

async function validateScenarioJson() {
  const output = $("#scenarioValidationResult");
  try {
    const payload = JSON.parse($("#scenarioJsonEditor").value);
    const result = await api("/api/scenarios/validate", {
      method: "POST",
      body: JSON.stringify({ payload })
    });
    output.textContent = prettyJson(result.summary);
    showToast("Scenario JSON is valid");
  } catch (error) {
    output.textContent = String(error.message || error);
    showToast("Scenario validation failed");
  }
}

function loadSelectedScenarioJson() {
  if (!state.scenarioDetail) return;
  $("#scenarioJsonEditor").value = prettyJson(state.scenarioDetail.raw);
  $("#scenarioValidationResult").textContent = "";
}

function drawGraph(svg, graph) {
  if (!svg) return;
  svg.innerHTML = "";
  svg.setAttribute("viewBox", "0 0 820 430");
  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", "410");
    text.setAttribute("y", "215");
    text.setAttribute("class", "graph-label");
    text.textContent = "No graph";
    svg.appendChild(text);
    return;
  }

  const nodes = [...graph.nodes].sort((a, b) => String(a.id).localeCompare(String(b.id)));
  const edges = graph.edges || [];
  const positions = {};
  const centerX = 410;
  const centerY = 206;
  const radius = Math.max(90, Math.min(165, 42 * nodes.length));
  nodes.forEach((node, index) => {
    const angle = (-Math.PI / 2) + (index / Math.max(1, nodes.length)) * Math.PI * 2;
    positions[node.id] = {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius
    };
  });

  const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  svg.appendChild(edgeLayer);
  svg.appendChild(nodeLayer);

  edges.forEach((edge) => {
    const source = positions[edge.source];
    const target = positions[edge.target];
    if (!source || !target) return;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", source.x);
    line.setAttribute("y1", source.y);
    line.setAttribute("x2", target.x);
    line.setAttribute("y2", target.y);
    line.setAttribute("class", "graph-edge");
    edgeLayer.appendChild(line);
  });

  nodes.forEach((node) => {
    const pos = positions[node.id];
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const compromised = node.compromised_state || "none";
    const isolated = node.isolation_state ? " isolated" : "";
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", "34");
    circle.setAttribute("class", `graph-node ${compromised === "none" ? "clean" : compromised}${isolated}`);
    group.appendChild(circle);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y - 2);
    label.setAttribute("class", "graph-label");
    label.textContent = node.id;
    group.appendChild(label);

    const sub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    sub.setAttribute("x", pos.x);
    sub.setAttribute("y", pos.y + 15);
    sub.setAttribute("class", "graph-sub");
    sub.textContent = `sec ${node.security_level}`;
    group.appendChild(sub);

    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = [
      node.id,
      `type=${node.node_type}`,
      `state=${node.compromised_state}`,
      `detection=${node.detection_state}`,
      `isolated=${Boolean(node.isolation_state)}`,
      `services=${(node.services || []).join(",")}`,
      `vulns=${(node.vulnerabilities || []).join(",")}`
    ].join("\n");
    group.appendChild(title);
    nodeLayer.appendChild(group);
  });
}

async function runSimulation() {
  const button = $("#runSimulation");
  setBusy(button, true, "Running");
  $("#runStatus").textContent = "Running";
  try {
    const adaptiveConfig = {
      planning_horizon: Number($("#planningHorizon").value),
      exploration_bias: Number($("#explorationBias").value),
      decision_noise: Number($("#decisionNoise").value),
      reduced_observability: $("#reducedObservability").checked,
      enable_decoy: $("#enableDecoy").checked,
      enable_bluff: $("#enableBluff").checked
    };
    const payload = await api("/api/simulations/run", {
      method: "POST",
      body: JSON.stringify({
        scenario_path: $("#runScenario").value,
        seed: Number($("#runSeed").value),
        horizon: Number($("#runHorizon").value),
        red_policy: $("#redPolicy").value,
        blue_policy: $("#bluePolicy").value,
        adaptive_config: adaptiveConfig
      })
    });
    state.currentRunResult = payload;
    renderRunResult(payload);
    await loadOverview();
    await loadRuns();
    showToast("Simulation complete");
  } catch (error) {
    $("#runStatus").textContent = "Error";
    showToast(error.message);
  } finally {
    setBusy(button, false);
  }
}

function renderRunResult(result) {
  $("#runStatus").textContent = result.metadata.run_id;
  const security = result.baseline_metrics.security_outcomes || {};
  const policy = result.baseline_metrics.policy_performance || {};
  renderMetricGrid($("#runMetrics"), [
    { label: "Run ID", value: result.metadata.run_id },
    { label: "Final Compromised", value: security.final_compromised_nodes },
    { label: "Max Compromised", value: security.max_compromised_nodes },
    { label: "Blue Containment", value: policy.blue_containment_actions },
    { label: "First Containment", value: policy.first_containment_timestep },
    { label: "Sequence Hash", value: result.baseline_metrics.sequence_hash.slice(0, 12) }
  ]);

  const slider = $("#snapshotSlider");
  slider.min = 0;
  slider.max = Math.max(0, result.snapshots.length - 1);
  slider.value = result.snapshots.length - 1;
  renderSnapshot(Number(slider.value));
  renderTimeline($("#runTimeline"), result.timeline || []);
}

function renderSnapshot(index) {
  const result = state.currentRunResult;
  if (!result) return;
  const snapshot = result.snapshots[index] || result.snapshots[0];
  $("#snapshotLabel").textContent = snapshot.label;
  drawGraph($("#runGraph"), snapshot.graph);
}

function renderTimeline(target, items) {
  target.innerHTML = items.map((item) => {
    const red = item.red_action || item.red_action_intent || {};
    const blue = item.blue_action || item.blue_action_intent || {};
    const delta = item.metric_delta || {};
    return `
      <div class="timeline-item">
        <div class="timeline-title">
          <span>Turn ${escapeHtml(item.timestep)}</span>
          <span class="muted">Compromised ${escapeHtml(delta.compromised_nodes_before ?? "")} to ${escapeHtml(delta.compromised_nodes_after ?? "")}</span>
        </div>
        <div class="action-row"><span class="actor-red">Red</span><span>${escapeHtml(red.action_type)} ${escapeHtml((red.targets || []).join(", "))}</span></div>
        <div class="muted">${escapeHtml(red.rationale || "")}</div>
        <div class="action-row"><span class="actor-blue">Blue</span><span>${escapeHtml(blue.action_type)} ${escapeHtml((blue.targets || []).join(", "))}</span></div>
        <div class="muted">${escapeHtml(blue.rationale || "")}</div>
      </div>
    `;
  }).join("");
}

async function loadRuns() {
  const payload = await api("/api/runs");
  state.runs = payload.runs || [];
  renderRuns();
  fillRunSelects();
}

function renderRuns() {
  $("#runRows").innerHTML = state.runs.map((run) => `
    <tr data-run-id="${escapeHtml(run.run_id)}">
      <td><strong>${escapeHtml(run.run_id)}</strong><br><span class="muted">${escapeHtml(compactPath(run.run_dir))}</span></td>
      <td>${escapeHtml(run.scenario_id)}</td>
      <td>${escapeHtml(run.seed)}</td>
      <td>${escapeHtml(run.horizon)}</td>
      <td>${escapeHtml(run.final_compromised_nodes ?? "")}</td>
    </tr>
  `).join("");
  document.querySelectorAll("#runRows tr").forEach((row) => {
    row.addEventListener("click", () => selectRun(row.dataset.runId));
  });
}

function fillRunSelects() {
  const options = state.runs.map((run) => `
    <option value="${escapeHtml(run.run_id)}">${escapeHtml(run.run_id)} - ${escapeHtml(run.scenario_id)}</option>
  `).join("");
  ["#compareLeft", "#compareRight"].forEach((selector) => {
    const element = $(selector);
    if (element) element.innerHTML = options;
  });
  if ($("#compareRight") && $("#compareRight").options.length > 1) {
    $("#compareRight").selectedIndex = 1;
  }
}

async function selectRun(runId) {
  if (!runId) return;
  const payload = await api(`/api/runs/${encodeURIComponent(runId)}`);
  state.selectedRun = payload;
  $("#replayTitle").textContent = payload.summary.run_id;
  $("#replayIntegrity").textContent = payload.summary.sequence_hash_matches ? "Integrity OK" : "Hash Drift";
  renderMetricGrid($("#replayMetrics"), [
    { label: "Scenario", value: payload.summary.scenario_id },
    { label: "Seed", value: payload.summary.seed },
    { label: "Horizon", value: payload.summary.horizon },
    { label: "Final Compromised", value: payload.summary.final_compromised_nodes },
    { label: "Blue Containment", value: payload.summary.blue_containment_actions },
    { label: "First Containment", value: payload.summary.first_containment_timestep }
  ]);
  const timeline = (payload.frames || []).map((frame) => ({
    timestep: frame.timestep,
    red_action: frame.red_action,
    blue_action: frame.blue_action,
    metric_delta: frame.metric_delta
  }));
  renderTimeline($("#replayTimeline"), timeline);
}

async function loadReports() {
  const payload = await api("/api/reports");
  state.reports = payload.reports || [];
  renderReports();
}

function reportSummaryText(report) {
  const summary = report.summary || {};
  const parts = Object.entries(summary)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .slice(0, 4)
    .map(([key, value]) => `${key}=${Array.isArray(value) ? value.join(",") : value}`);
  return parts.join(" | ");
}

function renderReports() {
  $("#reportRows").innerHTML = state.reports.map((report) => `
    <tr data-artifact-path="${escapeHtml(report.path)}">
      <td><strong>${escapeHtml(report.name)}</strong><br><span class="muted">${escapeHtml(compactPath(report.path))}</span></td>
      <td>${escapeHtml(report.type)}</td>
      <td>${escapeHtml(reportSummaryText(report))}</td>
    </tr>
  `).join("");
  document.querySelectorAll("#reportRows tr").forEach((row) => {
    row.addEventListener("click", () => loadArtifact(row.dataset.artifactPath));
  });
}

async function loadArtifact(path) {
  const payload = await api(`/api/artifact?path=${encodeURIComponent(path)}`);
  $("#artifactTitle").textContent = compactPath(payload.path);
  $("#artifactKind").textContent = payload.kind;
  $("#artifactViewer").textContent = payload.kind === "json" ? prettyJson(payload.payload) : payload.text;
}

async function runReport(buttonSelector, endpoint, body, pickArtifact) {
  const button = $(buttonSelector);
  setBusy(button, true, "Generating");
  try {
    const payload = await api(endpoint, { method: "POST", body: JSON.stringify(body) });
    await loadOverview();
    await loadRuns();
    await loadReports();
    const artifact = pickArtifact ? pickArtifact(payload) : payload.report_file;
    if (artifact) await loadArtifact(artifact);
    showToast("Report generated");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(button, false);
  }
}

function bindReportButtons() {
  $("#runMultiSeed").addEventListener("click", () => runReport("#runMultiSeed", "/api/reports/multi-seed", {
    scenario_path: $("#multiSeedScenario").value,
    seeds: $("#multiSeedSeeds").value,
    horizon: Number($("#multiSeedHorizon").value)
  }));

  $("#runMatrix").addEventListener("click", () => runReport("#runMatrix", "/api/reports/policy-matrix", {
    scenario_path: $("#matrixScenario").value,
    scenario_batch: $("#matrixBatch").value,
    seeds: $("#matrixSeeds").value,
    horizon: Number($("#matrixHorizon").value),
    include_ablations: $("#matrixAblations").checked
  }));

  $("#runStress").addEventListener("click", () => runReport("#runStress", "/api/reports/stress-suite", {
    seeds: $("#stressSeeds").value,
    horizon: Number($("#stressHorizon").value)
  }));

  $("#runAblation").addEventListener("click", () => runReport("#runAblation", "/api/reports/ablation", {
    scenario_path: $("#ablationScenario").value,
    seeds: $("#ablationSeeds").value,
    horizon: Number($("#ablationHorizon").value),
    include_ablations: $("#ablationAblations").checked,
    containerized: $("#ablationContainerized").checked
  }, (payload) => payload.template_file || payload.matrix_report_file));

  $("#runCompare").addEventListener("click", () => runReport("#runCompare", "/api/reports/compare", {
    left_run_id: $("#compareLeft").value,
    right_run_id: $("#compareRight").value
  }, (payload) => payload.report_file));
}

async function loadContainerSpecs() {
  const payload = await api("/api/container/specs");
  state.containerSpecs = payload.specs || [];
  $("#containerSpec").innerHTML = state.containerSpecs.map((spec) => `
    <option value="${escapeHtml(spec.spec_id)}">${escapeHtml(spec.spec_id)}</option>
  `).join("");
}

async function resolveContainerProfile() {
  const button = $("#resolveContainerProfile");
  setBusy(button, true, "Resolving");
  try {
    const payload = await api("/api/container/profile", {
      method: "POST",
      body: JSON.stringify({
        spec_id: $("#containerSpec").value,
        build_image: $("#containerBuild").checked,
        no_rm: $("#containerNoRm").checked,
        execute: $("#containerExecute").checked
      })
    });
    $("#containerCommand").textContent = prettyJson(payload);
    showToast("Container profile ready");
  } catch (error) {
    $("#containerCommand").textContent = error.message;
    showToast(error.message);
  } finally {
    setBusy(button, false);
  }
}

async function runReleaseValidation() {
  const button = $("#runReleaseValidation");
  setBusy(button, true, "Running");
  try {
    const payload = await api("/api/release-validation", {
      method: "POST",
      body: JSON.stringify({})
    });
    const report = payload.report || {};
    renderMetricGrid($("#releaseMetrics"), [
      { label: "All Gates", value: report.all_gates_pass ? "Pass" : "Fail" },
      { label: "Gate Count", value: report.gate_count },
      { label: "Pass", value: report.pass_count },
      { label: "Fail", value: report.fail_count },
      { label: "Report", value: payload.report_file || "not written" }
    ]);
    $("#releaseGates").innerHTML = (report.gates || []).map((gate) => `
      <div class="gate">
        <span class="gate-status ${escapeHtml(gate.status)}">${escapeHtml(gate.status)}</span>
        <div>
          <strong>${escapeHtml(gate.gate_id)}</strong>
          <div>${escapeHtml(gate.description)}</div>
          <div class="muted">${escapeHtml(gate.evidence || gate.failure_detail)}</div>
        </div>
      </div>
    `).join("");
    await loadOverview();
    await loadReports();
    showToast("Release validation complete");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(button, false);
  }
}

function bindNavigation() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
      $(`#view-${button.dataset.view}`).classList.add("active");
    });
  });
}

function bindEvents() {
  bindNavigation();
  bindReportButtons();
  $("#themeToggle").addEventListener("change", (event) => {
    const theme = event.target.checked ? "dark" : "light";
    saveTheme(theme);
    applyTheme(theme);
    showToast(`${theme === "dark" ? "Dark" : "Light"} mode`);
  });
  $("#refreshScenarios").addEventListener("click", () => loadScenarios().catch((error) => showToast(error.message)));
  $("#scenarioSearch").addEventListener("input", renderScenarioRows);
  $("#loadSelectedScenarioJson").addEventListener("click", loadSelectedScenarioJson);
  $("#validateScenarioJson").addEventListener("click", validateScenarioJson);
  $("#runSimulation").addEventListener("click", runSimulation);
  $("#snapshotSlider").addEventListener("input", (event) => renderSnapshot(Number(event.target.value)));
  $("#refreshRuns").addEventListener("click", () => loadRuns().catch((error) => showToast(error.message)));
  $("#refreshReports").addEventListener("click", () => loadReports().catch((error) => showToast(error.message)));
  $("#resolveContainerProfile").addEventListener("click", resolveContainerProfile);
  $("#runReleaseValidation").addEventListener("click", runReleaseValidation);
  $("#copyRunArtifactPath").addEventListener("click", async () => {
    const path = state.currentRunResult?.artifacts?.run_dir;
    if (!path) return;
    try {
      await navigator.clipboard.writeText(path);
      showToast("Artifact path copied");
    } catch {
      showToast(path);
    }
  });
}

async function init() {
  initTheme();
  bindEvents();
  try {
    await loadOverview();
    await loadScenarios();
    await loadRuns();
    await loadReports();
    await loadContainerSpecs();
    loadSelectedScenarioJson();
  } catch (error) {
    showToast(error.message);
  }
}

document.addEventListener("DOMContentLoaded", init);
