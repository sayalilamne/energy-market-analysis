// Form handling: collect inputs, call Python, render summary cards + charts.

const form = document.getElementById("decision-form");
const emptyState = document.getElementById("empty-state");
const resultsPane = document.getElementById("results-pane");
const sizeSlider = document.getElementById("size-slider");
const sizeReadout = document.getElementById("size-readout");
const metaBadge = document.getElementById("meta-badge");

sizeSlider.addEventListener("input", () => {
  sizeReadout.textContent = sizeSlider.value;
});

window.__onPyodideReady = (meta) => {
  const dates = Object.values(meta).map((m) => m.refreshed).sort();
  metaBadge.textContent = `Data as of ${dates[dates.length - 1]}`;
};

function gatherInputs() {
  const fd = new FormData(form);
  return {
    primary_goal:     fd.get("primary_goal"),
    reliability:      fd.get("reliability"),
    carbon_goal:      fd.get("carbon_goal"),
    geography:        fd.get("geography"),
    primary_workload: fd.get("primary_workload"),
    speed_to_power:   fd.get("speed_to_power"),
    cost_priority:    fd.get("cost_priority"),
    rto:              fd.get("rto"),
    size_mw:          Number(fd.get("size_mw")),
    type:             fd.get("type"),
    ppa:              fd.get("ppa"),
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

function renderSummaryCards(res) {
  const feasClass = res.feasibility.flag === "Feasible" ? "green" : "red";
  const cfeClass = res.carbon_free_score >= 70 ? "green" : res.carbon_free_score >= 40 ? "yellow" : "red";

  const cards = [
    { label: "Blended LCOE",      value: `$${res.blended_lcoe_per_mwh}/MWh`,
      tip: res.tooltips.lcoe },
    { label: "Estimated CapEx",   value: fmtMoney(res.total_capex_usd),
      tip: res.tooltips.capex },
    { label: "Carbon-free Score", value: `${res.carbon_free_score}/100`, cls: cfeClass,
      tip: res.tooltips.cfe },
    { label: "Feasibility",       value: res.feasibility.flag, cls: feasClass,
      tip: `${res.tooltips.feasibility}\n\n${res.feasibility.reason}` },
    { label: "Scope 2 (location)", value: fmtTons(res.emissions.location_tons),
      tip: res.tooltips.emissions, sub: "tCO₂e / year" },
    { label: "Scope 2 (market)",   value: fmtTons(res.emissions.market_tons),
      tip: res.tooltips.emissions, sub: "tCO₂e / year" },
  ];

  const host = document.getElementById("summary-cards");
  host.innerHTML = cards.map((c) => `
    <div class="summary-card">
      <div class="tip" title="${c.tip.replace(/"/g, "&quot;")}">i</div>
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
let mixMode = "sankey";

function renderMixChart() {
  if (!currentResult) return;
  const { mix_pct } = currentResult;
  const size = Number(gatherInputs().size_mw);
  if (mixMode === "sankey") window.Charts.renderSankey("mix-chart", mix_pct, size);
  else window.Charts.renderDonut("mix-chart", mix_pct);
}

document.getElementById("mix-toggle").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  document.querySelectorAll("#mix-toggle button").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  mixMode = btn.dataset.mode;
  renderMixChart();
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const inputs = gatherInputs();
  const res = window.runAnalysis(inputs);
  currentResult = res;

  emptyState.classList.add("hidden");
  resultsPane.classList.remove("hidden");

  renderSummaryCards(res);
  renderMixChart();
  window.Charts.renderMap("map-chart", inputs.rto);
  window.Charts.renderProjection("projection-chart",
    res.blended_lcoe_per_mwh, res.emissions.market_tons);
  renderRecs(res.recommendations);
});
