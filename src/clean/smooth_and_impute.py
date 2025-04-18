# src/clean/smooth_and_impute.py
"""
Applies interpolation and exponential smoothing to selected health metrics and adds them as new columns.
Original columns are left untouched. Excludes step count and walking distance, which are assumed to be
consistently tracked by the device.

This helps fill in missing data points and reduces daily noise from fluctuations.

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np

def smooth_and_impute(df: pd.DataFrame, span: int = 14) -> pd.DataFrame:
    """
    Applies interpolation for short gaps and exponential weighted smoothing to selected health metrics
    to estimate underlying trends. Smoothed values are added as new columns prefixed with 'Trend'.

    Args:
        df (pd.DataFrame): Cleaned DataFrame of daily health metrics with a 'date' column.
        span (int): Smoothing span and maximum interpolation gap (default is 14 days).

    Returns:
        pd.DataFrame: Modified DataFrame with new 'Trend' columns for smoothed metrics.
    """
    if "date" not in df.columns:
        raise ValueError("Input DataFrame must include a 'date' column.")

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").set_index("date")

    # Derived fields
    df["TDEE"] = df[["ActiveCaloriesBurned", "BasalCaloriesBurned"]].fillna(0).sum(axis=1)
    df["NetCalories"] = df["CaloriesIn"] - df["TDEE"]

    # Metrics to exclude from smoothing (assumed to be logged consistently)
    excluded_metrics = {"StepCount", "DistanceWalkingRunning"}

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target_metrics = [col for col in numeric_cols if col not in excluded_metrics]

    for col in target_metrics:
        interpolated = df[col].interpolate(method="time", limit=span, limit_direction="both")
        trend_col = f"Trend{col}"
        df[trend_col] = interpolated.ewm(span=span, adjust=False).mean()

    df.reset_index(inplace=True)
    return df