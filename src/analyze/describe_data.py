"""
Analyzes cleaned health metrics and provides a summary report. This includes:
- Latest trend metric values
- Daily, weekly, and monthly deltas
- 90-day rolling statistics
- Saves text and CSV reports to output/

Returns summary lines to the caller for optional custom printing.

Author: Lincoln Quick
"""

import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def describe_data(df: pd.DataFrame, output_dir: str = "output") -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    def get_metric(name): 
        return f"Trend{name}" if f"Trend{name}" in df.columns else name

    latest = df.iloc[-1]
    daily = df.diff().tail(1)
    weekly = df.diff(periods=7).tail(1)
    monthly = df.resample("ME").last().diff().tail(1)
    last_90 = df.tail(90)

    lines = []
    def add_line(label, value):
        line = f"{label:<35}: {value}"
        lines.append(line)

    lines.append("--- Metric Summary ---")
    for metric in ["Weight", "BodyFatPercentage", "LeanBodyMass", "CaloriesIn", "BasalCaloriesBurned", "ActiveCaloriesBurned"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"Latest {metric}", f"{latest.get(col, 'N/A'):.2f}")

    lines.append("\n--- Delta Summary ---")
    for metric in ["Weight", "BodyFatPercentage", "LeanBodyMass"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"{metric} change (1d)", f"{daily[col].values[0]:.2f}")
            add_line(f"{metric} change (7d)", f"{weekly[col].values[0]:.2f}")
            add_line(f"{metric} change (monthly)", f"{monthly[col].values[0]:.2f}")

    lines.append("\n--- 90-Day Statistics ---")
    for metric in ["Weight", "LeanBodyMass", "CaloriesIn", "NetCalories", "TDEE"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"{metric} mean (90d)", f"{last_90[col].mean():.2f}")
            add_line(f"{metric} std dev (90d)", f"{last_90[col].std():.2f}")
            add_line(f"{metric} min (90d)", f"{last_90[col].min():.2f}")
            add_line(f"{metric} max (90d)", f"{last_90[col].max():.2f}")

    # Save to file
    with open(os.path.join(output_dir, "summary_report.txt"), "w") as f:
        for line in lines:
            f.write(line + "\n")
    logger.info("Summary saved to output/summary_report.txt")

    # Save delta CSV
    deltas = {
        "Metric": [],
        "Delta_1d": [],
        "Delta_7d": [],
        "Delta_month": [],
    }
    for col in df.columns:
        deltas["Metric"].append(col)
        deltas["Delta_1d"].append(daily[col].values[0] if col in daily else None)
        deltas["Delta_7d"].append(weekly[col].values[0] if col in weekly else None)
        deltas["Delta_month"].append(monthly[col].values[0] if col in monthly else None)

    pd.DataFrame(deltas).to_csv(os.path.join(output_dir, "metric_deltas.csv"), index=False)
    logger.info("Delta CSV saved to output/metric_deltas.csv")

    return lines