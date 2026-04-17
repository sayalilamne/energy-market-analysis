# Energy Market Analysis Tool

## Project Goal

Develop a web tool for energy mix analysis. 

Given a specific decision matrix criteria, the tool should be able to generate the following:
- scope 2 carbon emissions
- energy mix breakdown represented as a bar chart 

The tool must be interactive and able to update the calculations on-the-fly as decision criteria changes.

### Decision Matrix Criteria

1. **Energy Reliability**
    - Standard (99.9%)
    - High (99.99%)
    - Five Nines (99.999%)

2. **Carbon/Sustainability Goals**
    - No mandate
    - Annual Net-Zero
    - 24/7 Carbon-free

3. **Geography**
    - Pacific North-West
    - Mid-Atlantic
    - Sun-belt-SW
    - Texas-Plains

4. **Primary Workload**
    - AI-Training
    - AI-Inference
    - Mixed-Cloud
    - Financial/HFT

5. **Speed to Power**
    - <2 years
    - 2-5 years
    - 5+ years

6. **Cost Priority**
    - Minimize Cost
    - Balanced
    - Performance First

7. **Regional Transmission Organizations/Independent System Operators**
    - CAISO
    - ERCOT
    - SPP
    - MISO
    - PJM
    - NYISO
    - ISO-NE

8. **Data Center Size**
    - Scale: 100 MW to 1000 MW

### Dashboard Requirements

Create a dashboard with visuals showcasing RTO/ISO regions on a USA map and the overall energy mix with symbols. Connect all necessary data sources for updates.

### Analysis Scope

Include a Scope 2 emissions analysis for the data center under market-based vs. location-based accounting using real EIA and CAISO OASIS data (both free and public).

## Technologies Used
    - Python3
    - GitHub Pages