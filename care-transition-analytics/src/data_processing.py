"""Data preparation and analytics for the UAC care transition dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "HHS_Unaccompanied_Alien_Children_Program.csv"


COLUMN_MAP = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "apprehended",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "transferred",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "discharged",
}

DISPLAY_NAMES = {
    "apprehended": "Children apprehended and placed in CBP custody",
    "cbp_custody": "Children in CBP custody",
    "transferred": "Children transferred out of CBP custody",
    "hhs_care": "Children in HHS Care",
    "discharged": "Children discharged from HHS Care",
    "transfer_efficiency": "Transfer Efficiency Ratio",
    "discharge_effectiveness": "Discharge Effectiveness Index",
    "pipeline_throughput": "Pipeline Throughput",
    "hhs_net_flow": "HHS Net Flow",
    "system_net_flow": "System Net Flow",
    "outcome_stability": "Outcome Stability Score",
}


@dataclass(frozen=True)
class DashboardThresholds:
    """Operational thresholds used for alerting and bottleneck tagging."""

    transfer_efficiency: float = 0.60
    discharge_effectiveness: float = 0.015
    backlog_pressure: float = 0.0
    stagnation_days: int = 5


def load_raw_data(source: str | Path | BinaryIO | None = None) -> pd.DataFrame:
    """Load the source CSV from a path or Streamlit uploaded file."""

    path_or_buffer = source if source is not None else DEFAULT_DATA_PATH
    if isinstance(path_or_buffer, (str, Path)) and not Path(path_or_buffer).exists():
        raise FileNotFoundError(
            "Source CSV not found. Place the file in data/raw/ or upload it in the sidebar."
        )
    return pd.read_csv(path_or_buffer)


def clean_uac_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names, types, sort order, and blank trailing rows."""

    missing = sorted(set(COLUMN_MAP) - set(raw_df.columns))
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    df = raw_df.rename(columns=COLUMN_MAP).loc[:, list(COLUMN_MAP.values())].copy()
    df = df.dropna(how="all")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_cols = ["apprehended", "cbp_custody", "transferred", "hhs_care", "discharged"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False).str.strip(),
            errors="coerce",
        )

    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator.astype(float).divide(denominator.replace({0: np.nan}).astype(float))
    return result.replace([np.inf, -np.inf], np.nan)


def add_pipeline_metrics(df: pd.DataFrame, smoothing_window: int = 7) -> pd.DataFrame:
    """Add transition, discharge, backlog, stability, and calendar features."""

    window = max(int(smoothing_window), 1)
    out = df.copy()
    out["transfer_efficiency"] = _safe_ratio(out["transferred"], out["cbp_custody"])
    out["discharge_effectiveness"] = _safe_ratio(out["discharged"], out["hhs_care"])
    out["pipeline_throughput"] = _safe_ratio(out["discharged"], out["apprehended"])

    out["cbp_transfer_gap"] = out["apprehended"] - out["transferred"]
    out["hhs_net_flow"] = out["transferred"] - out["discharged"]
    out["system_net_flow"] = out["apprehended"] - out["discharged"]

    out["transfer_efficiency_ma"] = out["transfer_efficiency"].rolling(window, min_periods=1).mean()
    out["discharge_effectiveness_ma"] = out["discharge_effectiveness"].rolling(window, min_periods=1).mean()
    out["pipeline_throughput_ma"] = out["pipeline_throughput"].rolling(window, min_periods=1).mean()
    out["hhs_net_flow_ma"] = out["hhs_net_flow"].rolling(window, min_periods=1).mean()
    out["system_net_flow_ma"] = out["system_net_flow"].rolling(window, min_periods=1).mean()

    rolling_mean = out["discharge_effectiveness"].rolling(window, min_periods=3).mean()
    rolling_std = out["discharge_effectiveness"].rolling(window, min_periods=3).std()
    coefficient_variation = rolling_std.divide(rolling_mean.replace({0: np.nan}))
    out["outcome_stability"] = (1 - coefficient_variation).clip(lower=0, upper=1)
    out["outcome_stability"] = out["outcome_stability"].fillna(out["outcome_stability"].median())

    out["month"] = out["date"].dt.to_period("M").astype(str)
    out["month_start"] = out["date"].dt.to_period("M").dt.to_timestamp()
    out["weekday"] = out["date"].dt.day_name()
    out["is_weekend"] = out["date"].dt.dayofweek >= 5
    return out


def prepare_data(source: str | Path | BinaryIO | None = None, smoothing_window: int = 7) -> pd.DataFrame:
    """Load, clean, and enrich the UAC dataset."""

    raw = load_raw_data(source)
    cleaned = clean_uac_data(raw)
    return add_pipeline_metrics(cleaned, smoothing_window=smoothing_window)


def filter_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Return rows within an inclusive date range."""

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    return df.loc[(df["date"] >= start) & (df["date"] <= end)].copy()


def period_summary(df: pd.DataFrame) -> dict[str, float | int | pd.Timestamp]:
    """Compute KPI values for the selected period."""

    if df.empty:
        return {}

    latest = df.iloc[-1]
    return {
        "start_date": df["date"].min(),
        "end_date": df["date"].max(),
        "days": int(len(df)),
        "apprehended": float(df["apprehended"].sum()),
        "transferred": float(df["transferred"].sum()),
        "discharged": float(df["discharged"].sum()),
        "avg_cbp_custody": float(df["cbp_custody"].mean()),
        "avg_hhs_care": float(df["hhs_care"].mean()),
        "latest_cbp_custody": float(latest["cbp_custody"]),
        "latest_hhs_care": float(latest["hhs_care"]),
        "transfer_efficiency": float(df["transferred"].sum() / df["cbp_custody"].sum())
        if df["cbp_custody"].sum()
        else np.nan,
        "discharge_effectiveness": float(df["discharged"].sum() / df["hhs_care"].sum())
        if df["hhs_care"].sum()
        else np.nan,
        "pipeline_throughput": float(df["discharged"].sum() / df["apprehended"].sum())
        if df["apprehended"].sum()
        else np.nan,
        "net_hhs_backlog": float(df["hhs_net_flow"].sum()),
        "net_system_backlog": float(df["system_net_flow"].sum()),
        "outcome_stability": float(df["outcome_stability"].mean()),
    }


def compare_to_previous_period(full_df: pd.DataFrame, selected_df: pd.DataFrame) -> dict[str, float]:
    """Compare selected KPIs against the immediately preceding period."""

    if selected_df.empty:
        return {}

    start = selected_df["date"].min()
    period_days = max((selected_df["date"].max() - start).days + 1, 1)
    previous_start = start - pd.Timedelta(days=period_days)
    previous_end = start - pd.Timedelta(days=1)
    previous_df = filter_by_date(full_df, previous_start, previous_end)

    current = period_summary(selected_df)
    previous = period_summary(previous_df)
    if not previous:
        return {}

    deltas = {}
    for key in [
        "transfer_efficiency",
        "discharge_effectiveness",
        "pipeline_throughput",
        "net_hhs_backlog",
        "outcome_stability",
    ]:
        if key in current and key in previous and pd.notna(previous[key]):
            deltas[key] = float(current[key] - previous[key])
    return deltas


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly volumes, ratios, and backlog pressure."""

    grouped = (
        df.groupby(["month_start", "month"], as_index=False)
        .agg(
            apprehended=("apprehended", "sum"),
            transferred=("transferred", "sum"),
            discharged=("discharged", "sum"),
            cbp_custody=("cbp_custody", "mean"),
            hhs_care=("hhs_care", "mean"),
            hhs_net_flow=("hhs_net_flow", "sum"),
            system_net_flow=("system_net_flow", "sum"),
            outcome_stability=("outcome_stability", "mean"),
            reporting_days=("date", "count"),
        )
        .sort_values("month_start")
    )
    grouped["transfer_efficiency"] = _safe_ratio(grouped["transferred"], grouped["cbp_custody"] * grouped["reporting_days"])
    grouped["discharge_effectiveness"] = _safe_ratio(grouped["discharged"], grouped["hhs_care"] * grouped["reporting_days"])
    grouped["pipeline_throughput"] = _safe_ratio(grouped["discharged"], grouped["apprehended"])
    return grouped


def weekday_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate average performance by weekday."""

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = (
        df.groupby("weekday", as_index=False)
        .agg(
            apprehended=("apprehended", "mean"),
            transferred=("transferred", "mean"),
            discharged=("discharged", "mean"),
            transfer_efficiency=("transfer_efficiency", "mean"),
            discharge_effectiveness=("discharge_effectiveness", "mean"),
            pipeline_throughput=("pipeline_throughput", "mean"),
            reporting_days=("date", "count"),
        )
        .set_index("weekday")
        .reindex(order)
        .dropna(how="all")
        .reset_index()
    )
    return grouped


def detect_bottlenecks(
    df: pd.DataFrame,
    thresholds: DashboardThresholds,
    smoothing_window: int = 7,
) -> pd.DataFrame:
    """Flag dates where low efficiency or positive net flow suggests process pressure."""

    if df.empty:
        return pd.DataFrame()

    out = df.copy()
    out["low_transfer"] = out["transfer_efficiency_ma"] < thresholds.transfer_efficiency
    out["low_discharge"] = out["discharge_effectiveness_ma"] < thresholds.discharge_effectiveness
    out["hhs_backlog_pressure"] = out["hhs_net_flow_ma"] > thresholds.backlog_pressure
    out["system_backlog_pressure"] = out["system_net_flow_ma"] > thresholds.backlog_pressure
    out["risk_score"] = (
        out["low_transfer"].astype(int)
        + out["low_discharge"].astype(int)
        + out["hhs_backlog_pressure"].astype(int)
        + out["system_backlog_pressure"].astype(int)
    )

    out["bottleneck_day"] = out["risk_score"] >= 2
    out["streak_id"] = (out["bottleneck_day"] != out["bottleneck_day"].shift()).cumsum()
    streaks = (
        out.loc[out["bottleneck_day"]]
        .groupby("streak_id")
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            reporting_days=("date", "count"),
            avg_risk_score=("risk_score", "mean"),
            avg_transfer_efficiency=("transfer_efficiency_ma", "mean"),
            avg_discharge_effectiveness=("discharge_effectiveness_ma", "mean"),
            avg_hhs_net_flow=("hhs_net_flow_ma", "mean"),
            total_hhs_net_flow=("hhs_net_flow", "sum"),
        )
        .reset_index(drop=True)
    )
    if streaks.empty:
        return streaks

    streaks["duration_days"] = (streaks["end_date"] - streaks["start_date"]).dt.days + 1
    streaks = streaks.loc[streaks["reporting_days"] >= max(1, thresholds.stagnation_days)]
    return streaks.sort_values(["avg_risk_score", "duration_days"], ascending=False)


def build_alerts(df: pd.DataFrame, thresholds: DashboardThresholds) -> list[dict[str, str]]:
    """Create human-readable alert cards for the most recent selected period state."""

    if df.empty:
        return []

    latest = df.iloc[-1]
    alerts: list[dict[str, str]] = []

    if latest["transfer_efficiency_ma"] < thresholds.transfer_efficiency:
        alerts.append(
            {
                "level": "High",
                "title": "CBP -> HHS transfer efficiency below threshold",
                "detail": (
                    f"{latest['transfer_efficiency_ma']:.1%} rolling transfer efficiency "
                    f"vs {thresholds.transfer_efficiency:.1%} threshold."
                ),
            }
        )

    if latest["discharge_effectiveness_ma"] < thresholds.discharge_effectiveness:
        alerts.append(
            {
                "level": "High",
                "title": "Sponsor placement effectiveness below threshold",
                "detail": (
                    f"{latest['discharge_effectiveness_ma']:.2%} rolling discharge effectiveness "
                    f"vs {thresholds.discharge_effectiveness:.2%} threshold."
                ),
            }
        )

    if latest["hhs_net_flow_ma"] > thresholds.backlog_pressure:
        alerts.append(
            {
                "level": "Medium",
                "title": "HHS care load pressure increasing",
                "detail": (
                    f"Rolling net flow is {latest['hhs_net_flow_ma']:.0f} more transfers "
                    "than discharges per reporting day."
                ),
            }
        )

    if latest["outcome_stability"] < 0.50:
        alerts.append(
            {
                "level": "Medium",
                "title": "Placement outcomes are volatile",
                "detail": f"Outcome stability score is {latest['outcome_stability']:.0%}.",
            }
        )

    if not alerts:
        alerts.append(
            {
                "level": "Normal",
                "title": "No current threshold breach",
                "detail": "The latest selected reporting day is within the configured alert thresholds.",
            }
        )

    return alerts


def format_number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f}"


def format_percent(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}%}"

