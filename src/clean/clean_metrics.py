"""
Clean and interpolate Apple Health metrics.

This module takes a dictionary of health metrics (date: {metric: value})
and performs the following:
- Converts to a pandas DataFrame and sorts by date
- Drops rows where 'CaloriesIn' is missing
- Interpolates missing values for Weight, LeanBodyMass, and BodyFatPercentage
  with a maximum gap limit defined in config
- Computes derived metrics:
    - TDEE = ActiveCaloriesBurned + BasalCaloriesBurned
    - NetCalories = CaloriesIn - TDEE

Used as part of the FitAssist AI preprocessing pipeline.
"""

import pandas as pd
import logging
from config.constants import MAX_MISSING_DAY_GAP

logger = logging.getLogger(__name__)

def clean_metrics(metrics: dict) -> pd.DataFrame:
    """
    Cleans and processes parsed health metrics.

    Args:
        metrics (dict): Dictionary of daily health metrics {date: {metric: value}}

    Returns:
        pd.DataFrame: Cleaned and processed DataFrame with interpolated values and derived columns
    """
    if not metrics:
        logger.warning("No metrics provided to clean.")
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(metrics, orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    logger.info(f"Initial metrics shape: {df.shape}")

    # Drop rows without CaloriesIn (can't model energy balance)
    df = df.dropna(subset=["CaloriesIn"])
    logger.info(f"Rows remaining after dropping missing CaloriesIn: {len(df)}")

    # Interpolate weight-related measurements with logging
    for col in ["Weight", "LeanBodyMass", "BodyFatPercentage"]:
        if col in df.columns:
            missing_before = df[col].isna().sum()
            df[col] = df[col].interpolate(method="time", limit=MAX_MISSING_DAY_GAP, limit_direction="both")
            missing_after = df[col].isna().sum()
            interpolated = missing_before - missing_after
            if interpolated > 0:
                logger.info(f"Interpolated {interpolated} values for {col} (max gap: {MAX_MISSING_DAY_GAP} days)")

    # Derived metrics
    df["TDEE"] = df[["ActiveCaloriesBurned", "BasalCaloriesBurned"]].fillna(0).sum(axis=1)
    df["NetCalories"] = df["CaloriesIn"] - df["TDEE"]

    logger.info(f"Final cleaned metrics shape: {df.shape}")
    return df