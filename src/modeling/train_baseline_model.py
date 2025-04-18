# src/modeling/train_baseline_model.py

"""
train_baseline_model.py

Trains a model to predict future weight change (delta) over a rolling window,
using smoothed calorie-related features and recent trend weight. This version
uses exponential smoothing ("Trend" columns) to reduce the impact of day-to-day noise.

Author: Lincoln Quick
"""

import pandas as pd
from xgboost import XGBRegressor
import logging

logger = logging.getLogger(__name__)

def train_weight_delta_model(df: pd.DataFrame, window: int = 21):
    """
    Trains a regression model to predict weight delta over time using trend features.

    Args:
        df (pd.DataFrame): Cleaned and smoothed health metrics DataFrame.
        window (int): Rolling window size to compute deltas and averages.

    Returns:
        model (XGBRegressor): Trained model.
        window (int): Window size used (needed for scaling delta).
    """
    df = df.copy()
    df = df.sort_values("date")

    # Ensure required trend columns exist
    required = [
        "TrendWeight", "TrendCaloriesIn", "TrendBasalCaloriesBurned", 
        "TrendActiveCaloriesBurned", "TrendNetCalories"
    ]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required trend metric: {col}")

    # Feature engineering using trend metrics
    df["NetCaloriesRolling"] = df["TrendNetCalories"].rolling(window=window).mean()
    df["CaloriesInRolling"] = df["TrendCaloriesIn"].rolling(window=window).mean()
    df["BasalRolling"] = df["TrendBasalCaloriesBurned"].rolling(window=window).mean()
    df["ActiveRolling"] = df["TrendActiveCaloriesBurned"].rolling(window=window).mean()
    df["RecentWeight"] = df["TrendWeight"].shift(1)
    df["WeightDelta"] = df["TrendWeight"].diff(periods=window)

    # Select input features and target
    features = df[[
        "RecentWeight", "NetCaloriesRolling",
        "CaloriesInRolling", "BasalRolling", "ActiveRolling"
    ]]
    target = df["WeightDelta"]

    # Drop incomplete rows
    valid = features.notnull().all(axis=1) & target.notnull()
    X = features[valid]
    y = target[valid]

    logger.info(f"Training set size: {len(X)} rows")
    logger.info(f"Features: {X.columns.tolist()}")
    logger.info(f"Target: WeightDelta over {window} days")

    model = XGBRegressor()
    model.fit(X, y)

    logger.info("Trained XGBoost regression model for weight delta prediction.")

    return model, window