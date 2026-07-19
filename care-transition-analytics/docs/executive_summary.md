# Executive Summary

## Purpose

This project provides a professional analytics dashboard for evaluating how effectively children move through the UAC care pipeline: CBP custody, HHS care, and sponsor placement.

## What It Measures

- **Transfer Efficiency Ratio:** how quickly children move from CBP custody to HHS care.
- **Discharge Effectiveness Index:** how effectively HHS care results in sponsor placement.
- **Pipeline Throughput:** whether exits are keeping pace with entries.
- **Backlog Accumulation Rate:** where unresolved pressure is building.
- **Outcome Stability Score:** whether placement outcomes are consistent over time.

## Why It Matters

Aggregate custody counts show system size, but they do not show process health. A care system can appear stable while hidden delays accumulate between intake, transfer, case management, and discharge. This dashboard exposes those delays using daily flow metrics, rolling trends, and threshold-based alerts.

## Initial Findings From the Provided Dataset

- The cleaned dataset includes 720 usable reporting days from January 12, 2023 through December 21, 2025.
- CBP intake totals 67,337 children, transfers out of CBP total 92,641, and HHS discharges total 124,853.
- Average active HHS care load is 6,061 children, making small percentage changes in discharge effectiveness operationally meaningful.
- Positive system backlog appears on 128 reporting days, indicating periods when exits did not keep pace with intake.
- Discharge effectiveness is a key monitoring signal because slow placements can increase HHS care pressure even when CBP custody levels are controlled.

## Recommended Actions

1. Add transfer efficiency and discharge effectiveness to routine leadership reporting.
2. Investigate sustained periods where transfers into HHS exceed discharges from HHS.
3. Use threshold-based alerts to detect bottlenecks before they become prolonged backlogs.
4. Compare weekday and month-over-month patterns to find workflow delays.
5. Integrate case-level data in future work to measure actual time-to-transfer and time-to-reunification.

## Stakeholder Value

For policy leaders, the dashboard clarifies where process reform is needed. For operations teams, it identifies days and periods requiring follow-up. For humanitarian stakeholders, it keeps attention on timely, reliable reunification rather than only system capacity.

