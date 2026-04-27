// Form handling: collect inputs, call Python, render summary cards + charts.

const form = document.getElementById("decision-form");
const emptyState = document.getElementById("empty-state");
const resultsPane = document.getElementById("results-pane");
const sizeSlider = document.getElementById("size-slider");
const sizeReadout = document.getElementById("size-readout");
const pueSlider = document.getElementById("pue-slider");
const pueReadout = document.getElementById("pue-readout");
const metaBadge = document.getElementById("meta-badge");
const durationWrap = document.getElementById("duration-wrap");

let HOURLY_PROFILES = null;

sizeSlider.addEventListener("input", () => {
  sizeReadout.textContent = sizeSlider.value;
});
pueSlider.addEventListener("input", () => {
  pueReadout.textContent = Number(pueSlider.value).toFixed(2);
});

// Show/hide duration sub-radio when resilience mode toggles.
document.querySelectorAll('input[name="resilience"]').forEach((r) => {
  r.addEventListener("change", (e) => {
    if (e.target.value === "Partial island") durationWrap.classList.remove("hidden");
    else durationWrap.classList.add("hidden");
  });
});

window.__onPyodideReady = async (meta) => {
  const dates = Object.values(meta).map((m) => m.refreshed).sort();
  metaBadge.textContent = `Data as of ${dates[dates.length - 1]}`;
  // Pull hourly profiles to JS for heatmap + duck-curve composition.
  try {
    const res = await fetch("data/hourly_profiles.json");
    HOURLY_PROFILES = await res.json();
  } catch (e) {
    console.warn("Could not load hourly profiles:", e);
  }
};

function gatherInputs() {
  const fd = new FormData(form);
  const resilience = fd.get("resilience");
  const duration = resilience === "Partial island" ? (fd.get("duration") || "4 hr") : "n/a";
  return {
    primary_goal:      fd.get("primary_goal"),
    reliability:       fd.get("reliability"),
    carbon_goal:       fd.get("carbon_goal"),
    geography:         fd.get("geography"),
    primary_workload:  fd.get("primary_workload"),
    speed_to_power:    fd.get("speed_to_power"),
    cost_priority:     fd.get("cost_priority"),
    rto:               fd.get("rto"),
    size_mw:           Number(fd.get("size_mw")),
    type:              fd.get("type"),
    ppa:               fd.get("ppa"),
    grid_relationship: fd.get("grid_relationship"),
    resilience,
    duration,
    pue:               Number(fd.get("pue")),
  };
}

function fmtMoney(n) {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${Math.round(n).toLocaleString()}`;
}
function fmtTons(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M t`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}k t`;
  return `${Math.round(n)} t`;
}

function tipText(t) {
  if (!t) return "";
  return [
    `Source: ${t.source}`,
    `Assumptions: ${t.assumptions}`,
    `Formula: ${t.formula}`,
    `Method: ${t.method}`,
  ].join("\n\n");
}

function renderSummaryCards(res) {
  const feasClass = res.feasibility.flag === "Feasible" ? "green" : "red";
  const cards = [
    { label: "Blended LCOE",        value: `$${res.blended_lcoe_per_mwh}/MWh`,
      sub: `Post-IRA $${res.lcoe_post_ira}/MWh`, tip: tipText(res.tooltips.lcoe) },
    { label: "Estimated CapEx",     value: fmtMoney(res.total_capex_usd),
      sub: `PUE ${res.pue} · ${res.effective_mw.toFixed(0)} MW load`,
      tip: tipText(res.tooltips.capex) },
    { label: "Scope 1 emissions",   value: fmtTons(res.emissions.scope1_tons),
      sub: "tCO₂e / yr (on-site)", tip: tipText(res.tooltips.scope1) },
    { label: "Scope 2 (location)",  value: fmtTons(res.emissions.location_tons),
      sub: "tCO₂e / yr (grid avg)", tip: tipText(res.tooltips.scope2) },
    { label: "Scope 2 (market)",    value: fmtTons(res.emissions.market_tons),
      sub: "tCO₂e / yr (PPA-adj)",  tip: tipText(res.tooltips.scope2) },
    { label: "Feasibility",         value: res.feasibility.flag, cls: feasClass,
      sub: res.feasibility.reason || "", tip: tipText(res.tooltips.feasibility) },
  ];

  document.getElementById("summary-cards").innerHTML = cards.map((c) => `
    <div class="summary-card">
      <div class="tip" title="${(c.tip || "").replace(/"/g, "&quot;")}">i</div>
      <div class="label">${c.label}</div>
      <div class="value ${c.cls || ""}">${c.value}</div>
      ${c.sub ? `<div class="sub">${c.sub}</div>` : ""}
    </div>`).join("");
}

function renderRecs(list) {
  document.getElementById("rec-list").innerHTML =
    list.map((r) => `<li>${r}</li>`).join("");
}

let currentResult = null;
let currentInputs = null;
let mixMode = "donut";
let lcoeMode = "pre";

function renderMixChart() {
  if (!currentResult) return;
  if (mixMode === "donut") window.Charts.renderDonut("chart-mix", currentResult.mix_pct);
  else window.Charts.renderSankey("chart-mix",
        currentResult.mix_pct, Number(currentInputs.size_mw), Number(currentInputs.pue));
}
document.getElementById("mix-toggle").addEventListener("click", (e) => {
  const btn = e.target.closest("button"); if (!btn) return;
  document.querySelectorAll("#mix-toggle button").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active"); mixMode = btn.dataset.mode; renderMixChart();
});

function renderWaterfall() {
  if (!currentResult) return;
  window.Charts.renderWaterfall("chart-waterfall",
    currentResult.lcoe_components, currentResult.lcoe_post_ira, lcoeMode);
}
document.getElementById("lcoe-toggle").addEventListener("click", (e) => {
  const btn = e.target.closest("button"); if (!btn) return;
  document.querySelectorAll("#lcoe-toggle button").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active"); lcoeMode = btn.dataset.mode; renderWaterfall();
});

function dominantRenewable(mixPct) {
  return (mixPct.solar || 0) >= (mixPct.wind || 0) ? "solar" : "wind";
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  currentInputs = gatherInputs();
  currentResult = window.runAnalysis(currentInputs);

  emptyState.classList.add("hidden");
  resultsPane.classList.remove("hidden");

  renderSummaryCards(currentResult);

  // Essentials
  window.Charts.renderMap("chart-map", currentInputs.rto);
  renderMixChart();
  window.Charts.renderTrajectory("chart-trajectory",
    currentResult.emissions.market_tons, currentResult.iea_nze,
    Number(currentInputs.size_mw), Number(currentInputs.pue));

  // Advanced
  renderWaterfall();
  window.Charts.renderPareto("chart-pareto",
    currentResult.blended_lcoe_per_mwh, currentResult.cfe_internal);
  window.Charts.renderCapexStack("chart-capex", currentResult.capex_breakdown);
  if (HOURLY_PROFILES) {
    window.Charts.renderCfHeatmap("chart-heatmap",
      HOURLY_PROFILES, dominantRenewable(currentResult.mix_pct));
  }
  window.Charts.renderIslandMatrix("chart-island");

  // Signature
  if (HOURLY_PROFILES) {
    window.Charts.renderDuck("chart-duck",
      currentResult.duck_curve, currentResult.mix_pct, HOURLY_PROFILES);
  }
  window.Charts.renderTornado("chart-tornado",
    currentResult.sensitivity, currentResult.blended_lcoe_per_mwh);
  window.Charts.renderIraDelta("chart-ira",
    currentResult.mix_pct,
    currentResult.blended_lcoe_per_mwh, currentResult.lcoe_post_ira);

  renderRecs(currentResult.recommendations);
});
