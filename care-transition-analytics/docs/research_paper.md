# Care Transition Efficiency & Placement Outcome Analytics

## Abstract

The Unaccompanied Alien Children (UAC) Program functions as a multi-stage care and reunification pipeline: CBP custody, transfer to HHS care, sheltering and case management, and discharge to a vetted sponsor. This project evaluates that pipeline using process-efficiency metrics rather than only aggregate custody counts. The analysis converts daily public reporting data into transition, discharge, throughput, backlog, and stability indicators designed to surface operational bottlenecks and support faster reunification decisions.

## Background

Traditional capacity monitoring answers how many children are in custody or care on a given date. It does not fully answer whether children are moving efficiently through the system. For a humanitarian care pipeline, speed, continuity, and reliability are critical because delays can compound across stages. A process lens helps distinguish between high volume, slow transfer, delayed discharge, and unstable sponsor placement performance.

## Dataset

The dataset contains daily reporting fields for:

- Reporting date
- Children apprehended and placed in CBP custody
- Children in CBP custody
- Children transferred out of CBP custody
- Children in HHS care
- Children discharged from HHS care

After dropping blank rows, the working dataset contains 720 usable reporting records from January 12, 2023 through December 21, 2025.

## Methodology

The care system is modeled as a flow pipeline:

1. Children apprehended and placed in CBP custody
2. Children transferred out of CBP custody into the HHS care system
3. Children discharged from HHS care to sponsor placement

The analysis computes five primary KPIs:

| KPI | Formula | Purpose |
| --- | --- | --- |
| Transfer Efficiency Ratio | Transfers / CBP custody | Measures CBP-to-HHS transition speed |
| Discharge Effectiveness Index | Discharges / HHS care | Measures sponsor placement effectiveness |
| Pipeline Throughput | Discharges / CBP intake | Measures whether exits are keeping pace with entries |
| Backlog Accumulation Rate | Transfers - discharges | Identifies HHS care-load pressure |
| Outcome Stability Score | 1 - rolling coefficient of variation in discharge effectiveness | Measures consistency of placement outcomes |

Rolling averages are used to reduce day-to-day volatility. Threshold-based alerts flag low transfer efficiency, low discharge effectiveness, positive backlog pressure, and volatile placement outcomes.

## Exploratory Data Analysis

Across the full cleaned dataset, reported CBP intake totals 67,337 children, transfers out of CBP total 92,641, and discharges from HHS care total 124,853. Average active CBP custody is 171.5 children per reporting day, while average active HHS care load is 6,061.3 children.

The mean daily Transfer Efficiency Ratio is 69.1%, with a median of 70.4%. The mean Discharge Effectiveness Index is 2.37%, with a median of 2.63%. Pipeline Throughput averages 250.3% because discharges in a given period may include children who entered care before that same selected period.

Backlog pressure is not uniform across the series. A simple intake-minus-discharge comparison shows positive system backlog on 128 of 720 reporting days. Monthly HHS net flow, calculated as transfers minus discharges, helps isolate periods when HHS care pressure increases even if CBP intake is low.

Weekday analysis indicates operational variation. In the profiled dataset, Thursday and Sunday show higher average discharge volumes than Monday through Wednesday, while Tuesday shows weaker average discharge effectiveness. This pattern should be interpreted cautiously because the dataset is an aggregate reporting series and does not contain case-level scheduling context.

## Key Insights

1. Capacity and process performance are different management questions. HHS care load can remain high even when CBP custody is low if discharges lag transfers.

2. Discharge effectiveness is the most sensitive bottleneck indicator. Small percentage changes matter because the denominator is the total active HHS care population.

3. Throughput above 100% is not automatically a data issue. It can occur when children discharged during the period entered HHS care before the selected window.

4. Sustained positive HHS net flow is an early warning signal. When transfers into HHS exceed discharges for multiple reporting days, care-load pressure can accumulate even if daily intake appears manageable.

5. Outcome stability adds a reliability lens. A high-discharge day followed by prolonged stagnation may be less operationally healthy than consistent placement throughput.

## Recommendations

- Track transfer and discharge metrics alongside custody counts in routine operating reports.
- Use rolling threshold alerts for transfer efficiency and discharge effectiveness rather than relying on single-day values.
- Review sustained positive HHS net-flow periods to identify staffing, sponsor verification, transportation, case management, or shelter-capacity constraints.
- Monitor weekday effects to determine whether weekend or off-cycle processes create avoidable delays.
- Pair aggregate dashboards with case-level data where available to measure actual length of stay and sponsor vetting timelines.

## Limitations

This dataset is aggregate and does not identify individual children, case complexity, sponsor type, shelter location, medical needs, legal constraints, or actual elapsed time between stages. The analysis therefore evaluates system-level flow and pressure, not individual-level outcomes. Metrics should be treated as operational signals requiring follow-up, not definitive causal evidence.

## Conclusion

The UAC care pipeline should be monitored as an end-to-end transition system. By measuring transfer efficiency, discharge effectiveness, throughput, backlog accumulation, and outcome stability, this project surfaces bottlenecks that are hidden by aggregate custody counts alone. The resulting dashboard supports faster reunification, improved case management workflows, and policy-level process reform.

