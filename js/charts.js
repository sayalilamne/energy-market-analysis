// Plotly.js renderers — 12 charts grouped Essentials / Advanced / Signature.
// Python returns numbers; JS turns them into Plotly figure JSON.

const TECH_COLOR = {
  solar:       "#f4b400",
  wind:        "#1a73e8",
  geothermal:  "#db4437",
  nuclear:     "#7c4dff",
  hydro:       "#00acc1",
  natural_gas: "#5f6368",
  coal:        "#202124",
  diesel:      "#9aa0a6",
  bess:        "#0f9d58",
};

const TECH_LABEL = {
  solar: "Solar", wind: "Wind", geothermal: "Geothermal", nuclear: "Nuclear",
  hydro: "Hydro", natural_gas: "Natural Gas", coal: "Coal", diesel: "Diesel", bess: "BESS",
};

const FIRM_TECHS     = new Set(["nuclear", "natural_gas", "coal", "diesel", "geothermal", "hydro", "bess"]);
const CARBON_FREE    = new Set(["solar", "wind", "geothermal", "hydro", "nuclear", "bess"]);

const BASE_LAYOUT = {
  font: { family: "Roboto, system-ui, sans-serif", color: "#202124", size: 12 },
  margin: { l: 50, r: 20, t: 10, b: 40 },
  paper_bgcolor: "white",
  plot_bgcolor: "white",
};

const CONFIG = { displayModeBar: false, responsive: true };

const RTO_STATES = {
  CAISO:  ["CA"],
  ERCOT:  ["TX"],
  SPP:    ["KS","OK","NE","ND","SD"],
  MISO:   ["IL","IN","MI","WI","MN","IA","MO","AR","LA"],
  PJM:    ["PA","NJ","DE","MD","VA","WV","OH","KY","DC"],
  NYISO:  ["NY"],
  "ISO-NE": ["ME","NH","VT","MA","RI","CT"],
};
const ALL_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
  "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND",
  "OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"];

// ────────────────────── ESSENTIALS ──────────────────────

function renderMap(id, rto) {
  const highlight = new Set(RTO_STATES[rto] || []);
  const fig = [{
    type: "choropleth",
    locationmode: "USA-states",
    locations: ALL_STATES,
    z: ALL_STATES.map((s) => (highlight.has(s) ? 1 : 0)),
    colorscale: [[0, "#eef2f6"], [1, "#1a73e8"]],
    showscale: false,
    marker: { line: { color: "#fff", width: 0.5 } },
    hovertemplate: "%{location}<extra></extra>",
  }];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    geo: { scope: "usa", projection: { type: "albers usa" }, bgcolor: "white" },
    margin: { l: 0, r: 0, t: 0, b: 0 },
  }, CONFIG);
}

function renderDonut(id, mixPct) {
  // Outer ring: by tech. Inner ring: carbon-free vs fossil grouping.
  const techs = Object.keys(mixPct);
  const outerLabels = techs.map((t) => TECH_LABEL[t] || t);
  const outerColors = techs.map((t) => TECH_COLOR[t] || "#999");
  const outerVals   = techs.map((t) => mixPct[t]);

  const cfShare = techs.filter((t) => CARBON_FREE.has(t)).reduce((s, t) => s + mixPct[t], 0);
  const fossilShare = 1 - cfShare;

  const fig = [
    {
      type: "pie", hole: 0.45,
      labels: outerLabels, values: outerVals,
      marker: { colors: outerColors, line: { color: "#fff", width: 1 } },
      textinfo: "label+percent", textposition: "outside",
      domain: { x: [0, 1], y: [0, 1] },
      sort: false,
    },
    {
      type: "pie", hole: 0.75,
      labels: ["Carbon-free", "Fossil"],
      values: [cfShare, fossilShare],
      marker: { colors: ["#0f9d58", "#5f6368"], line: { color: "#fff", width: 1 } },
      textinfo: "none",
      domain: { x: [0.18, 0.82], y: [0.18, 0.82] },
      hovertemplate: "%{label}: %{percent}<extra></extra>",
      sort: false,
    },
  ];
  Plotly.newPlot(id, fig, { ...BASE_LAYOUT, showlegend: false }, CONFIG);
}

function renderSankey(id, mixPct, sizeMw, pue) {
  const techs = Object.keys(mixPct);
  const itLoad = sizeMw;
  const totalLoad = sizeMw * pue;
  const overhead = totalLoad - itLoad;

  const labels  = [...techs.map((t) => TECH_LABEL[t] || t), "Total Site Load", "IT Load", "Cooling + Overhead"];
  const colors  = [...techs.map((t) => TECH_COLOR[t] || "#999"), "#1a73e8", "#0f9d58", "#9aa0a6"];

  const siteIdx     = techs.length;
  const itIdx       = techs.length + 1;
  const overheadIdx = techs.length + 2;

  const source = [];
  const target = [];
  const value  = [];
  techs.forEach((t, i) => {
    source.push(i); target.push(siteIdx);
    value.push(+(mixPct[t] * totalLoad).toFixed(1));
  });
  source.push(siteIdx); target.push(itIdx);       value.push(+itLoad.toFixed(1));
  source.push(siteIdx); target.push(overheadIdx); value.push(+overhead.toFixed(1));

  const fig = [{
    type: "sankey",
    arrangement: "snap",
    node: { label: labels, color: colors, pad: 14, thickness: 16,
            line: { color: "#e1e5ea", width: 1 } },
    link: { source, target, value,
            color: [...techs.map((t) => (TECH_COLOR[t] || "#999") + "88"), "#0f9d5888", "#9aa0a688"] },
  }];
  Plotly.newPlot(id, fig, { ...BASE_LAYOUT, margin: { l: 10, r: 10, t: 10, b: 10 } }, CONFIG);
}

function renderTrajectory(id, marketTons, ieaCurve, sizeMw, pue) {
  const years = Array.from({ length: 25 }, (_, i) => 2026 + i);
  // Project market emissions improving 3%/yr from grid decarbonization.
  const proj = years.map((_, i) => +(marketTons * Math.pow(0.97, i)).toFixed(0));

  // IEA NZE intensity (lb/MWh) → tons/yr at this site.
  const annualMwh = sizeMw * pue * 8760;
  const iea = years.map((y) => {
    const lb = ieaCurve[String(y)];
    if (lb === undefined) return null;
    return +(lb * annualMwh / 2204.62).toFixed(0);
  });

  const fig = [
    { x: years, y: proj, name: "Projected Scope 2 (market)",
      type: "scatter", mode: "lines+markers",
      line: { color: "#db4437", width: 2.5 } },
    { x: years, y: iea, name: "IEA NZE benchmark",
      type: "scatter", mode: "lines",
      line: { color: "#0f9d58", width: 2, dash: "dash" },
      connectgaps: true },
  ];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    margin: { l: 60, r: 20, t: 10, b: 50 },
    yaxis:  { title: "tCO₂e / yr", rangemode: "tozero" },
    xaxis:  { dtick: 2 },
    legend: { orientation: "h", y: -0.2 },
  }, CONFIG);
}

// ────────────────────── ADVANCED ──────────────────────

function renderWaterfall(id, components, postIra, mode) {
  // components: {capex_amort, fixed_om, variable_om, fuel}
  const labels = ["CapEx amort.", "Fixed O&M", "Variable O&M", "Fuel", "Blended"];
  const measure = ["relative","relative","relative","relative","total"];
  const vals = [components.capex_amort, components.fixed_om,
                components.variable_om, components.fuel, 0];
  const total = components.capex_amort + components.fixed_om + components.variable_om + components.fuel;
  const ira = mode === "post" ? +(postIra - total).toFixed(2) : 0;
  const lbl2 = mode === "post" ? [...labels.slice(0,4), "IRA credit", "Post-IRA"] : labels;
  const m2   = mode === "post" ? [...measure.slice(0,4), "relative", "total"] : measure;
  const v2   = mode === "post" ? [...vals.slice(0,4), ira, 0] : vals;

  const fig = [{
    type: "waterfall",
    x: lbl2,
    measure: m2,
    y: v2,
    text: v2.map((v) => v ? `$${v.toFixed(1)}` : ""),
    textposition: "outside",
    increasing: { marker: { color: "#1a73e8" } },
    decreasing: { marker: { color: "#0f9d58" } },
    totals:     { marker: { color: "#202124" } },
    connector:  { line: { color: "#cbd2d9" } },
  }];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    yaxis: { title: "$/MWh" },
    margin: { l: 60, r: 20, t: 10, b: 60 },
  }, CONFIG);
}

function renderPareto(id, lcoe, cfeScore) {
  // Plot known archetype mixes vs the user's chosen point.
  const archetypes = [
    { name: "All-gas",            lcoe: 60,  reliability: 95 },
    { name: "Gas + BESS",         lcoe: 75,  reliability: 92 },
    { name: "Solar + BESS",       lcoe: 95,  reliability: 70 },
    { name: "Wind + Solar + BESS",lcoe: 90,  reliability: 65 },
    { name: "Nuclear-anchored",   lcoe: 100, reliability: 99 },
    { name: "Geothermal + Solar", lcoe: 110, reliability: 88 },
    { name: "Hydro-rich",         lcoe: 85,  reliability: 90 },
  ];
  // Simple Pareto frontier — points where no other has lower LCOE & higher reliability.
  const frontier = archetypes.filter((p) => !archetypes.some((q) =>
    q !== p && q.lcoe <= p.lcoe && q.reliability >= p.reliability &&
    (q.lcoe < p.lcoe || q.reliability > p.reliability)
  )).sort((a, b) => a.lcoe - b.lcoe);

  const userReliability = Math.min(99, 60 + cfeScore * 0.4);
  const fig = [
    { x: archetypes.map((p) => p.lcoe), y: archetypes.map((p) => p.reliability),
      mode: "markers+text", type: "scatter",
      text: archetypes.map((p) => p.name), textposition: "top center",
      marker: { size: 10, color: "#5f6368" }, name: "Archetypes" },
    { x: frontier.map((p) => p.lcoe), y: frontier.map((p) => p.reliability),
      mode: "lines", type: "scatter",
      line: { color: "#1a73e8", width: 2, dash: "dot" },
      name: "Pareto frontier" },
    { x: [lcoe], y: [userReliability],
      mode: "markers", type: "scatter",
      marker: { size: 16, color: "#db4437", symbol: "star",
                line: { color: "#fff", width: 2 } },
      name: "Your mix" },
  ];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    xaxis: { title: "Blended LCOE ($/MWh)" },
    yaxis: { title: "Reliability score" },
    legend: { orientation: "h", y: -0.2 },
    margin: { l: 60, r: 20, t: 30, b: 60 },
  }, CONFIG);
}

function renderCapexStack(id, breakdown) {
  const buckets = ["land", "equipment", "epc", "interconnection", "financing"];
  const colors  = { land: "#9aa0a6", equipment: "#1a73e8", epc: "#0f9d58",
                    interconnection: "#f4b400", financing: "#7c4dff" };
  const techs = breakdown.map((r) => TECH_LABEL[r.tech] || r.tech);

  const traces = buckets.map((b) => ({
    type: "bar",
    name: b.charAt(0).toUpperCase() + b.slice(1),
    x: techs,
    y: breakdown.map((r) => r[b] / 1e6),
    marker: { color: colors[b] },
    hovertemplate: "%{x}<br>" + b + ": $%{y:.1f}M<extra></extra>",
  }));

  Plotly.newPlot(id, traces, {
    ...BASE_LAYOUT,
    barmode: "stack",
    yaxis: { title: "$M" },
    legend: { orientation: "h", y: -0.25 },
    margin: { l: 60, r: 20, t: 10, b: 70 },
  }, CONFIG);
}

function renderCfHeatmap(id, hourlyProfiles, dominantRenewable) {
  // dominantRenewable = "solar" | "wind" — pick whichever has higher share in mix.
  const matrix = hourlyProfiles[dominantRenewable] || hourlyProfiles.solar;
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const hours  = Array.from({ length: 24 }, (_, i) => i);

  const fig = [{
    type: "heatmap",
    z: matrix,
    x: hours,
    y: months,
    colorscale: [
      [0,    "#0b3d91"], [0.25, "#1a73e8"],
      [0.5,  "#7cb342"], [0.75, "#fbbc04"], [1, "#db4437"],
    ],
    colorbar: { title: "CF", thickness: 12 },
    hovertemplate: "%{y} h%{x}: CF %{z:.2f}<extra></extra>",
  }];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    xaxis: { title: "Hour", dtick: 3 },
    yaxis: { title: "Month", autorange: "reversed" },
    margin: { l: 50, r: 60, t: 10, b: 40 },
  }, CONFIG);
}

function renderIslandMatrix(id) {
  const modes     = ["Non-island", "Partial island", "Partial island", "Partial island"];
  const durations = ["n/a",        "4 hr",            "24 hr",          "72 hr+"];
  const premium   = [0,            10,                22,               40];
  const storage   = [0.05,         0.20,              0.40,             0.65];

  const fig = [
    { type: "bar", x: durations, y: premium, name: "CapEx premium (%)",
      marker: { color: "#db4437" }, yaxis: "y1" },
    { type: "scatter", x: durations, y: storage.map((s) => s * 100),
      mode: "lines+markers", name: "BESS as % of site MW",
      line: { color: "#1a73e8", width: 2 }, yaxis: "y2" },
  ];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    xaxis: { title: "Backup duration" },
    yaxis:  { title: "CapEx premium (%)", side: "left", rangemode: "tozero" },
    yaxis2: { title: "BESS share (%)",    side: "right", overlaying: "y", rangemode: "tozero" },
    legend: { orientation: "h", y: -0.2 },
    margin: { l: 60, r: 60, t: 10, b: 50 },
  }, CONFIG);
}

// ────────────────────── SIGNATURE ──────────────────────

function renderDuck(id, duckCurve, mixPct, hourlyProfiles) {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const solarShare = mixPct.solar || 0;
  const windShare  = mixPct.wind  || 0;
  // Use July profiles as representative day.
  const solar = (hourlyProfiles.solar || hourlyProfiles.solar)[6];
  const wind  = (hourlyProfiles.wind  || hourlyProfiles.wind)[6];

  const onSite = hours.map((h) => solarShare * solar[h] + windShare * wind[h]);
  const net    = duckCurve.map((d, h) => +(d - onSite[h]).toFixed(3));

  const fig = [
    { x: hours, y: duckCurve, name: "Grid demand (RTO)",
      type: "scatter", mode: "lines",
      line: { color: "#5f6368", width: 2 }, fill: "tozeroy",
      fillcolor: "rgba(95,99,104,0.15)" },
    { x: hours, y: onSite, name: "On-site renewables",
      type: "scatter", mode: "lines",
      line: { color: "#f4b400", width: 2 }, fill: "tozeroy",
      fillcolor: "rgba(244,180,0,0.20)" },
    { x: hours, y: net, name: "Net residual",
      type: "scatter", mode: "lines",
      line: { color: "#db4437", width: 2.5, dash: "dot" } },
  ];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    xaxis: { title: "Hour of day", dtick: 2 },
    yaxis: { title: "Load (norm.)", rangemode: "tozero" },
    legend: { orientation: "h", y: -0.2 },
    margin: { l: 60, r: 20, t: 10, b: 50 },
  }, CONFIG);
}

function renderTornado(id, rows, baseLcoe) {
  const sorted = rows.slice().sort((a, b) => a.swing - b.swing);
  const labels = sorted.map((r) => r.variable);
  const lows  = sorted.map((r) => r.low_lcoe  - baseLcoe);
  const highs = sorted.map((r) => r.high_lcoe - baseLcoe);

  const fig = [
    { type: "bar", orientation: "h", y: labels, x: lows,
      name: "−1σ", marker: { color: "#0f9d58" },
      hovertemplate: "%{y}<br>%{x:+.1f} $/MWh<extra></extra>" },
    { type: "bar", orientation: "h", y: labels, x: highs,
      name: "+1σ", marker: { color: "#db4437" },
      hovertemplate: "%{y}<br>%{x:+.1f} $/MWh<extra></extra>" },
  ];
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    barmode: "overlay",
    xaxis: { title: `Δ from baseline ($${baseLcoe}/MWh)`, zeroline: true,
             zerolinecolor: "#202124", zerolinewidth: 1 },
    legend: { orientation: "h", y: -0.2 },
    margin: { l: 110, r: 20, t: 10, b: 60 },
  }, CONFIG);
}

function renderIraDelta(id, mixPct, lcoePre, lcoePost) {
  // Bar chart of pre vs post LCOE plus delta.
  const fig = [
    { type: "bar", x: ["Pre-IRA", "Post-IRA"], y: [lcoePre, lcoePost],
      marker: { color: ["#5f6368", "#0f9d58"] },
      text: [`$${lcoePre.toFixed(1)}`, `$${lcoePost.toFixed(1)}`],
      textposition: "outside",
      hovertemplate: "%{x}: $%{y:.2f}/MWh<extra></extra>" },
  ];
  const delta = (lcoePre - lcoePost).toFixed(2);
  Plotly.newPlot(id, fig, {
    ...BASE_LAYOUT,
    yaxis: { title: "$/MWh", rangemode: "tozero" },
    annotations: [{
      x: 0.5, y: Math.max(lcoePre, lcoePost) * 1.05, xref: "x", yref: "y",
      text: `IRA savings: $${delta}/MWh`, showarrow: false,
      font: { size: 13, color: "#0f9d58", family: "Roboto" },
    }],
    margin: { l: 60, r: 20, t: 30, b: 50 },
  }, CONFIG);
}

window.Charts = {
  renderMap, renderDonut, renderSankey, renderTrajectory,
  renderWaterfall, renderPareto, renderCapexStack, renderCfHeatmap, renderIslandMatrix,
  renderDuck, renderTornado, renderIraDelta,
};
