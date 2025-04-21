# src/clean/smooth_and_impute.py
"""
Interpolates and smooths health metrics, then calculates derived fields:
- Trend* metrics use interpolation + exponential smoothing (except CaloriesIn)
- Lean body mass is recalculated from TrendWeight and TrendBodyFatPercentage
- ΔWeight is calculated daily and smoothed over a centered 7-day window
- TDEE, RMR, PA, and EnergyBalance are derived from physiological models
- No smoothing is applied to derived values except SmoothedΔWeight
- RMR uses Livingston-Kohlstadt formula
- PA = TDEE - RMR (clipped to ≥ 0)

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
    if "date" not in df.columns:
        raise ValueError("Input DataFrame must include a 'date' column.")
    
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").set_index("date")

    dob = pd.to_datetime(user_info.get("dob", "1990-01-01")) if user_info else datetime(1990, 1, 1)
    sex = user_info.get("sex", "male") if user_info else "male"

    # Interpolate & Smooth
    excluded_metrics = {"StepCount", "DistanceWalkingRunning", "EnergyBalance", "TDEE", "RMR", "PA"}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target_metrics = [col for col in numeric_cols if col not in excluded_metrics]

    for col in target_metrics:
        interpolated = df[col].interpolate(method="time", limit=span, limit_direction="both")
        if col == "CaloriesIn":
            df["TrendCaloriesIn"] = interpolated
        elif col == "Weight":
            # Use centered 2-sided smoothing for Weight
            interpolated = df["Weight"].interpolate(method="time", limit=span, limit_direction="both")
            df["TrendWeight"] = interpolated.rolling(window=21, center=True, min_periods=7).mean()
        else:
            df[f"Trend{col}"] = interpolated.ewm(span=span, adjust=False).mean()

    # Derived: Lean body mass
    if "TrendWeight" in df.columns and "TrendBodyFatPercentage" in df.columns:
        df["TrendLeanBodyMass"] = (1 - df["TrendBodyFatPercentage"]) * df["TrendWeight"]

    # Daily ΔWeight using TrendWeight
    df["ΔWeight"] = df["TrendWeight"].diff(periods=1)

    # Smoothed ΔWeight using centered 7-day window (for stability in EnergyBalance)
    df["SmoothedDailyΔWeight"] = df["ΔWeight"].rolling(window=7, center=True, min_periods=1).mean()

    # ΔLean from TrendLeanBodyMass
    if "TrendLeanBodyMass" in df.columns:
        df["ΔLean"] = df["TrendLeanBodyMass"].diff(periods=1)
        df["SmoothedDailyΔLean"] = df["ΔLean"].rolling(window=7, center=True, min_periods=1).mean()
        df["SmoothedDailyΔFat"] = df["SmoothedDailyΔWeight"] - df["SmoothedDailyΔLean"]
        
        # Use smoothed fat/lean deltas
        df["EnergyBalance"] = df.apply(
            lambda row: estimate_caloric_imbalance(row["SmoothedDailyΔFat"], row["SmoothedDailyΔLean"])
            if pd.notna(row["SmoothedDailyΔFat"]) and pd.notna(row["SmoothedDailyΔLean"]) else np.nan,
            axis=1
        )
    else:
        df["EnergyBalance"] = df["SmoothedDailyΔWeight"].apply(
            lambda dw: estimate_caloric_imbalance(dw * 0.85, dw * 0.15) if pd.notna(dw) else np.nan
        )

    # Age and RMR
    df["Age"] = df.index.to_series().apply(lambda d: calculate_age(dob, d))
    df["RMR"] = df.apply(
        lambda row: calculate_rmr(row["TrendWeight"], row["Age"], sex)
        if pd.notna(row["TrendWeight"]) else np.nan,
        axis=1
    )

    # TDEE = max(CaloriesIn - EnergyBalance, RMR)
    df["TDEE_raw"] = df["TrendCaloriesIn"] - df["EnergyBalance"]
    df["TDEE"] = df[["TDEE_raw", "RMR"]].apply(lambda row: max(row["TDEE_raw"], row["RMR"] + 1e-3), axis=1)

    # PA = TDEE - RMR, clipped to small positive value
    df["PA"] = (df["TDEE"] - df["RMR"]).clip(lower=1e-3)

    df.reset_index(inplace=True)
    return df