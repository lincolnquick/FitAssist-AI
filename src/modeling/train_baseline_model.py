# src/predict/train_baseline_model.py

"""
train_baseline_model.py

Trains a model to predict future weight change (delta) over a rolling window,
using calorie-related features and recent weight.

Note: appears to be overestimating weight change. 

Author: Lincoln Quick
"""

import pandas as pd
from xgboost import XGBRegressor
import logging

logger = logging.getLogger(__name__)

def train_weight_delta_model(df: pd.DataFrame, window: int = 21):
    """
    Trains a regression model to predict weight delta over time.

    Args:
        df (pd.DataFrame): Cleaned health metrics DataFrame.
        window (int): Rolling window size to compute deltas and averages.

    Returns:
        model (XGBRegressor): Trained model.
        window (int): Window size used (needed for scaling delta).
    """
    df = df.sort_values("date").copy()

    # Derived metrics
    df["NetCalories"] = df["CaloriesIn"] - (df["BasalCaloriesBurned"] + df["ActiveCaloriesBurned"])
    df["NetCaloriesRolling"] = df["NetCalories"].rolling(window=window).mean()
    df["CaloriesInRolling"] = df["CaloriesIn"].rolling(window=window).mean()
    df["BasalRolling"] = df["BasalCaloriesBurned"].rolling(window=window).mean()
    df["ActiveRolling"] = df["ActiveCaloriesBurned"].rolling(window=window).mean()
    df["RecentWeight"] = df["Weight"].shift(1)
    df["WeightDelta"] = df["Weight"].diff(periods=window)

    features = df[["RecentWeight", "NetCaloriesRolling", "CaloriesInRolling", "BasalRolling", "ActiveRolling"]]
    target = df["WeightDelta"]

    valid = features.notnull().all(axis=1) & target.notnull()
    X = features[valid]
    y = target[valid]

    logger.debug(f"Training set size: {len(X)} rows")
    logger.debug(f"Features: {X.columns.tolist()}")
    logger.debug(f"Target: WeightDelta over {window} days")

    model = XGBRegressor()
    model.fit(X, y)

    return model, window