from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_processing import (
    DashboardThresholds,
    DEFAULT_DATA_PATH,
    DISPLAY_NAMES,
    build_alerts,
    compare_to_previous_period,
    detect_bottlenecks,
    filter_by_date,
    format_number,
    format_percent,
    monthly_summary,
    period_summary,
    prepare_data,
    weekday_summary,
)


st.set_page_config(
    page_title="Care Transition Analytics",
    page_icon="HHS",
    layout="wide",
    initial_sidebar_state="expanded",
)


COLORWAY = ["#0F766E", "#2563EB", "#D97706", "#7C3AED", "#DC2626", "#334155"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = COLORWAY


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #111827;
            --muted: #5B6472;
            --line: #D9E2EC;
            --panel: #FFFFFF;
            --soft: #F7F9FC;
            --teal: #0F766E;
            --blue: #2563EB;
            --amber: #D97706;
            --red: #DC2626;
        }
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        [data-testid="stSidebar"] {
            background: #F7F9FC;
            border-right: 1px solid var(--line);
        }
        .app-header {
            border-bottom: 1px solid var(--line);
            padding-bottom: 1rem;
            margin-bottom: 1rem;
        }
        .app-kicker {
            color: var(--teal);
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }
        .app-title {
            color: var(--ink);
            font-size: clamp(1.85rem, 3vw, 3rem);
            line-height: 1.05;
            font-weight: 850;
            margin: 0;
        }
        .app-subtitle {
            color: var(--muted);
            max-width: 980px;
            font-size: 1rem;
            margin-top: .65rem;
        }
        .metric-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1rem .85rem;
            min-height: 132px;
            box-shadow: 0 1px 2px rgba(17, 24, 39, .04);
        }
        .metric-label {
            color: var(--muted);
            font-size: .78rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: .04em;
            min-height: 2.1rem;
        }
        .metric-value {
            color: var(--ink);
            font-size: clamp(1.35rem, 2.3vw, 2.1rem);
            line-height: 1.1;
            font-weight: 850;
            margin-top: .35rem;
            overflow-wrap: anywhere;
        }
        .metric-note {
            color: var(--muted);
            font-size: .82rem;
            margin-top: .45rem;
        }
        .delta-good { color: var(--teal); font-weight: 800; }
        .delta-warn { color: var(--amber); font-weight: 800; }
        .delta-bad { color: var(--red); font-weight: 800; }
        .section-title {
            color: var(--ink);
            font-size: 1.25rem;
            line-height: 1.2;
            font-weight: 850;
            margin: .4rem 0 .15rem;
        }
        .section-copy {
            color: var(--muted);
            margin: 0 0 .75rem;
            font-size: .94rem;
        }
        .alert {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--panel);
            padding: .95rem 1rem;
            margin-bottom: .65rem;
        }
        .alert-high { border-left: 5px solid var(--red); }
        .alert-medium { border-left: 5px solid var(--amber); }
        .alert-normal { border-left: 5px solid var(--teal); }
        .alert-level {
            color: var(--muted);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .alert-title {
            color: var(--ink);
            font-weight: 850;
            margin-top: .1rem;
        }
        .alert-detail {
            color: var(--muted);
            font-size: .9rem;
            margin-top: .2rem;
        }
        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .8rem .9rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: .25rem;
            border-bottom: 1px solid var(--line);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: .8rem .9rem;
            font-weight: 700;
        }
        .dataframe {
            font-size: .88rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_prepare_data(source_bytes: bytes | None, source_name: str | None, smoothing_window: int) -> pd.DataFrame:
    if source_bytes is not None:
        from io import BytesIO

        return prepare_data(BytesIO(source_bytes), smoothing_window=smoothing_window)
    return prepare_data(DEFAULT_DATA_PATH, smoothing_window=smoothing_window)


def metric_card(label: str, value: str, note: str, delta: float | None = None, inverse: bool = False) -> None:
    delta_html = ""
    if delta is not None and pd.notna(delta):
        good = delta < 0 if inverse else delta >= 0
        klass = "delta-good" if good else "delta-bad"
        sign = "+" if delta > 0 else ""
        delta_html = f'<span class="{klass}">{sign}{delta:.1%}</span> vs prior period'
    elif note:
        delta_html = note

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{delta_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <p class="section-copy">{copy}</p>
        """,
        unsafe_allow_html=True,
    )


def alert_card(alert: dict[str, str]) -> None:
    level = alert["level"].lower()
    st.markdown(
        f"""
        <div class="alert alert-{level}">
            <div class="alert-level">{alert['level']} signal</div>
            <div class="alert-title">{alert['title']}</div>
            <div class="alert-detail">{alert['detail']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def flow_sankey(summary: dict[str, float]) -> go.Figure:
    apprehended = max(summary.get("apprehended", 0), 0)
    transferred = max(summary.get("transferred", 0), 0)
    discharged = max(summary.get("discharged", 0), 0)
    cbp_gap = max(apprehended - transferred, 0)
    hhs_gap = max(transferred - discharged, 0)

    labels = [
        "CBP intake",
        "CBP custody",
        "HHS care",
        "Sponsor placement",
        "CBP unresolved pressure",
        "HHS unresolved pressure",
    ]
    source = [0, 1, 1, 2, 2]
    target = [1, 2, 4, 3, 5]
    value = [apprehended, transferred, cbp_gap, discharged, hhs_gap]
    colors = ["#0F766E", "#2563EB", "#D97706", "#7C3AED", "#DC2626"]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node={
                    "pad": 20,
                    "thickness": 18,
                    "line": {"color": "#CBD5E1", "width": 1},
                    "label": labels,
                    "color": ["#E0F2F1", "#DBEAFE", "#EDE9FE", "#DCFCE7", "#FEF3C7", "#FEE2E2"],
                },
                link={"source": source, "target": target, "value": value, "color": colors},
            )
        ]
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10), font=dict(size=12))
    return fig


def line_chart(
    df: pd.DataFrame,
    y_cols: list[str],
    title: str,
    y_axis_title: str,
    as_percent: bool = False,
    threshold: float | None = None,
) -> go.Figure:
    fig = go.Figure()
    for col in y_cols:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[col],
                mode="lines",
                name=DISPLAY_NAMES.get(col.replace("_ma", ""), col),
                line=dict(width=2.5),
                hovertemplate="%{x|%b %d, %Y}<br>%{y:.2%}<extra>%{fullData.name}</extra>"
                if as_percent
                else "%{x|%b %d, %Y}<br>%{y:,.0f}<extra>%{fullData.name}</extra>",
            )
        )
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="#DC2626",
            annotation_text="Alert threshold",
            annotation_position="top left",
        )
    fig.update_layout(
        title=title,
        height=390,
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(orientation="h", y=-0.18),
        yaxis_title=y_axis_title,
        xaxis_title=None,
    )
    if as_percent:
        fig.update_yaxes(tickformat=".1%")
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: list[str], title: str, barmode: str = "group") -> go.Figure:
    melted = df.melt(id_vars=[x], value_vars=y, var_name="metric", value_name="value")
    melted["metric"] = melted["metric"].map(DISPLAY_NAMES).fillna(melted["metric"])
    fig = px.bar(melted, x=x, y="value", color="metric", barmode=barmode, title=title)
    fig.update_layout(height=390, margin=dict(l=10, r=10, t=55, b=10), legend=dict(orientation="h", y=-0.18))
    fig.update_yaxes(title=None)
    fig.update_xaxes(title=None)
    return fig


inject_css()

with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload UAC CSV", type=["csv"])
    smoothing_window = st.slider("Rolling window", 3, 30, 7, help="Days used for rolling trend and alert calculations.")

    source_bytes = uploaded.getvalue() if uploaded is not None else None
    source_name = uploaded.name if uploaded is not None else None

    try:
        full_df = cached_prepare_data(source_bytes, source_name, smoothing_window)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    min_date = full_df["date"].min().date()
    max_date = full_df["date"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    st.divider()
    st.subheader("Metric toggles")
    show_transfer = st.checkbox("Transfer Efficiency Ratio", value=True)
    show_discharge = st.checkbox("Discharge Effectiveness Index", value=True)
    show_throughput = st.checkbox("Pipeline Throughput", value=True)
    show_stability = st.checkbox("Outcome Stability Score", value=True)

    st.divider()
    st.subheader("Alert thresholds")
    transfer_threshold = st.slider("Minimum transfer efficiency", 0.0, 1.5, 0.60, 0.05, format="%.2f")
    discharge_threshold = st.slider("Minimum discharge effectiveness", 0.0, 0.08, 0.015, 0.001, format="%.3f")
    backlog_threshold = st.slider("Backlog pressure per reporting day", -250, 250, 0, 10)
    stagnation_days = st.slider("Minimum bottleneck reporting days", 2, 20, 5)

thresholds = DashboardThresholds(
    transfer_efficiency=transfer_threshold,
    discharge_effectiveness=discharge_threshold,
    backlog_pressure=backlog_threshold,
    stagnation_days=stagnation_days,
)

selected_df = filter_by_date(full_df, start_date, end_date)
summary = period_summary(selected_df)
deltas = compare_to_previous_period(full_df, selected_df)
monthly_df = monthly_summary(selected_df)
weekday_df = weekday_summary(selected_df)
bottlenecks = detect_bottlenecks(selected_df, thresholds, smoothing_window=smoothing_window)

st.markdown(
    """
    <div class="app-header">
        <div class="app-kicker">U.S. Department of Health and Human Services analytics concept</div>
        <h1 class="app-title">Care Transition Efficiency & Placement Outcome Analytics</h1>
        <div class="app-subtitle">
            A process-efficiency dashboard for monitoring CBP intake, transfer velocity, HHS care load,
            discharge performance, backlog pressure, and placement outcome stability.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if selected_df.empty:
    st.warning("No rows are available for the selected date range.")
    st.stop()

source_label = uploaded.name if uploaded else str(DEFAULT_DATA_PATH)
st.caption(
    f"Source: {Path(source_label).name} | Reporting dates: "
    f"{summary['start_date'].date()} to {summary['end_date'].date()} | "
    f"{summary['days']} usable reporting days"
)

kpi_cols = st.columns(5)
with kpi_cols[0]:
    metric_card(
        "Transfer Efficiency Ratio",
        format_percent(summary["transfer_efficiency"]),
        "Transfers divided by active CBP custody.",
        deltas.get("transfer_efficiency"),
    )
with kpi_cols[1]:
    metric_card(
        "Discharge Effectiveness Index",
        format_percent(summary["discharge_effectiveness"], decimals=2),
        "Discharges divided by active HHS care load.",
        deltas.get("discharge_effectiveness"),
    )
with kpi_cols[2]:
    metric_card(
        "Pipeline Throughput",
        format_percent(summary["pipeline_throughput"]),
        "Discharges divided by CBP intake.",
        deltas.get("pipeline_throughput"),
    )
with kpi_cols[3]:
    metric_card(
        "HHS Backlog Accumulation",
        format_number(summary["net_hhs_backlog"]),
        "Transfers minus discharges across selected period.",
        deltas.get("net_hhs_backlog"),
        inverse=True,
    )
with kpi_cols[4]:
    metric_card(
        "Outcome Stability Score",
        format_percent(summary["outcome_stability"], decimals=0),
        "Higher score means less variation in discharge effectiveness.",
        deltas.get("outcome_stability"),
    )

volume_cols = st.columns(4)
volume_cols[0].metric("CBP intake", format_number(summary["apprehended"]))
volume_cols[1].metric("Transfers to HHS", format_number(summary["transferred"]))
volume_cols[2].metric("Sponsor placements", format_number(summary["discharged"]))
volume_cols[3].metric("Latest HHS care load", format_number(summary["latest_hhs_care"]))

tab_pipeline, tab_efficiency, tab_bottlenecks, tab_outcomes, tab_method = st.tabs(
    ["Pipeline Flow", "Efficiency Panels", "Bottleneck Detection", "Outcome Trends", "Data & Method"]
)

with tab_pipeline:
    section_title(
        "Care Pipeline Flow",
        "Track how daily intake moves through CBP custody, HHS care, and sponsor placement over the selected period.",
    )
    left, right = st.columns([1.05, 1])
    with left:
        st.plotly_chart(flow_sankey(summary), width="stretch")
    with right:
        fig_load = line_chart(
            selected_df,
            ["cbp_custody", "hhs_care"],
            "Active Care Load",
            "Children",
        )
        st.plotly_chart(fig_load, width="stretch")
    st.plotly_chart(
        bar_chart(
            selected_df,
            "date",
            ["apprehended", "transferred", "discharged"],
            "Daily Pipeline Volumes",
        ),
        width="stretch",
    )

with tab_efficiency:
    section_title(
        "Transfer & Discharge Efficiency Panels",
        "Monitor ratio-based operating performance with configurable alert thresholds and rolling averages.",
    )
    selected_metrics = []
    if show_transfer:
        selected_metrics.append("transfer_efficiency_ma")
    if show_discharge:
        selected_metrics.append("discharge_effectiveness_ma")
    if show_throughput:
        selected_metrics.append("pipeline_throughput_ma")
    if selected_metrics:
        st.plotly_chart(
            line_chart(
                selected_df,
                selected_metrics,
                f"{smoothing_window}-Reporting-Day Rolling Efficiency",
                "Ratio",
                as_percent=True,
            ),
            width="stretch",
        )
    else:
        st.info("Select at least one ratio metric in the sidebar.")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            line_chart(
                selected_df,
                ["transfer_efficiency_ma"],
                "Transfer Efficiency vs Threshold",
                "Transfers / CBP custody",
                as_percent=True,
                threshold=transfer_threshold,
            ),
            width="stretch",
        )
    with c2:
        st.plotly_chart(
            line_chart(
                selected_df,
                ["discharge_effectiveness_ma"],
                "Discharge Effectiveness vs Threshold",
                "Discharges / HHS care",
                as_percent=True,
                threshold=discharge_threshold,
            ),
            width="stretch",
        )

with tab_bottlenecks:
    section_title(
        "Bottleneck Detection",
        "Identify periods when transfer or discharge performance falls below thresholds while unresolved care pressure grows.",
    )
    left, right = st.columns([.82, 1.18])
    with left:
        for alert in build_alerts(selected_df, thresholds):
            alert_card(alert)
    with right:
        st.plotly_chart(
            line_chart(
                selected_df,
                ["hhs_net_flow_ma", "system_net_flow_ma"],
                f"{smoothing_window}-Reporting-Day Backlog Pressure",
                "Children per reporting day",
                threshold=backlog_threshold,
            ),
            width="stretch",
        )

    heat_df = selected_df.copy()
    heat_df["risk_bucket"] = pd.cut(
        heat_df["hhs_net_flow_ma"],
        bins=[-10_000, -100, 0, 100, 10_000],
        labels=["Strong relief", "Relief", "Pressure", "High pressure"],
    )
    heat = px.scatter(
        heat_df,
        x="date",
        y="discharge_effectiveness",
        size=heat_df["hhs_net_flow_ma"].abs().clip(lower=3),
        color="risk_bucket",
        title="Discharge Effectiveness and HHS Net Flow Pressure",
        labels={"date": "", "discharge_effectiveness": "Discharge effectiveness", "risk_bucket": "Net flow state"},
        color_discrete_map={
            "Strong relief": "#0F766E",
            "Relief": "#2563EB",
            "Pressure": "#D97706",
            "High pressure": "#DC2626",
        },
    )
    heat.update_yaxes(tickformat=".2%")
    heat.update_layout(height=410, margin=dict(l=10, r=10, t=55, b=10), legend=dict(orientation="h", y=-0.18))
    st.plotly_chart(heat, width="stretch")

    if bottlenecks.empty:
        st.success("No sustained bottleneck periods meet the current threshold settings.")
    else:
        display_bottlenecks = bottlenecks.copy()
        display_bottlenecks["start_date"] = display_bottlenecks["start_date"].dt.strftime("%Y-%m-%d")
        display_bottlenecks["end_date"] = display_bottlenecks["end_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            display_bottlenecks[
                [
                    "start_date",
                    "end_date",
                    "reporting_days",
                    "duration_days",
                    "avg_transfer_efficiency",
                    "avg_discharge_effectiveness",
                    "avg_hhs_net_flow",
                    "total_hhs_net_flow",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "avg_transfer_efficiency": st.column_config.ProgressColumn(
                    "Avg transfer efficiency", format="%.1f%%", min_value=0, max_value=1
                ),
                "avg_discharge_effectiveness": st.column_config.NumberColumn(
                    "Avg discharge effectiveness", format="%.2%"
                ),
                "avg_hhs_net_flow": st.column_config.NumberColumn("Avg HHS net flow", format="%.0f"),
                "total_hhs_net_flow": st.column_config.NumberColumn("Total HHS net flow", format="%.0f"),
            },
        )

with tab_outcomes:
    section_title(
        "Outcome Trend Analysis",
        "Evaluate whether sponsor placements are keeping pace with inflows and whether outcomes are stable over time.",
    )
    monthly_left, monthly_right = st.columns(2)
    with monthly_left:
        monthly_line = px.line(
            monthly_df,
            x="month_start",
            y=["discharge_effectiveness", "pipeline_throughput"],
            markers=True,
            title="Month-over-Month Placement Performance",
            labels={"month_start": "", "value": "Ratio", "variable": "Metric"},
        )
        monthly_line.update_yaxes(tickformat=".1%")
        monthly_line.update_layout(height=390, margin=dict(l=10, r=10, t=55, b=10), legend=dict(orientation="h", y=-0.18))
        st.plotly_chart(monthly_line, width="stretch")
    with monthly_right:
        monthly_bar = px.bar(
            monthly_df,
            x="month_start",
            y="hhs_net_flow",
            color="hhs_net_flow",
            color_continuous_scale=["#0F766E", "#F7F9FC", "#DC2626"],
            title="Monthly HHS Backlog Accumulation",
            labels={"month_start": "", "hhs_net_flow": "Transfers minus discharges"},
        )
        monthly_bar.update_layout(height=390, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
        st.plotly_chart(monthly_bar, width="stretch")

    outcome_cols = ["outcome_stability"] if show_stability else []
    if outcome_cols:
        st.plotly_chart(
            line_chart(
                selected_df,
                outcome_cols,
                "Rolling Outcome Stability Score",
                "Score",
                as_percent=True,
            ),
            width="stretch",
        )

    st.plotly_chart(
        bar_chart(
            weekday_df,
            "weekday",
            ["apprehended", "transferred", "discharged"],
            "Weekday vs Weekend Transition Speed",
        ),
        width="stretch",
    )

with tab_method:
    section_title(
        "Data & Method",
        "Transparent metric definitions, cleaned data preview, and caveats for policy interpretation.",
    )
    method_cols = st.columns(2)
    with method_cols[0]:
        st.markdown(
            """
            **Core metrics**

            - **Transfer Efficiency Ratio:** transfers out of CBP custody divided by active CBP custody.
            - **Discharge Effectiveness Index:** discharges from HHS care divided by active HHS care.
            - **Pipeline Throughput:** discharges divided by CBP intake for the reporting period.
            - **Backlog Accumulation Rate:** transfers minus discharges; positive values indicate HHS pressure.
            - **Outcome Stability Score:** one minus the rolling coefficient of variation in discharge effectiveness.
            """
        )
    with method_cols[1]:
        st.markdown(
            """
            **Interpretation notes**

            - These are aggregate reporting metrics, not child-level longitudinal records.
            - Daily ratios compare current-period flows with same-day care loads.
            - Throughput can exceed 100% when discharges include children admitted before the selected period.
            - Missing or blank rows are removed during cleaning.
            """
        )

    preview_cols = [
        "date",
        "apprehended",
        "cbp_custody",
        "transferred",
        "hhs_care",
        "discharged",
        "transfer_efficiency",
        "discharge_effectiveness",
        "pipeline_throughput",
        "hhs_net_flow",
    ]
    preview = selected_df[preview_cols].copy()
    preview["date"] = preview["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        preview.sort_values("date", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "transfer_efficiency": st.column_config.NumberColumn("Transfer efficiency", format="%.1%"),
            "discharge_effectiveness": st.column_config.NumberColumn("Discharge effectiveness", format="%.2%"),
            "pipeline_throughput": st.column_config.NumberColumn("Pipeline throughput", format="%.1%"),
            "hhs_net_flow": st.column_config.NumberColumn("HHS net flow", format="%.0f"),
        },
    )
