const $ = (id) => document.getElementById(id);

const state = {
  featureId: null,
  results: []
};

function getCssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function drawReleaseChart(enabledCount, disabledCount) {
  const canvas = $("releaseChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.34;
  const innerRadius = radius * 0.58;
  const total = enabledCount + disabledCount;

  ctx.clearRect(0, 0, width, height);
  if (!total) {
    ctx.fillStyle = "#95a3b8";
    ctx.font = "14px Segoe UI";
    ctx.fillText("Sem dados ainda", cx - 48, cy);
    return;
  }

  const colors = [getCssVar("--ok"), getCssVar("--err")];
  const values = [enabledCount, disabledCount];
  const labels = ["Liberados", "Bloqueados"];
  let startAngle = -Math.PI / 2;

  values.forEach((value, i) => {
    const angle = (value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, startAngle + angle);
    ctx.closePath();
    ctx.fillStyle = colors[i];
    ctx.fill();
    startAngle += angle;
  });

  ctx.globalCompositeOperation = "destination-out";
  ctx.beginPath();
  ctx.arc(cx, cy, innerRadius, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalCompositeOperation = "source-over";

  ctx.fillStyle = "#10233f";
  ctx.font = "bold 18px Segoe UI";
  ctx.fillText(String(total), cx - 8, cy + 5);
  ctx.font = "12px Segoe UI";
  ctx.fillStyle = "#5f6c80";
  ctx.fillText("usuários", cx - 24, cy + 24);

  labels.forEach((label, i) => {
    const y = 20 + i * 18;
    ctx.fillStyle = colors[i];
    ctx.fillRect(12, y - 9, 10, 10);
    ctx.fillStyle = "#34445b";
    ctx.font = "12px Segoe UI";
    ctx.fillText(`${label}: ${values[i]}`, 28, y);
  });
}

function drawSourceChart(sourceCounts) {
  const canvas = $("sourceChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const labels = ["ml", "rollout", "feature_disabled", "feature_not_found"];
  const values = labels.map((k) => sourceCounts[k] || 0);
  const maxValue = Math.max(1, ...values);
  const pad = 30;
  const barGap = 16;
  const barWidth = (width - pad * 2 - barGap * (labels.length - 1)) / labels.length;

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#d5ddeb";
  ctx.beginPath();
  ctx.moveTo(pad, height - pad);
  ctx.lineTo(width - pad, height - pad);
  ctx.stroke();

  labels.forEach((label, i) => {
    const value = values[i];
    const x = pad + i * (barWidth + barGap);
    const barHeight = ((height - pad * 2) * value) / maxValue;
    const y = height - pad - barHeight;
    ctx.fillStyle = label === "ml" ? "#135dff" : label === "rollout" ? "#0a8f4d" : "#b67a00";
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#34445b";
    ctx.font = "11px Segoe UI";
    ctx.fillText(String(value), x + barWidth / 2 - 4, y - 4);
    ctx.fillText(label, x - 2, height - 10);
  });
}

function setStatus(text, cls = "") {
  const el = $("apiStatus");
  el.className = `status ${cls}`;
  el.textContent = text;
}

function baseUrl() {
  return $("baseUrl").value.trim().replace(/\/$/, "");
}

function authHeaders() {
  const token = $("token").value.trim();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function callApi(path, options = {}) {
  const started = performance.now();
  const res = await fetch(`${baseUrl()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {})
    }
  });
  const elapsed = Math.round(performance.now() - started);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (_) { data = text; }
  return { ok: res.ok, status: res.status, data, elapsed };
}

async function loadFeatureByKey(featureKey) {
  const out = await callApi("/features");
  if (!out.ok || !Array.isArray(out.data)) return null;
  return out.data.find((f) => f.key === featureKey) || null;
}

async function upsertFeature() {
  const payload = {
    name: $("featureName").value.trim(),
    key: $("featureKey").value.trim(),
    description: "Criada pelo protótipo simples",
    enabled: $("enabled").checked,
    rollout_percentage: Number($("rollout").value),
    ml_enabled: $("mlEnabled").checked
  };

  if (!payload.name || !payload.key) {
    setStatus("Preencha feature name e key.", "warn");
    return;
  }

  setStatus("Verificando se a feature já existe...");
  const existing = await loadFeatureByKey(payload.key);

  if (existing) {
    const out = await callApi(`/features/${existing.id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    if (!out.ok) {
      setStatus(`Erro ao atualizar feature (${out.status}) em ${out.elapsed}ms\n${JSON.stringify(out.data, null, 2)}`, "err");
      return;
    }
    state.featureId = out.data?.id || existing.id;
    setStatus(`Feature atualizada com sucesso (id=${state.featureId}) em ${out.elapsed}ms.`, "ok");
    return;
  }

  const out = await callApi("/features", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  if (!out.ok) {
    setStatus(`Erro ao criar feature (${out.status}) em ${out.elapsed}ms\n${JSON.stringify(out.data, null, 2)}`, "err");
    return;
  }
  state.featureId = out.data?.id || null;
  setStatus(`Feature criada com sucesso (id=${state.featureId}) em ${out.elapsed}ms.`, "ok");
}

async function listFeatures() {
  const out = await callApi("/features");
  if (!out.ok) {
    setStatus(`Erro ao listar features (${out.status})\n${JSON.stringify(out.data, null, 2)}`, "err");
    return;
  }
  setStatus(`Features carregadas (${out.data.length}) em ${out.elapsed}ms.\n${JSON.stringify(out.data, null, 2)}`, "ok");
}

function resetResults() {
  state.results = [];
  $("resultsBody").innerHTML = "";
  ["mTotal", "mEnabled", "mDisabled", "mRate", "mMl", "mRollout", "mFeatureDisabled", "mFeatureNotFound"].forEach((id) => {
    $(id).textContent = id === "mRate" ? "0%" : "0";
  });
  drawReleaseChart(0, 0);
  drawSourceChart({});
}

function renderResults() {
  const rows = state.results.map((r) => {
    const enabled = r.enabled ? "true" : "false";
    const statusClass = r.eventOk ? "ok" : "err";
    const statusText = r.eventOk ? `ok (${r.eventStatus})` : `falhou (${r.eventStatus})`;
    return `<tr>
      <td>${r.userId}</td>
      <td>${enabled}</td>
      <td>${r.decisionSource || "-"}</td>
      <td>${r.score ?? "-"}</td>
      <td>${r.eventType}</td>
      <td class="${statusClass}">${statusText}</td>
    </tr>`;
  }).join("");
  $("resultsBody").innerHTML = rows;

  const total = state.results.length;
  const enabled = state.results.filter((r) => r.enabled).length;
  const disabled = total - enabled;
  const bySource = (source) => state.results.filter((r) => r.decisionSource === source).length;
  const sourceCounts = {
    ml: bySource("ml"),
    rollout: bySource("rollout"),
    feature_disabled: bySource("feature_disabled"),
    feature_not_found: bySource("feature_not_found")
  };

  $("mTotal").textContent = String(total);
  $("mEnabled").textContent = String(enabled);
  $("mDisabled").textContent = String(disabled);
  $("mRate").textContent = total ? `${((enabled / total) * 100).toFixed(1)}%` : "0%";
  $("mMl").textContent = String(sourceCounts.ml);
  $("mRollout").textContent = String(sourceCounts.rollout);
  $("mFeatureDisabled").textContent = String(sourceCounts.feature_disabled);
  $("mFeatureNotFound").textContent = String(sourceCounts.feature_not_found);
  drawReleaseChart(enabled, disabled);
  drawSourceChart(sourceCounts);
}

async function simulate() {
  const featureKey = $("featureKey").value.trim();
  if (!featureKey) {
    setStatus("Defina uma feature key antes de simular.", "warn");
    return;
  }

  const users = $("users").value
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean);

  if (!users.length) {
    setStatus("Informe pelo menos 1 user_id para simular.", "warn");
    return;
  }

  resetResults();
  setStatus(`Iniciando simulação de ${users.length} usuários...`);

  let evalFailures = 0;

  for (const userId of users) {
    const evalOut = await callApi("/evaluate", {
      method: "POST",
      body: JSON.stringify({
        feature_key: featureKey,
        user: { user_id: userId }
      })
    });

    if (!evalOut.ok) {
      evalFailures += 1;
      state.results.push({
        userId,
        enabled: false,
        decisionSource: "evaluate_error",
        score: null,
        eventType: "not_sent",
        eventOk: false,
        eventStatus: evalOut.status
      });
      continue;
    }

    const enabled = !!evalOut.data?.enabled;
    const decisionSource = evalOut.data?.decision_source || "unknown";
    const score = evalOut.data?.score ?? null;
    const eventType = enabled ? "viewed_feature" : "viewed_default_checkout";

    const eventOut = await callApi("/events", {
      method: "POST",
      body: JSON.stringify({
        source: "prototype_web",
        user_id: userId,
        feature_key: featureKey,
        event_type: eventType,
        timestamp: new Date().toISOString(),
        properties: {
          decision_source: decisionSource,
          score
        }
      })
    });

    state.results.push({
      userId,
      enabled,
      decisionSource,
      score,
      eventType,
      eventOk: eventOut.ok,
      eventStatus: eventOut.status
    });
  }

  renderResults();

  const okEvents = state.results.filter((r) => r.eventOk).length;
  setStatus(
    `Simulação concluída. users=${users.length}, evaluate_errors=${evalFailures}, eventos_salvos=${okEvents}`,
    evalFailures ? "warn" : "ok"
  );
}

$("upsertFeatureBtn").addEventListener("click", upsertFeature);
$("loadFeaturesBtn").addEventListener("click", listFeatures);
$("simulateBtn").addEventListener("click", simulate);
$("clearBtn").addEventListener("click", () => {
  resetResults();
  setStatus("Resultados limpos.");
});

resetResults();
