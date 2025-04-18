# src/analyze/describe_data.py

"""
Analyzes cleaned health metrics and provides a summary report. This includes:
- Latest trend metric values
- Daily, weekly, and monthly deltas
- 90-day rolling statistics
- Console output with color formatting
- Saves text and CSV reports to output/

Uses Trend-prefixed metrics if available for more stable summaries.

Author: Lincoln Quick
"""

import os
import logging
import pandas as pd
from colorama import Fore, Style, init

init(autoreset=True)
logger = logging.getLogger(__name__)

def describe_data(df: pd.DataFrame, output_dir: str = "output") -> None:
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Use Trend metrics if they exist
    def get_metric(name): 
        return f"Trend{name}" if f"Trend{name}" in df.columns else name

    # Compute time deltas and rolling window
    latest = df.iloc[-1]
    daily = df.diff().tail(1)
    weekly = df.diff(periods=7).tail(1)
    monthly = df.resample("ME").last().diff().tail(1)
    last_90 = df.tail(90)

    # Summary output
    lines = []
    def add_line(label, value, color=Fore.WHITE):
        line = f"{color}{label:<35}: {value}{Style.RESET_ALL}"
        print(line)
        lines.append(f"{label:<35}: {value}")

    print(Fore.CYAN + "\n--- Metric Summary ---\n" + Style.RESET_ALL)
    for metric in ["Weight", "BodyFatPercentage", "LeanBodyMass", "CaloriesIn", "BasalCaloriesBurned", "ActiveCaloriesBurned"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"Latest {metric}", f"{latest.get(col, 'N/A'):.2f}")

    print(Fore.YELLOW + "\n--- Delta Summary ---\n" + Style.RESET_ALL)
    for metric in ["Weight", "BodyFatPercentage", "LeanBodyMass"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"{metric} change (1d)", f"{daily[col].values[0]:.2f}", Fore.YELLOW)
            add_line(f"{metric} change (7d)", f"{weekly[col].values[0]:.2f}", Fore.YELLOW)
            add_line(f"{metric} change (monthly)", f"{monthly[col].values[0]:.2f}", Fore.YELLOW)

    print(Fore.GREEN + "\n--- 90-Day Statistics ---\n" + Style.RESET_ALL)
    for metric in ["Weight", "LeanBodyMass", "CaloriesIn", "NetCalories", "TDEE"]:
        col = get_metric(metric)
        if col in df.columns:
            add_line(f"{metric} mean (90d)", f"{last_90[col].mean():.2f}", Fore.GREEN)
            add_line(f"{metric} std dev (90d)", f"{last_90[col].std():.2f}", Fore.GREEN)
            add_line(f"{metric} min (90d)", f"{last_90[col].min():.2f}", Fore.GREEN)
            add_line(f"{metric} max (90d)", f"{last_90[col].max():.2f}", Fore.GREEN)

    # Save summary to text file
    summary_path = os.path.join(output_dir, "summary_report.txt")
    with open(summary_path, "w") as f:
        for line in lines:
            f.write(line + "\n")
    logger.info(f"Summary saved to {summary_path}")

    # Save deltas to CSV
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

    delta_df = pd.DataFrame(deltas)
    csv_path = os.path.join(output_dir, "metric_deltas.csv")
    delta_df.to_csv(csv_path, index=False)
    logger.info(f"Delta CSV saved to {csv_path}")