"""
caloric_efficiency.py

Analyzes how many calories are required to produce one pound of weight change
using rolling and monthly aggregation, based on smoothed "Trend" metrics.

Outputs:
- CSVs with rolling and monthly efficiency calculations
- Line plot showing caloric efficiency trends

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
from config.constants import KG_TO_LBS

logger = logging.getLogger(__name__)

def analyze_efficiency(df: pd.DataFrame, output_dir: str = "output") -> dict:
    """
    Analyze how many calories are required per pound of body weight change over time.

    Uses smoothed trend metrics for Weight and NetCalories.

    Args:
        df (pd.DataFrame): Cleaned health metrics DataFrame including trend metrics.
        output_dir (str): Directory where output files will be saved.

    Returns:
        dict: {
            "avg_cal_per_lb": float,
            "efficiency_df": pd.DataFrame (7-day rolling analysis),
            "monthly_summary": pd.DataFrame (monthly efficiency)
        }
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")

    # Use trend metrics
    if "TrendWeight" not in df or "TrendNetCalories" not in df:
        raise ValueError("Required trend columns ('TrendWeight', 'TrendNetCalories') not found in data.")

    df["WeightDelta"] = df["TrendWeight"].diff()

    # === Rolling 7-Day Analysis ===
    window = 7
    roll = df[["TrendWeight", "TrendNetCalories"]].rolling(f"{window}D", min_periods=window)

    rolling_weight_lbs = roll["TrendWeight"].apply(lambda x: (x.iloc[-1] - x.iloc[0]) * KG_TO_LBS)
    rolling_calories = roll["TrendNetCalories"].sum()
    calories_per_pound = rolling_calories / rolling_weight_lbs.replace(0, np.nan)
    calories_per_pound = calories_per_pound.replace([np.inf, -np.inf], np.nan)

    efficiency_df = pd.DataFrame({
        "CaloriesPerPound": calories_per_pound,
        "RollingNetCalories": rolling_calories,
        "WeightChangeLbs": rolling_weight_lbs
    })

    efficiency_df = efficiency_df[(efficiency_df["CaloriesPerPound"].abs() < 10000) & 
                                  (efficiency_df["CaloriesPerPound"].abs() > 500)]

    os.makedirs(output_dir, exist_ok=True)
    efficiency_path = os.path.join(output_dir, "caloric_efficiency.csv")
    efficiency_df.to_csv(efficiency_path)
    logger.info(f"Saved caloric efficiency analysis to {efficiency_path}")

    # === Plot rolling efficiency ===
    plt.figure(figsize=(10, 5))
    plt.plot(efficiency_df.index, efficiency_df["CaloriesPerPound"], label="Calories per Pound", color="tab:blue")
    plt.axhline(y=3500, linestyle="--", color="gray", label="Theoretical Avg (3500 kcal/lb)")
    plt.title("Caloric Efficiency Over Time (7-Day Rolling)")
    plt.xlabel("Date")
    plt.ylabel("Calories per Pound")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plot_path = os.path.join(output_dir, "caloric_efficiency.png")
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved efficiency plot to {plot_path}")

    # === Monthly Efficiency Summary ===
    monthly = df.resample("M").agg({
        "TrendNetCalories": "sum",
        "TrendWeight": ["first", "last"]
    })
    monthly.columns = ["NetCalories", "StartWeight", "EndWeight"]
    monthly["WeightDeltaLbs"] = (monthly["EndWeight"] - monthly["StartWeight"]) * KG_TO_LBS
    monthly["CaloriesPerPound"] = monthly["NetCalories"] / monthly["WeightDeltaLbs"].replace(0, np.nan)
    monthly = monthly[monthly["CaloriesPerPound"].abs().between(500, 20000)]

    monthly_path = os.path.join(output_dir, "monthly_efficiency.csv")
    monthly.to_csv(monthly_path)
    logger.info(f"Saved monthly caloric efficiency to {monthly_path}")

    avg_cal = efficiency_df["CaloriesPerPound"].mean()
    logger.info(f"Estimated average calories per pound lost: {avg_cal:.1f} kcal/lb")

    return {
        "avg_cal_per_lb": avg_cal,
        "efficiency_df": efficiency_df,
        "monthly_summary": monthly
    }