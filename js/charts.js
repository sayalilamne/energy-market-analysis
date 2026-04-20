// Plotly.js renderers. Python returns pure data dicts; JS turns them into figures.

const TECH_COLOR = {
  solar:       "#f4b400",
  wind:        "#1a73e8",
  geothermal:  "#db4437",
  natural_gas: "#5f6368",
  coal:        "#202124",
  diesel:      "#9aa0a6",
  bess:        "#0f9d58",
};

const TECH_LABEL = {
  solar: "Solar", wind: "Wind", geothermal: "Geothermal",
  natural_gas: "Natural Gas", coal: "Coal", diesel: "Diesel", bess: "BESS",
};

const BASE_LAYOUT = {
  font: { family: "Roboto, system-ui, sans-serif", color: "#202124", size: 12 },
  margin: { l: 40, r: 20, t: 10, b: 40 },
  paper_bgcolor: "white",
  plot_bgcolor: "white",
};

const CONFIG = { displayModeBar: false, responsive: true };

// ── SANKEY: source → site ──
function renderSankey(containerId, mixPct, sizeMw) {
  const techs = Object.keys(mixPct);
  const labels = [...techs.map((t) => TECH_LABEL[t] || t), "Data Center"];
  const colors = [...techs.map((t) => TECH_COLOR[t] || "#999"), "#1a73e8"];
  const sinkIdx = labels.length - 1;

  const source = techs.map((_, i) => i);
  const target = techs.map(() => sinkIdx);
  const value  = techs.map((t) => +(mixPct[t] * sizeMw).toFixed(1));

  const fig = [{
    type: "sankey",
    arrangement: "snap",
    node: { label: labels, color: colors, pad: 14, thickness: 16,
            line: { color: "#e1e5ea", width: 1 } },
    link: { source, target, value,
            color: techs.map((t) => TECH_COLOR[t] + "88") },
  }];
  Plotly.newPlot(containerId, fig, { ...BASE_LAYOUT, margin: { l: 10, r: 10, t: 10, b: 10 } }, CONFIG);
}

// ── DONUT ──
function renderDonut(containerId, mixPct) {
  const techs = Object.keys(mixPct);
  const fig = [{
    type: "pie",
    labels: techs.map((t) => TECH_LABEL[t] || t),
    values: techs.map((t) => mixPct[t]),
    hole: 0.55,
    marker: { colors: techs.map((t) => TECH_COLOR[t] || "#999") },
    textinfo: "label+percent",
    textposition: "outside",
  }];
  Plotly.newPlot(containerId, fig, BASE_LAYOUT, CONFIG);
}

// ── CHOROPLETH: highlight user RTO ──
const RTO_STATES = {
  CAISO:  ["CA"],
  ERCOT:  ["TX"],
  SPP:    ["KS","OK","NE","ND","SD"],
  MISO:   ["IL","IN","MI","WI","MN","IA","MO","AR","LA"],
  PJM:    ["PA","NJ","DE","MD","VA","WV","OH","KY","DC"],
  NYISO:  ["NY"],
  "ISO-NE": ["ME","NH","VT","MA","RI","CT"],
};

function renderMap(containerId, rto) {
  const highlight = new Set(RTO_STATES[rto] || []);
  const allStates = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND",
    "OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"];
  const fig = [{
    type: "choropleth",
    locationmode: "USA-states",
    locations: allStates,
    z: allStates.map((s) => (highlight.has(s) ? 1 : 0)),
    colorscale: [[0, "#eef2f6"], [1, "#1a73e8"]],
    showscale: false,
    marker: { line: { color: "#fff", width: 0.5 } },
    hovertemplate: "%{location}<extra></extra>",
  }];
  const layout = {
    ...BASE_LAYOUT,
    geo: { scope: "usa", projection: { type: "albers usa" }, bgcolor: "white" },
    margin: { l: 0, r: 0, t: 0, b: 0 },
  };
  Plotly.newPlot(containerId, fig, layout, CONFIG);
}

// ── 10-YEAR PROJECTION: emissions + LCOE drift ──
function renderProjection(containerId, lcoe, marketTons) {
  const years = Array.from({ length: 10 }, (_, i) => 2026 + i);
  // Simple assumption: LCOE drifts +1%/yr, emissions -3%/yr via grid cleanup.
  const lcoeSeries = years.map((_, i) => +(lcoe * Math.pow(1.01, i)).toFixed(2));
  const emSeries   = years.map((_, i) => +(marketTons * Math.pow(0.97, i)).toFixed(0));

  const fig = [
    { x: years, y: lcoeSeries, name: "Blended LCOE ($/MWh)",
      type: "scatter", mode: "lines+markers",
      line: { color: "#1a73e8", width: 2 }, yaxis: "y1" },
    { x: years, y: emSeries, name: "Market Scope 2 (tCO₂e)",
      type: "scatter", mode: "lines+markers",
      line: { color: "#db4437", width: 2 }, yaxis: "y2" },
  ];
  const layout = {
    ...BASE_LAYOUT,
    margin: { l: 60, r: 60, t: 10, b: 40 },
    xaxis: { tickmode: "linear", dtick: 1 },
    yaxis:  { title: "$/MWh", side: "left",  rangemode: "tozero" },
    yaxis2: { title: "tCO₂e", side: "right", overlaying: "y", rangemode: "tozero" },
    legend: { orientation: "h", y: -0.2 },
  };
  Plotly.newPlot(containerId, fig, layout, CONFIG);
}

window.Charts = { renderSankey, renderDonut, renderMap, renderProjection };
