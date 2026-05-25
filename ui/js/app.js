const $ = (id) => document.getElementById(id);

const setText = (id, value) => {
  const el = $(id);
  if (el) el.textContent = value;
};

const state = {
  page: localStorage.getItem("adaptiveFlags.page") || "dashboard",
  features: [],
  evaluations: [],
  events: [],
  experiments: [],
  experimentsCount: 0,
  modelStatus: null,
  lastSyncAt: null,
  lastStatusPayload: "Nenhum detalhe disponível.",
  statusHistory: [],
  featureFilter: "",
  eventsPage: 1,
  eventsPerPage: 25,
  charts: { release: null, source: null, timeline: null },
};

function baseUrl() {
  const raw = $("baseUrl")?.value?.trim();
  const resolved = raw || localStorage.getItem("adaptiveFlags.baseUrl")?.trim() || window.location.origin;
  return resolved.replace(/\/$/, "");
}

function headers() {
  const token = $("token")?.value?.trim() || localStorage.getItem("adaptiveFlags.token")?.trim() || "";
  const out = {};
  if (token) out.Authorization = `Bearer ${token}`;
  return out;
}

function setStatus(message, data = null) {
  const summary = $("apiStatusSummary");
  const meta = $("apiStatusMeta");
  const payload = $("apiStatusPayload");
  const history = $("statusHistory");
  if (summary) summary.textContent = message;
  if (meta) meta.textContent = `Atualizado em ${new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date())}`;

  if (data === null) {
    state.lastStatusPayload = "Nenhum detalhe disponível.";
    if (payload) payload.textContent = state.lastStatusPayload;
    return;
  }

  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  state.lastStatusPayload = text;
  if (payload) payload.textContent = text;

  state.statusHistory.unshift({
    message,
    payload: text,
    at: new Date().toISOString(),
  });
  state.statusHistory = state.statusHistory.slice(0, 5);
  if (history) {
    history.innerHTML = state.statusHistory.map((entry, index) => {
      const time = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(entry.at));
      return `<button class="history-item" type="button" data-index="${index}">
        <span>${entry.message}</span>
        <small>${time}</small>
      </button>`;
    }).join("");
    history.querySelectorAll(".history-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        const entry = state.statusHistory[Number(btn.dataset.index)];
        if (!entry) return;
        if (summary) summary.textContent = entry.message;
        if (meta) meta.textContent = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "medium" }).format(new Date(entry.at));
        if (payload) payload.textContent = entry.payload;
        state.lastStatusPayload = entry.payload;
      });
    });
  }
}

function setModelStatus(message, data = null) {
  const parts = [message];
  if (data !== null) parts.push(typeof data === "string" ? data : JSON.stringify(data, null, 2));
  const target = $("modelStatusPreview");
  if (target) target.textContent = parts.join("\n\n");
}

function formatLastSync(value) {
  if (!value) return "Sincronização pendente";
  return `Atualizado em ${new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(value)}`;
}

function updateDashboardSummary() {
  setText("overviewFeatures", String(state.features.length));
  setText("overviewEvents", String(state.events.length));
  setText("overviewModel", state.modelStatus?.status ? "Ativo" : "Sem dados");
  setText("overviewLastSync", formatLastSync(state.lastSyncAt));
  setText("overviewSync", formatLastSync(state.lastSyncAt));
  setText("insightLastSync", formatLastSync(state.lastSyncAt));
  const m = metricsFromEvaluations();
  setText("compareMl", String(m.ml));
  setText("compareRollout", String(m.rollout));
  setText("compareDelta", String(Math.abs(m.ml - m.rollout)));
  setText("mEvents", `${state.events.length} / ${state.features.length}`);
  setText("insightLastSyncCard", formatLastSync(state.lastSyncAt));
}

function markDashboardSync() {
  state.lastSyncAt = new Date();
  updateDashboardSummary();
}

function setPage(page, { fromHash = false } = {}) {
  const next = ["dashboard", "insights", "features", "evaluation", "events", "governance"].includes(page) ? page : "dashboard";
  state.page = next;
  localStorage.setItem("adaptiveFlags.page", next);

  document.querySelectorAll(".page").forEach((el) => {
    el.classList.toggle("active", el.dataset.page === next);
  });

  document.querySelectorAll(".nav-item").forEach((btn) => {
    const active = btn.dataset.page === next;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-current", active ? "page" : "false");
  });

  if (!fromHash && window.location.hash && window.location.hash !== `#${next}`) {
    history.replaceState(null, "", `#${next}`);
  }
}

function setLoading(btnId, loadingText) {
  const btn = $(btnId);
  if (!btn) return () => {};
  const prev = btn.textContent;
  btn.disabled = true;
  btn.textContent = loadingText;
  return () => {
    btn.disabled = false;
    btn.textContent = prev;
  };
}

async function api(path, options = {}) {
  const started = performance.now();
  try {
    const finalHeaders = { ...headers(), ...(options.headers || {}) };
    if (options.body !== undefined && options.body !== null && !("Content-Type" in finalHeaders)) {
      finalHeaders["Content-Type"] = "application/json";
    }

    const res = await fetch(`${baseUrl()}${path}`, { ...options, headers: finalHeaders });
    const elapsed = Math.round(performance.now() - started);
    const text = await res.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    return { ok: res.ok, status: res.status, data, elapsed };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      data: { detail: `Falha de rede ao acessar ${path}: ${String(error)}` },
      elapsed: Math.round(performance.now() - started),
    };
  }
}

function normalizeNumber(value, fallback = null) {
  if (value === "" || value === null || value === undefined) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function yesNo(value) {
  return value ? '<span class="pill ok">Sim</span>' : '<span class="pill bad">Não</span>';
}

function enabledLabel(value) {
  return value ? '<span class="pill ok">Liberado</span>' : '<span class="pill bad">Bloqueado</span>';
}

function statusLabel(value) {
  return value ? '<span class="pill ok">Ativa</span>' : '<span class="pill bad">Pausada</span>';
}

function decisionLabel(value) {
  const labels = {
    ml: "Inteligente",
    rollout: "Gradual",
    feature_disabled: "Regra pausada",
    feature_not_found: "Regra não encontrada",
  };
  return labels[value] || value || "-";
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value || "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function metricsFromEvaluations() {
  const total = state.evaluations.length;
  const enabled = state.evaluations.filter((v) => v.enabled).length;
  const disabled = total - enabled;
  const bySource = (src) => state.evaluations.filter((v) => v.decision_source === src).length;
  return {
    total,
    enabled,
    disabled,
    rate: total ? (enabled / total) * 100 : 0,
    ml: bySource("ml"),
    rollout: bySource("rollout"),
    feature_disabled: bySource("feature_disabled"),
    feature_not_found: bySource("feature_not_found"),
  };
}

function updateMetricCards() {
  const m = metricsFromEvaluations();
  $("mTotal").textContent = String(m.total);
  $("mEnabled").textContent = String(m.enabled);
  $("mDisabled").textContent = String(m.disabled);
  $("mRate").textContent = `${m.rate.toFixed(1)}%`;
  $("mMl").textContent = String(m.ml);
  $("mRollout").textContent = String(m.rollout);
  updateDashboardSummary();
}

function renderFeaturesTable() {
  const body = $("featuresBody");
  if (!body) return;
  const filter = state.featureFilter.trim().toLowerCase();
  const filtered = filter
    ? state.features.filter((feature) => {
      const haystack = `${feature.name ?? ""} ${feature.key ?? ""}`.toLowerCase();
      return haystack.includes(filter);
    })
    : state.features;

  $("featuresCount").textContent = `${filtered.length} linhas`;

  if (!filtered.length) {
    body.innerHTML = '<tr><td colspan="5">Nenhuma regra encontrada.</td></tr>';
    return;
  }

  body.innerHTML = filtered.map((feature) => {
    const rollout = feature.rollout_percentage ?? "-";
    return `\n<tr>\n<td>${feature.name ?? "-"}</td>\n<td>${feature.key ?? "-"}</td>\n<td>${rollout === "-" ? "-" : `${rollout}%`}</td>\n<td>${yesNo(feature.ml_enabled)}</td>\n<td>${statusLabel(feature.enabled)}</td>\n</tr>`;
  }).join("");
}

function renderEvaluationTable() {
  $("evaluationCount").textContent = `${state.evaluations.length} linhas`;
  $("evalBody").innerHTML = state.evaluations.length
    ? state.evaluations.map((r) => {
    return `\n<tr>\n<td>${r.user_id}</td>\n<td>${enabledLabel(r.enabled)}</td>\n<td>${decisionLabel(r.decision_source)}</td>\n<td>${r.score ?? "-"}</td>\n<td>${r.threshold ?? "-"}</td>\n<td>${r.experiment?.variant ?? "-"}</td>\n</tr>`;
  }).join("")
    : '<tr><td colspan="6">Nenhuma avaliação feita ainda.</td></tr>';
}

function renderEventsTable() {
  const sorted = [...state.events].sort((a, b) => String(b.timestamp).localeCompare(String(a.timestamp)));
  const perPage = Math.max(1, normalizeNumber($("eventsPerPage")?.value, 25) || 25);
  const totalPages = Math.max(1, Math.ceil(sorted.length / perPage));
  state.eventsPage = Math.min(Math.max(1, state.eventsPage), totalPages);
  const start = (state.eventsPage - 1) * perPage;
  const pageRows = sorted.slice(start, start + perPage);
  $("eventsCount").textContent = `${sorted.length} linhas • página ${state.eventsPage}/${totalPages}`;
  $("eventsBody").innerHTML = pageRows.length
    ? pageRows.map((e) => `\n<tr>\n<td>${formatDateTime(e.timestamp)}</td>\n<td>${e.user_id || "-"}</td>\n<td>${e.feature_key || "-"}</td>\n<td>${e.event_type || "-"}</td>\n<td>${e.properties?.latency_ms ?? "-"}</td>\n</tr>`).join("")
    : '<tr><td colspan="5">Nenhuma atividade encontrada.</td></tr>';

  const typeSummary = $("eventTypeSummary");
  if (typeSummary) {
    const counts = {};
    for (const e of sorted) counts[e.event_type || "-"] = (counts[e.event_type || "-"] || 0) + 1;
    const topTypes = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
    typeSummary.innerHTML = topTypes.length
      ? topTypes.map(([type, count]) => `<span class="pill">${type}: ${count}</span>`).join("")
      : '<span class="pill">Sem tipos registrados</span>';
  }

  const prevBtn = $("eventsPrevBtn");
  const nextBtn = $("eventsNextBtn");
  if (prevBtn) prevBtn.disabled = state.eventsPage <= 1;
  if (nextBtn) nextBtn.disabled = state.eventsPage >= totalPages;
}

function buildTimeline() {
  const bucket = {};
  for (const e of state.events) {
    const dt = new Date(e.timestamp);
    if (Number.isNaN(dt.getTime())) continue;
    const key = `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
    bucket[key] = (bucket[key] || 0) + 1;
  }
  const labels = Object.keys(bucket).sort();
  const values = labels.map((k) => bucket[k]);
  return { labels, values };
}

function drawCharts() {
  if (typeof Chart === "undefined") return;
  const palette = { blue: "#0d67e8", green: "#0f8a52", red: "#cb3748", amber: "#b07a19", gray: "#72839f" };
  const m = metricsFromEvaluations();

  if (state.charts.release) state.charts.release.destroy();
  state.charts.release = new Chart($("releaseChart"), {
    type: "doughnut",
    data: { labels: ["Liberados", "Bloqueados"], datasets: [{ data: [m.enabled, m.disabled], backgroundColor: [palette.green, palette.red], borderWidth: 0 }] },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: "62%",
      plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8 } } },
    },
  });

  if (state.charts.source) state.charts.source.destroy();
  state.charts.source = new Chart($("sourceChart"), {
    type: "bar",
    data: {
      labels: ["Inteligente", "Gradual", "Regra pausada", "Não encontrada"],
      datasets: [{ label: "Decisões", data: [m.ml, m.rollout, m.feature_disabled, m.feature_not_found], backgroundColor: [palette.blue, palette.green, palette.amber, palette.gray], borderRadius: 6 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(16,32,51,0.08)" } },
      },
    },
  });

  const timeline = buildTimeline();
  if (state.charts.timeline) state.charts.timeline.destroy();
  state.charts.timeline = new Chart($("eventsTimelineChart"), {
    type: "line",
    data: {
      labels: timeline.labels,
      datasets: [{ label: "Eventos/dia", data: timeline.values, borderColor: palette.blue, backgroundColor: "rgba(13,103,232,0.12)", fill: true, tension: 0.25, pointRadius: 3 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(16,32,51,0.08)" } },
      },
    },
  });
}

function configureCharts() {
  if (typeof Chart === "undefined") return;
  Chart.defaults.color = "#4c5d73";
  Chart.defaults.font.family = "\"Manrope\", sans-serif";
  Chart.defaults.plugins.tooltip.backgroundColor = "rgba(15, 23, 34, 0.94)";
  Chart.defaults.plugins.tooltip.titleColor = "#ffffff";
  Chart.defaults.plugins.tooltip.bodyColor = "#eaf1fa";
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.cornerRadius = 10;
  Chart.defaults.plugins.tooltip.displayColors = false;
  Chart.defaults.elements.line.borderWidth = 2;
  Chart.defaults.elements.point.radius = 3;
  Chart.defaults.elements.point.hoverRadius = 4;
}

function featurePayload() {
  return {
    name: $("featureName").value.trim(),
    key: $("featureKey").value.trim(),
    description: "Atualizada pela UI",
    enabled: $("enabled").checked,
    rollout_percentage: normalizeNumber($("rollout").value, 0),
    ml_enabled: $("mlEnabled").checked,
    ml_threshold_mode: $("thresholdMode").value,
    ml_threshold_value: normalizeNumber($("thresholdValue").value, 0.1),
  };
}

async function upsertFeature() {
  const release = setLoading("upsertFeatureBtn", "Salvando...");
  try {
    const payload = featurePayload();
    if (!payload.name || !payload.key) {
      setStatus("Informe o nome e o identificador da regra.");
      return;
    }
    const list = await api("/features");
    if (!list.ok || !Array.isArray(list.data)) {
      setStatus(`Erro ao consultar regras (${list.status})`, list.data);
      return;
    }
    const existing = list.data.find((f) => f.key === payload.key);
    const out = existing
      ? await api(`/features/${existing.id}`, { method: "PUT", body: JSON.stringify(payload) })
      : await api("/features", { method: "POST", body: JSON.stringify(payload) });

    if (out.ok) {
      const refreshed = await api("/features");
      state.features = Array.isArray(refreshed.data) ? refreshed.data : state.features;
      updateMetricCards();
      renderFeaturesTable();
      markDashboardSync();
    }

    setStatus(out.ok ? `Regra salva em ${out.elapsed}ms.` : `Erro ao salvar regra (${out.status})`, out.data);
  } finally { release(); }
}

async function listFeatures(btnId = "loadFeaturesBtnFeature") {
  const release = setLoading(btnId, "Carregando...");
  try {
    const out = await api("/features");
    state.features = Array.isArray(out.data) ? out.data : [];
    updateMetricCards();
    renderFeaturesTable();
    markDashboardSync();
    setStatus(out.ok ? `Regras carregadas: ${state.features.length}` : `Erro ao carregar regras (${out.status})`, out.data);
  } finally { release(); }
}

async function runHealth() {
  const release = setLoading("healthBtn", "Testando...");
  try {
    const out = await api("/health");
    if (out.ok) markDashboardSync();
    setStatus(out.ok ? `Sistema disponível em ${out.elapsed}ms` : `Erro ao verificar o sistema (${out.status})`, out.data);
  } finally { release(); }
}

async function loadMetrics() {
  const release = setLoading("metricsBtn", "Carregando...");
  try {
    const out = await api("/metrics");
    if (out.ok) markDashboardSync();
    setStatus(out.ok ? `Métricas carregadas em ${out.elapsed}ms` : `Erro ao carregar métricas (${out.status})`, out.data);
  } finally { release(); }
}

async function trainModel() {
  const release = setLoading("trainBtn", "Treinando...");
  try {
    const out = await api("/train", { method: "POST", body: JSON.stringify({}) });
    setStatus(out.ok ? `Treino concluído em ${out.elapsed}ms` : `Erro no treino (${out.status})`, out.data);
    setModelStatus(out.ok ? `Treino concluído em ${out.elapsed}ms` : `Erro no treino (${out.status})`, out.data);
    if (out.ok) {
      state.modelStatus = out.data;
      markDashboardSync();
    }
  } finally { release(); }
}

async function loadModelStatus() {
  const release = setLoading("modelStatusBtn", "Carregando...");
  try {
    const out = await api("/model/status");
    setStatus(out.ok ? "Status do modelo carregado" : `Erro ao carregar status do modelo (${out.status})`, out.data);
    setModelStatus(out.ok ? "Status do modelo carregado" : `Erro ao carregar status do modelo (${out.status})`, out.data);
    if (out.ok) {
      state.modelStatus = out.data;
      markDashboardSync();
    }
  } finally { release(); }
}

async function loadModelRuns() {
  const release = setLoading("modelRunsBtn", "Carregando...");
  try {
    const out = await api("/model/runs?limit=10");
    const runs = Array.isArray(out.data) ? out.data : Array.isArray(out.data?.runs) ? out.data.runs : [];
    setStatus(out.ok ? `Histórico de treino carregado: ${runs.length}` : `Erro ao carregar histórico de treinos (${out.status})`, out.data);
    setModelStatus(out.ok ? `Histórico de treino carregado: ${runs.length}` : `Erro ao carregar histórico de treinos (${out.status})`, out.data);
    if (out.ok) markDashboardSync();
  } finally { release(); }
}

async function evaluateUsers() {
  const release = setLoading("simulateBtn", "Avaliando...");
  try {
    const featureKey = $("featureKey").value.trim();
    const users = $("users").value.split("\n").map((u) => u.trim()).filter(Boolean);
    if (!featureKey || !users.length) {
      setStatus("Informe o identificador da regra e ao menos um usuário.");
      return;
    }

    const output = [];
    for (const userId of users) {
      const out = await api("/evaluate", {
        method: "POST",
        body: JSON.stringify({ feature_key: featureKey, user: { user_id: userId } }),
      });
      output.push(out.ok ? out.data : { user_id: userId, enabled: false, decision_source: `error_${out.status}` });
    }

    state.evaluations = output;
    updateMetricCards();
    renderEvaluationTable();
    drawCharts();
    markDashboardSync();
    setStatus(`Avaliação concluída para ${users.length} usuários.`);
  } finally { release(); }
}

function clearEvaluations() {
  state.evaluations = [];
  updateMetricCards();
  renderEvaluationTable();
  drawCharts();
  markDashboardSync();
  setStatus("Avaliações limpas.");
}

function operationalMetrics() {
  const out = {};
  const latency = normalizeNumber($("latencyMs").value);
  const errorRate = normalizeNumber($("errorRate").value);
  const cpu = normalizeNumber($("cpuPct").value);
  const mem = normalizeNumber($("memPct").value);
  if (latency !== null) out.latency_ms = latency;
  if (errorRate !== null) out.error_rate = errorRate;
  if (cpu !== null) out.cpu_pct = cpu;
  if (mem !== null) out.mem_pct = mem;
  return out;
}

async function sendEvent(single = true) {
  const btn = single ? "sendEventBtn" : "sendIngestBtn";
  const release = setLoading(btn, "Enviando...");
  try {
    const featureKey = $("featureKey").value.trim();
    const userId = $("eventUserId").value.trim();
    const eventType = $("eventType").value.trim();
    const source = $("eventSource").value.trim() || "ui_manual";
    if (!featureKey || !userId || !eventType) {
      setStatus("Preencha regra, usuário e tipo de atividade.");
      return;
    }

    const baseEvent = {
      user_id: userId,
      feature_key: featureKey,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      properties: operationalMetrics(),
    };

    const out = single
      ? await api("/events", { method: "POST", body: JSON.stringify({ ...baseEvent, source }) })
      : await api("/ingest/events", { method: "POST", body: JSON.stringify({ source, events: [baseEvent] }) });

    setStatus(out.ok ? (single ? "Atividade registrada." : "Atividades registradas em lote.") : `Erro ao registrar atividade (${out.status})`, out.data);
    if (out.ok) markDashboardSync();
  } finally { release(); }
}

async function loadEventsFromDb(btnId = "loadEventsBtn") {
  const release = setLoading(btnId, "Carregando...");
  try {
    const params = new URLSearchParams();
    const user = $("filterUserId").value.trim();
    const feature = $("filterFeatureKey").value.trim();
    const type = $("filterEventType").value.trim();
    if (user) params.set("user_id", user);
    if (feature) params.set("feature_key", feature);
    if (type) params.set("event_type", type);

    const out = await api(params.toString() ? `/events?${params.toString()}` : "/events");
    if (!out.ok || !Array.isArray(out.data)) {
      setStatus(`Erro ao carregar eventos (${out.status})`, out.data);
      return;
    }

    state.events = out.data;
    state.eventsPage = 1;
    renderEventsTable();
    updateMetricCards();
    drawCharts();
    markDashboardSync();
    setStatus(`Eventos carregados: ${state.events.length}`);
  } finally { release(); }
}

async function loadExperiments() {
  const release = setLoading("loadExperimentsBtn", "Carregando...");
  try {
    const out = await api("/experiments");
    state.experiments = Array.isArray(out.data) ? out.data : [];
    state.experimentsCount = state.experiments.length;
    updateDashboardSummary();
    if (out.ok) markDashboardSync();
    setStatus(out.ok ? `Experimentos carregados: ${state.experiments.length}` : `Erro ao carregar experimentos (${out.status})`, out.data);
  } finally { release(); }
}

function bind() {
  const on = (id, fn) => {
    const el = $(id);
    if (!el) return;
    el.addEventListener("click", async () => {
      try { await fn(); } catch (error) { setStatus(`Erro na ação ${id}`, String(error)); }
    });
  };

  on("healthBtn", runHealth);
  on("metricsBtn", loadMetrics);
  on("upsertFeatureBtn", upsertFeature);
  on("loadFeaturesBtnFeature", () => listFeatures("loadFeaturesBtnFeature"));
  on("trainBtn", trainModel);
  on("modelStatusBtn", loadModelStatus);
  on("modelRunsBtn", loadModelRuns);
  on("simulateBtn", evaluateUsers);
  on("clearEvaluationsBtn", clearEvaluations);
  on("sendEventBtn", () => sendEvent(true));
  on("sendIngestBtn", () => sendEvent(false));
  on("loadEventsBtn", loadEventsFromDb);
  on("loadExperimentsBtn", loadExperiments);
  on("eventsPrevBtn", () => {
    state.eventsPage = Math.max(1, state.eventsPage - 1);
    renderEventsTable();
  });
  on("eventsNextBtn", () => {
    state.eventsPage += 1;
    renderEventsTable();
  });
  on("copyStatusBtn", async () => {
    try {
      await navigator.clipboard.writeText(state.lastStatusPayload || "Nenhum detalhe disponível.");
      setStatus("Detalhes copiados para a área de transferência.", state.lastStatusPayload);
    } catch (error) {
      setStatus("Não foi possível copiar os detalhes.", String(error));
    }
  });
  on("clearStatusBtn", () => {
    state.lastStatusPayload = "Nenhum detalhe disponível.";
    state.statusHistory = [];
    const summary = $("apiStatusSummary");
    const meta = $("apiStatusMeta");
    const payload = $("apiStatusPayload");
    const history = $("statusHistory");
    if (summary) summary.textContent = "Pronto.";
    if (meta) meta.textContent = "Aguardando ação.";
    if (payload) payload.textContent = "Nenhum detalhe disponível.";
    if (history) history.innerHTML = "";
  });
  const featureFilter = $("featureFilter");
  if (featureFilter) {
    featureFilter.addEventListener("input", () => {
      state.featureFilter = featureFilter.value;
      renderFeaturesTable();
    });
  }
  const eventsPerPage = $("eventsPerPage");
  if (eventsPerPage) {
    eventsPerPage.addEventListener("change", () => {
      state.eventsPage = 1;
      renderEventsTable();
    });
  }
  document.querySelectorAll(".nav-item[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.page;
      requestAnimationFrame(() => setPage(next, { fromHash: true }));
    });
  });
  window.addEventListener("hashchange", () => setPage(window.location.hash.replace(/^#/, ""), { fromHash: true }));
}

function init() {
  const baseUrlInput = $("baseUrl");
  if (baseUrlInput && !baseUrlInput.value.trim()) {
    baseUrlInput.value = window.location.origin;
  }
  configureCharts();
  const chartScript = $("chartJs");
  if (chartScript && typeof Chart === "undefined") {
    chartScript.addEventListener("load", () => {
      configureCharts();
      drawCharts();
    }, { once: true });
  }
  bind();
  setPage(window.location.hash.replace(/^#/, "") || state.page, { fromHash: Boolean(window.location.hash) });
  updateMetricCards();
  updateDashboardSummary();
  renderFeaturesTable();
  renderEvaluationTable();
  renderEventsTable();
  if (typeof Chart === "undefined") {
    setStatus("Os gráficos não carregaram, mas o restante do painel continua disponível.");
  }
  Promise.allSettled([
    listFeatures("loadFeaturesBtnFeature"),
    loadEventsFromDb("loadEventsBtn"),
    loadModelStatus(),
    loadExperiments(),
  ]).finally(() => drawCharts());
}

document.addEventListener("DOMContentLoaded", init);
