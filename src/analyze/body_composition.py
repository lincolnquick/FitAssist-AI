# src/analyze/body_composition.py

"""
body_composition.py

Analyzes changes in body composition over time using monthly differences
in smoothed weight, fat mass, and lean body mass. Visualizes the distribution
of mass change attributed to fat versus lean tissue.

This version uses 'Trend' metrics for more stable estimates.

Author: Lincoln Quick
"""

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from config.constants import KG_TO_LBS

logger = logging.getLogger(__name__)

def analyze_body_composition(df: pd.DataFrame, output_dir: str = "output") -> pd.DataFrame:
    """
    Analyze monthly changes in fat mass and lean mass, using smoothed metrics, and determine 
    the ratio of fat to lean tissue lost or gained.

    Args:
        df (pd.DataFrame): Cleaned metrics DataFrame with trend weight, body fat %, and lean mass
        output_dir (str): Folder to save outputs

    Returns:
        pd.DataFrame: Monthly summary of weight, fat mass, and lean mass changes
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Use smoothed values
    df["Weight"] = df["TrendWeight"]
    df["BodyFatPercentage"] = df["TrendBodyFatPercentage"]
    df["LeanBodyMass"] = df["TrendLeanBodyMass"]

    # Calculate fat mass using smoothed values
    df["FatMass"] = df["Weight"] * df["BodyFatPercentage"]
    df["LeanMass"] = df["LeanBodyMass"]

    # Resample monthly, using last value of each month
    monthly = df[["Weight", "FatMass", "LeanMass"]].resample("M").last()
    monthly_change = monthly.diff().dropna()

    # Compute percent contributions
    total_change = monthly_change["Weight"]
    fat_change = monthly_change["FatMass"]
    lean_change = monthly_change["LeanMass"]

    fat_ratio = fat_change / total_change
    lean_ratio = lean_change / total_change

    result = pd.DataFrame({
        "WeightChangeKg": total_change,
        "FatMassChangeKg": fat_change,
        "LeanMassChangeKg": lean_change,
        "FatMassChangeLb": fat_change * KG_TO_LBS,
        "LeanMassChangeLb": lean_change * KG_TO_LBS,
        "FatRatio": fat_ratio,
        "LeanRatio": lean_ratio
    })

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "composition_analysis.csv")
    result.to_csv(csv_path)
    logger.info(f"Saved composition analysis to {csv_path}")

    # Plot changes
    plt.figure(figsize=(10, 6))
    result[["FatMassChangeKg", "LeanMassChangeKg"]].plot(kind="bar", stacked=True, ax=plt.gca())
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Monthly Changes in Fat Mass and Lean Mass (kg)")
    plt.ylabel("Mass Change (kg)")
    plt.xlabel("Month")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join(output_dir, "composition_analysis.png")
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved body composition plot to {plot_path}")

    return result