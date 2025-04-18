# src/analyze/describe_data.py

"""
describe_data.py

Analyzes cleaned health metrics and provides a summary report. This includes:
- Latest metric values
- Daily, weekly, and monthly deltas
- 90-day rolling statistics
- Console output with color formatting
- Saves text and CSV reports to output/

Author: Lincoln Quick
"""

import os
import logging
import pandas as pd
from colorama import Fore, Style, init

init(autoreset=True)
logger = logging.getLogger(__name__)

def describe_data(df: pd.DataFrame, output_dir: str = "output") -> None:
    """
    Analyze the cleaned metrics and output a summary report.

    Args:
        df (pd.DataFrame): Cleaned health data with datetime-indexed rows.
        output_dir (str): Path to store summary report and delta CSV.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    latest = df.iloc[-1]
    daily = df.diff().tail(1)
    weekly = df.diff(periods=7).tail(1)
    monthly = df.resample("ME").last().diff().tail(1)
    last_90 = df.tail(90)

    # Prepare summary
    lines = []
    def add_line(label, value, color=Fore.WHITE):
        line = f"{color}{label:<35}: {value}{Style.RESET_ALL}"
        print(line)
        lines.append(f"{label:<35}: {value}")

    print(Fore.CYAN + "\n--- Metric Summary ---\n" + Style.RESET_ALL)
    add_line("Latest Weight", f"{latest.get('Weight', 'N/A'):.2f}")
    add_line("Latest BodyFatPercentage", f"{latest.get('BodyFatPercentage', 'N/A'):.2f}")
    add_line("Latest LeanBodyMass", f"{latest.get('LeanBodyMass', 'N/A'):.2f}")
    add_line("Latest CaloriesIn", f"{latest.get('CaloriesIn', 'N/A'):.2f}")
    add_line("Latest BasalCaloriesBurned", f"{latest.get('BasalCaloriesBurned', 'N/A'):.2f}")
    add_line("Latest ActiveCaloriesBurned", f"{latest.get('ActiveCaloriesBurned', 'N/A'):.2f}")

    print(Fore.YELLOW + "\n--- Delta Summary ---\n" + Style.RESET_ALL)
    for metric in ["Weight", "BodyFatPercentage", "LeanBodyMass"]:
        add_line(f"{metric} change (1d)", f"{daily[metric].values[0]:.2f}", Fore.YELLOW)
        add_line(f"{metric} change (7d)", f"{weekly[metric].values[0]:.2f}", Fore.YELLOW)
        add_line(f"{metric} change (monthly)", f"{monthly[metric].values[0]:.2f}", Fore.YELLOW)

    print(Fore.GREEN + "\n--- 90-Day Statistics ---\n" + Style.RESET_ALL)
    for metric in ["Weight", "LeanBodyMass", "CaloriesIn", "NetCalories", "TDEE"]:
        if metric in last_90.columns:
            add_line(f"{metric} mean (90d)", f"{last_90[metric].mean():.2f}", Fore.GREEN)
            add_line(f"{metric} std dev (90d)", f"{last_90[metric].std():.2f}", Fore.GREEN)
            add_line(f"{metric} min (90d)", f"{last_90[metric].min():.2f}", Fore.GREEN)
            add_line(f"{metric} max (90d)", f"{last_90[metric].max():.2f}", Fore.GREEN)

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