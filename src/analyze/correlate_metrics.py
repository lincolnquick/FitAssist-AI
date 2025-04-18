# src/analyze/correlate_metrics.py

"""
correlate_metrics.py

Analyzes correlations between health and lifestyle metrics to evaluate:
- Calorie balance and weight change
- Fat vs. lean mass loss
- Behavior-driven trends (e.g., activity vs intake)
- Metabolic adaptation indicators

Outputs:
- Console summary with interpretation
- Text report
- CSV file of correlations

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def interpret_correlation(r: float) -> str:
    """Provides a descriptive interpretation of the correlation coefficient."""
    if pd.isna(r):
        return "insufficient data"
    abs_r = abs(r)
    if abs_r >= 0.9:
        strength = "very strong"
    elif abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.5:
        strength = "moderate"
    elif abs_r >= 0.3:
        strength = "weak"
    elif abs_r >= 0.1:
        strength = "very weak"
    else:
        strength = "negligible"
    direction = "positive" if r > 0 else "negative" if r < 0 else "no"
    return f"{strength} {direction} correlation"

def correlate_metrics(df: pd.DataFrame, output_dir: str = "output") -> None:
    """
    Analyzes and reports correlations between health metrics.

    Args:
        df (pd.DataFrame): Cleaned health data.
        output_dir (str): Directory to save correlation outputs.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Derived metrics
    df = df.copy()
    df["FatMass"] = df["Weight"] * df["BodyFatPercentage"]
    df["LeanMass"] = df["LeanBodyMass"]
    df["TDEE"] = df["BasalCaloriesBurned"] + df["ActiveCaloriesBurned"]
    df["NetCalories"] = df["CaloriesIn"] - df["TDEE"]
    df["WeightDelta"] = df["Weight"].diff()
    df["FatMassDelta"] = df["FatMass"].diff()
    df["LeanMassDelta"] = df["LeanMass"].diff()
    df["NetCalDelta"] = df["NetCalories"].diff()

    correlation_sets = {
        "Energy Balance": [
            ("NetCalories", "WeightDelta"),
            ("CaloriesIn", "TDEE"),
            ("TDEE", "WeightDelta"),
        ],
        "Body Composition": [
            ("Weight", "FatMass"),
            ("Weight", "LeanMass"),
            ("FatMass", "LeanMass"),
        ],
        "Activity & Behavior": [
            ("StepCount", "ActiveCaloriesBurned"),
            ("DistanceWalkingRunning", "ActiveCaloriesBurned"),
            ("StepCount", "NetCalories"),
            ("CaloriesIn", "StepCount"),
            ("CaloriesIn", "ActiveCaloriesBurned"),
        ],
        "Change-on-Change": [
            ("WeightDelta", "NetCalDelta"),
            ("FatMassDelta", "NetCalDelta"),
            ("LeanMassDelta", "NetCalDelta"),
        ]
    }

    report_lines = ["=== Correlation Report ===\n"]
    correlations = []

    for section, pairs in correlation_sets.items():
        report_lines.append(f"\n--- {section} ---")
        for x, y in pairs:
            if x in df.columns and y in df.columns:
                valid_df = df[[x, y]].dropna()
                if len(valid_df) > 2:
                    r = valid_df[x].corr(valid_df[y])
                    interpretation = interpret_correlation(r)
                    report_lines.append(f"{x} vs {y}: r = {r:.3f} ({interpretation})")
                    correlations.append({
                        "Metric1": x,
                        "Metric2": y,
                        "Correlation": r,
                        "Interpretation": interpretation,
                        "Category": section
                    })
                else:
                    report_lines.append(f"{x} vs {y}: insufficient data")

    # Output summary
    summary_path = os.path.join(output_dir, "correlation_report.txt")
    with open(summary_path, "w") as f:
        for line in report_lines:
            print(line)
            f.write(line + "\n")
    logger.info(f"Correlation summary saved to {summary_path}")

    # Output CSV
    df_corr = pd.DataFrame(correlations)
    csv_path = os.path.join(output_dir, "correlation_summary.csv")
    df_corr.to_csv(csv_path, index=False)
    logger.info(f"Correlation CSV saved to {csv_path}")