# Care Transition Efficiency & Placement Outcome Analytics

Professional Streamlit analytics project for evaluating the UAC care pipeline from CBP intake through HHS care and sponsor placement.

## Project Purpose

This project reframes the HHS UAC dataset from simple capacity monitoring into process-efficiency and placement-outcome analytics. It helps answer:

- How efficiently are children transferred from CBP to HHS?
- Are discharges keeping pace with inflows?
- When do care backlogs accumulate?
- Are placement outcomes stable or deteriorating over time?

## Project Structure

```text
care-transition-analytics/
  app.py
  requirements.txt
  README.md
  data/
    raw/
      HHS_Unaccompanied_Alien_Children_Program.csv
  docs/
    research_paper.md
    executive_summary.md
  src/
    data_processing.py
  .streamlit/
    config.toml
```

## Run Locally

```powershell
cd care-transition-analytics
python -m pip install -r requirements.txt
streamlit run app.py
```

In this Codex environment, the bundled Python runtime can run the app directly:

```powershell
 -m streamlit run app.py
```

## Dashboard Modules

- **Care Pipeline Flow Visualization:** Sankey flow and active load trends.
- **Transfer & Discharge Efficiency Panels:** Rolling ratios and threshold comparisons.
- **Bottleneck Detection Charts:** Net-flow pressure, alert cards, and sustained bottleneck table.
- **Outcome Trend Analysis:** Monthly placement performance, backlog accumulation, stability, and weekday effects.
- **Data & Method:** Metric definitions, caveats, and cleaned dataset preview.

## Core KPIs

| KPI | Definition | Interpretation |
| --- | --- | --- |
| Transfer Efficiency Ratio | Transfers out of CBP custody / children in CBP custody | Measures CBP-to-HHS transition speed |
| Discharge Effectiveness Index | Discharges from HHS care / children in HHS care | Measures sponsor placement effectiveness |
| Pipeline Throughput | Discharges / CBP intake | Measures whether exits are keeping pace with entries |
| Backlog Accumulation Rate | Transfers into HHS - discharges from HHS | Positive values suggest HHS care-load pressure |
| Outcome Stability Score | 1 - rolling coefficient of variation in discharge effectiveness | Higher score means placement outcomes are more consistent |

## Data Handling

The app removes blank rows, parses the reporting date, converts comma-formatted counts to numeric values, and computes all metrics from the cleaned dataset. Users can either use the included CSV in `data/raw/` or upload an updated CSV from the sidebar.

## Deliverables

- Streamlit dashboard for live analytics.
- Research paper with EDA, insights, limitations, and recommendations.
- Executive summary for government stakeholders.

