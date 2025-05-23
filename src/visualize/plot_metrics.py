# src/visualize/plot_metrics.py

"""
plot_metrics.py

Generates grouped and enhanced time series plots for health metrics over
various time periods (full, yearly, monthly). Groups include:
- Weight & Body Composition
- Calories & Energy Balance
- Activity (Steps and Distance)

Uses smoothed 'Trend' metrics when available to reduce visual noise and
fill in gaps caused by missing raw data.

Author: Lincoln Quick
"""

import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
from config.constants import KG_TO_LBS

logger = logging.getLogger(__name__)

# Define metric groupings
PLOT_GROUPS = {
    "weight": ["Weight", "BodyFatPercentage", "LeanBodyMass"],
    "calories": ["CaloriesIn", "TDEE", "EnergyBalance", "RMR", "PA", "BasalCaloriesBurned", "ActiveCaloriesBurned"],
    "activity": ["StepCount", "DistanceWalkingRunning"],
}

# Map raw metrics to their smoothed "Trend" versions
TREND_MAPPING = {
    'Weight': 'TrendWeight',
    'BodyFatPercentage': 'TrendBodyFatPercentage',
    'LeanBodyMass': 'TrendLeanBodyMass',
    'CaloriesIn': 'TrendCaloriesIn',
    'TDEE': 'TrendTDEE',
    'EnergyBalance': 'EnergyBalance',
    'RMR': 'RMR',
    'PA': 'PA',
    'BasalCaloriesBurned': 'TrendBasalCaloriesBurned',
    'ActiveCaloriesBurned': 'TrendActiveCaloriesBurned',
}


def plot_metrics(
        df: pd.DataFrame,
        output_dir: str = "output/plots",
        periods: list[str] = ["full", "year", "month"],
        use_imperial_units: bool = False):
    """
    Generate and save time series plots for grouped health metrics.

    Args:
        df (pd.DataFrame): Cleaned health data with a datetime 'date' column.
        output_dir (str): Root output folder to save plots.
        periods (list[str]): Which time periods to generate plots for ('full', 'year', 'month').
        use_imperial_units (bool): Whether to display weight in pounds.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Log missing values for diagnostics
    for trend_metric in ["TrendWeight", "TrendBodyFatPercentage", "TrendLeanBodyMass"]:
        if trend_metric in df.columns and df[trend_metric].isna().sum() > 0:
            missing_dates = df[df[trend_metric].isna()]["date"].tolist()
            logger.debug(f"{trend_metric} has missing values on: {missing_dates}")

    # Convert mass units if needed
    if use_imperial_units:
        if "TrendWeight" in df.columns:
            df["TrendWeight"] *= KG_TO_LBS
        if "TrendLeanBodyMass" in df.columns:
            df["TrendLeanBodyMass"] *= KG_TO_LBS

    for group_name, metrics in PLOT_GROUPS.items():
        available_metrics = []
        for m in metrics:
            trend_col = TREND_MAPPING.get(m, m)
            if trend_col in df.columns and df[trend_col].notna().sum() > 0:
                available_metrics.append(trend_col)

        if not available_metrics:
            logger.warning(f"No valid metrics found for group: {group_name}")
            continue

        if "full" in periods:
            _plot_time_series(df, available_metrics, group_name, output_dir, label="full", use_imperial_units=use_imperial_units)

        if "year" in periods:
            for year, year_df in df.groupby(df["date"].dt.year):
                _plot_time_series(year_df, available_metrics, group_name, output_dir, label=str(year), use_imperial_units=use_imperial_units)

        if "month" in periods:
            monthly_groups = df.groupby([df["date"].dt.year, df["date"].dt.month])
            for (year, month), month_df in monthly_groups:
                label = f"{year}-{month:02d}"
                _plot_time_series(month_df, available_metrics, group_name, output_dir, label=label, use_imperial_units=use_imperial_units)


def _plot_time_series(df: pd.DataFrame, metrics: list[str], group_name: str, output_dir: str, label: str, use_imperial_units: bool = False):
    """
    Internal helper to plot and save a single time series graph.

    Args:
        df (pd.DataFrame): Data subset to plot.
        metrics (list[str]): Column names to include.
        group_name (str): Name of the plot group (used in filename).
        output_dir (str): Output folder path.
        label (str): Time period label (e.g., "full", "2025", "2025-04").
        use_imperial_units (bool): Whether to show weight in pounds.
    """
    if df.empty:
        logger.warning(f"Skipping empty data for {group_name} - {label}")
        return

    plt.figure(figsize=(10, 6))

    if group_name == "weight":
        ax1 = plt.gca()
        ax2 = ax1.twinx()

        for col in metrics:
            if col == "TrendWeight":
                label_text = "Weight (lb)" if use_imperial_units else "Weight (kg)"
                ax1.plot(df["date"], df[col], label=label_text, color="tab:blue", linewidth=2)
            elif col == "TrendLeanBodyMass":
                label_text = "Lean Body Mass (lb)" if use_imperial_units else "Lean Body Mass (kg)"
                ax1.plot(df["date"], df[col], label=label_text, color="tab:green", linewidth=2)
            elif col == "TrendBodyFatPercentage":
                ax2.plot(df["date"], df[col] * 100, label="Body Fat (%)", color="tab:red", linewidth=2, linestyle="--")

        ax1.set_ylabel("Mass (lb)" if use_imperial_units else "Mass (kg)")
        ax2.set_ylabel("Body Fat (%)")

        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    elif group_name == "calories":
        ax = plt.gca()
        if "RMR" in metrics and "PA" in metrics:
            ax.stackplot(df["date"],
                         df["RMR"],
                         df["PA"],
                         labels=["RMR", "Physical Activity"],
                         colors=["#9ecae1", "#6baed6"])
        if "TrendCaloriesIn" in metrics:
            ax.plot(df["date"], df["TrendCaloriesIn"], label="Calories In", color="tab:orange", linewidth=2)
        if "EnergyBalance" in metrics:
            ax.plot(df["date"], df["EnergyBalance"], label="Energy Balance", color="tab:red", linestyle="--", linewidth=2)

        ax.set_ylabel("Calories")
        ax.legend()

    elif group_name == "activity":
        ax1 = plt.gca()
        ax2 = ax1.twinx()

        if "StepCount" in df:
            ax1.bar(df["date"], df["StepCount"], width=0.8, label="Steps", alpha=0.4, color="tab:blue")
        if "DistanceWalkingRunning" in df:
            ax2.plot(df["date"], df["DistanceWalkingRunning"], label="Distance (km)", color="tab:green", linewidth=2)

        ax1.set_ylabel("Step Count")
        ax2.set_ylabel("Distance (km)")

        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    else:
        for col in metrics:
            if col in df.columns:
                plt.plot(df["date"], df[col], label=col, linewidth=2)
        plt.ylabel("Value")

    plt.title(f"{group_name.title()} Metrics - {label}")
    plt.xlabel("Date")
    plt.grid(True)
    plt.tight_layout()

    group_dir = os.path.join(output_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)
    filename = f"{group_name}_{label}.png"
    filepath = os.path.join(group_dir, filename)
    plt.savefig(filepath)
    plt.close()

    logger.debug(f"Saved plot: {filepath}")