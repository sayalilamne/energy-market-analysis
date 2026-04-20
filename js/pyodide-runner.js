// Loads Pyodide, pulls our Python modules + data JSONs into its virtual FS,
// then exposes window.runAnalysis(inputs) for main.js to call.

const PYODIDE_VERSION = "0.26.4";
const PY_FILES = [
  "__init__.py",
  "capacity.py",
  "lcoe.py",
  "capex.py",
  "emissions.py",
  "rto_signals.py",
  "feasibility.py",
  "recommendations.py",
  "optimizer.py",
];
const DATA_FILES = [
  "nrel_atb_2024.json",
  "egrid_2022.json",
  "eia_capacity_factors.json",
  "rto_hourly_sample.json",
  "_meta.json",
];

let pyodide = null;

function setStatus(msg) {
  const el = document.getElementById("load-status");
  if (el) el.textContent = msg;
}

async function writeIntoFS(path, url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch failed: ${url}`);
  const text = await res.text();
  pyodide.FS.writeFile(path, text);
}

async function boot() {
  setStatus("Loading Pyodide runtime (~5 MB)…");
  // eslint-disable-next-line no-undef
  pyodide = await loadPyodide({
    indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
  });

  setStatus("Mounting Python modules…");
  pyodide.FS.mkdir("/energy");
  for (const name of PY_FILES) {
    await writeIntoFS(`/energy/${name}`, `energy/${name}`);
  }

  setStatus("Mounting datasets…");
  pyodide.FS.mkdir("/data");
  for (const name of DATA_FILES) {
    await writeIntoFS(`/data/${name}`, `data/${name}`);
  }

  // Make `py` importable as a top-level package.
  pyodide.runPython(`
import sys
if "/" not in sys.path:
    sys.path.insert(0, "/")
from energy.optimizer import run_analysis
  `);

  // Expose meta for UI badge.
  const meta = JSON.parse(pyodide.FS.readFile("/data/_meta.json", { encoding: "utf8" }));
  window.__DATASET_META__ = meta;

  setStatus("Ready.");
  document.getElementById("loading-overlay").classList.add("hidden");
  document.getElementById("generate-btn").disabled = false;
  if (window.__onPyodideReady) window.__onPyodideReady(meta);
}

window.runAnalysis = function (inputs) {
  if (!pyodide) throw new Error("Pyodide not ready yet.");
  const pyInputs = pyodide.toPy(inputs);
  const result = pyodide.runPython("run_analysis")(pyInputs);
  return result.toJs({ dict_converter: Object.fromEntries });
};

boot().catch((err) => {
  console.error(err);
  setStatus(`Load failed: ${err.message}`);
});
