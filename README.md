# Energy Market Analysis Tool

## Project Goal

Develop a visually sophisticated and interactive web dashboard for energy mix analysis of a customized BYOG (Bring Your Own Generation) data center project. The tool takes inputs from a decision matrix informed by credible public datasets and provides outputs as interactive, publication-quality graphs and maps (including bar charts, pie charts, Sankey diagrams, Choropleth maps, line charts, etc.).

---

## Dashboard Inputs: Decision Matrix Criteria

The interactive dashboard should be fully functional in the browser, showcasing the following 11 decision matrix criteria. After configuring all selections, click **"Generate Optimal Energy Mix"** to get instant results.

### 1. Primary Goal
- Cost
- Carbon
- Reliability
- Balanced

### 2. Energy Reliability
- Standard (99.9%)
- High (99.99%)
- Five Nines (99.999%)

### 3. Carbon / Sustainability Goals
- No mandate
- Annual Net-Zero
- 24/7 Carbon-free

### 4. Geography
*Shown as a map highlighting region selection for land availability for any renewable energy source.*
- Pacific Northwest
- Mid-Atlantic
- Sun-belt SW
- Texas Plains

### 5. Primary Workload
- AI Training
- AI Inference
- Mixed Cloud
- Financial / HFT

### 6. Speed to Power
- < 2 years
- 2–5 years
- 5+ years

### 7. Cost Priority
- Minimize Cost
- Balanced
- Performance First

### 8. Regional Transmission Organizations / Independent System Operators
*Shown as a map highlighting region selection.*
- CAISO
- ERCOT
- SPP
- MISO
- PJM
- NYISO
- ISO-NE

### 9. Data Center Size
*Shown as a slider.*
- Scale: 100 MW – 1,000 MW

### 10. Type of Data Center
- Enterprise
- Colocation
- Hyperscale

### 11. PPA Willingness
- Virtual
- Physical
- None

---

## Key Datasets

Mix logic weights vary by region, scale, land, storage, and procurement preferences.

| Dataset | Source | Purpose |
|---|---|---|
| NREL ATB 2024 | atb.nrel.gov | LCOE / cost baselines by technology |
| EIA Form 860/923 | eia.gov | Capacity factors by plant and region |
| EPA eGRID 2022 | epa.gov | Emissions intensity by RTO grid region |
| LBNL Queued Up | emp.lbl.gov | Interconnection queue data for feasibility |
| RTO Hourly Generation Files | CAISO OASIS, ERCOT Data Products, PJM Data Miner 2, etc. | 24/7 CFE matching |

---

## Dashboard Outputs

Visualizations draw inspiration from [Google Charts](https://developers.google.com/chart/interactive/docs/basic_customizing_chart) for look & feel. Output visuals include Sankey diagrams, pie charts, line charts, Choropleth maps, and tree maps as appropriate.

| Output | Format |
|---|---|
| Blended LCOE | Dollar value |
| Estimated CapEx | Dollar value |
| Carbon-free Score | Percentage / score |
| Feasibility Flag | Feasible / Not Feasible |
| Location & Market-based Scope 2 Carbon Emissions | Value with units |

### Visual Mix Breakdown
Includes: Solar, Wind, Geothermal, Nuclear, Natural Gas, Coal, Diesel Generator, BESS — represented as a Sankey diagram, tree map, disk, or pie chart.

### Strategic Recommendations
5 tailored recommendations specific to the selected configuration.

> **Hover tooltip:** Each output result displays a tooltip on hover summarizing how the result was calculated, which dataset was used, and the formula applied.

---

## Technologies

- Python 3
- Libraries: `gridstatus`, `PySAM`, `plotly.express`, `plotly.graph_objects`
- GitHub Pages

---

## UX Features

- Visualization style inspired by [Google Charts](https://developers.google.com/chart/interactive/docs/basic_customizing_chart)
- Single-page layout: inputs and outputs on the same page with dynamic interactivity
- Fully responsive — sidebar hides on mobile
