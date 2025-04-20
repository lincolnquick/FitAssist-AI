# src/clean/smooth_and_impute.py
"""
Interpolates and smooths health metrics, then calculates derived fields:
- Trend* metrics use interpolation + exponential smoothing (except CaloriesIn)
- Lean body mass is recalculated from TrendWeight and TrendBodyFatPercentage
- TDEE, RMR, PA, and EnergyBalance are derived from physiological models
- No smoothing is applied to derived values

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.tools.energy import (
    calculate_rmr,
    calculate_age,
    estimate_caloric_imbalance
)

def smooth_and_impute(df: pd.DataFrame, user_info: dict = None, span: int = 14) -> pd.DataFrame:
    """
    Apply smoothing and derive physiological metrics.

    Args:
        df (pd.DataFrame): DataFrame with 'date' and health metrics (mass in kg).
        user_info (dict): {"dob": "YYYY-MM-DD", "sex": "male" or "female", "height_cm": float}.
        span (int): Rolling window size for deltas and smoothing (default = 14 days).

    Returns:
        pd.DataFrame: Updated DataFrame with Trend and derived columns.
    """
    if "date" not in df.columns:
        raise ValueError("Input DataFrame must include a 'date' column.")
    
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").set_index("date")

    # Extract user info with defaults
    dob = pd.to_datetime(user_info.get("dob", "1990-01-01")) if user_info else datetime(1990, 1, 1)
    sex = user_info.get("sex", "male") if user_info else "male"

    # Exclude these from smoothing
    excluded_metrics = {"StepCount", "DistanceWalkingRunning", "EnergyBalance", "TDEE", "RMR", "PA"}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target_metrics = [col for col in numeric_cols if col not in excluded_metrics]

    # Interpolation and smoothing
    for col in target_metrics:
        interpolated = df[col].interpolate(method="time", limit=span, limit_direction="both")
        if col == "CaloriesIn":
            df["TrendCaloriesIn"] = interpolated
        else:
            df[f"Trend{col}"] = interpolated.ewm(span=span, adjust=False).mean()

    # Derived: Lean body mass from weight and body fat %
    if "TrendWeight" in df.columns and "TrendBodyFatPercentage" in df.columns:
        df["TrendLeanBodyMass"] = (1 - df["TrendBodyFatPercentage"]) * df["TrendWeight"]

    # ΔWeight over time
    df["ΔWeight"] = df["TrendWeight"].diff(periods=span)

    # If lean mass present, use FM/FFM split for energy balance
    if "TrendLeanBodyMass" in df.columns:
        df["ΔLean"] = df["TrendLeanBodyMass"].diff(periods=span)
        df["ΔFat"] = df["ΔWeight"] - df["ΔLean"]
        df["EnergyBalance"] = df.apply(
            lambda row: estimate_caloric_imbalance(row["ΔFat"], row["ΔLean"])
            if pd.notna(row["ΔFat"]) and pd.notna(row["ΔLean"]) else np.nan,
            axis=1
        )
    else:
        df["EnergyBalance"] = df["ΔWeight"].apply(
            lambda dw: estimate_caloric_imbalance(dw * 0.85, dw * 0.15) if pd.notna(dw) else np.nan
        )

    # TDEE = Intake - EnergyBalance
    df["TDEE"] = df["TrendCaloriesIn"] - df["EnergyBalance"]

    # Age and RMR
    df["Age"] = df.index.to_series().apply(lambda d: calculate_age(dob, d))
    df["RMR"] = df.apply(
        lambda row: calculate_rmr(row["TrendWeight"], row["Age"], sex)
        if pd.notna(row["TrendWeight"]) else np.nan,
        axis=1
    )

    # PA = TDEE - RMR, clipped to ≥0
    df["PA"] = (df["TDEE"] - df["RMR"]).clip(lower=0)

    df.reset_index(inplace=True)
    return df