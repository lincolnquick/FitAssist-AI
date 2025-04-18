"""
train_baseline_model.py

Trains a simple regression model using recent weight and 21-day rolling
net calorie trends to forecast future weight. Prioritizes recent weight
as a stronger predictor than caloric data.

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

def train_baseline_model(df: pd.DataFrame, window: int = 21):
    """
    Trains a baseline linear regression model to predict future weight trends
    based on recent weight and rolling net calorie averages.

    Args:
        df (pd.DataFrame): Cleaned health data including weight and calories.
        window (int): Rolling window size in days for net calorie trend.

    Returns:
        model (LinearRegression): Trained scikit-learn linear regression model.
    """
    df = df.sort_values("date").copy()

    # Calculate rolling net calories and weight average
    df["NetCalories"] = df["CaloriesIn"] - (df["BasalCaloriesBurned"] + df["ActiveCaloriesBurned"])
    df["NetCaloriesRolling"] = df["NetCalories"].rolling(window=window).mean()
    df["WeightRolling"] = df["Weight"].rolling(window=window).mean()
    df["RecentWeight"] = df["Weight"].shift(1)  # Use prior day's weight as current predictor

    # Build feature set
    features = df[["RecentWeight", "NetCaloriesRolling"]].dropna()
    target = df.loc[features.index, "WeightRolling"]

    # Final training set
    X = features
    y = target

    # Train model
    model = LinearRegression()
    model.fit(X, y)
    logger.info("Trained baseline regression model using RecentWeight and NetCaloriesRolling")

    return model

def predict_weight_trajectory(model, start_weight: float, net_calories_trend: float, days: list[int] = [30, 60, 90]) -> dict:
    """
    Predicts future weight based on recent weight and a constant net calorie trend.

    Args:
        model (LinearRegression): Trained regression model.
        start_weight (float): Most recent known weight (in kg).
        net_calories_trend (float): Recent average net calories.
        days (list[int]): Future day offsets to predict.

    Returns:
        dict: {day_offset: predicted_weight}
    """
    forecast = {}
    current_weight = start_weight

    for day in range(1, max(days) + 1):
        prediction_input = np.array([[current_weight, net_calories_trend]])
        predicted_weight = model.predict(prediction_input)[0]
        current_weight = predicted_weight  # Use prediction as next input

        if day in days:
            forecast[day] = predicted_weight

    return forecast