"""
predict_weight.py

FitAssist AI: Predictive modeling and weight forecasting module.

This script trains a regression model using recent Apple Health data (NetCalories and Weight),
accounts for metabolic adaptation, and generates future weight predictions over a defined time horizon.

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LinearRegression
from config.constants import MAX_MISSING_DAY_GAP

logger = logging.getLogger(__name__)

def train_model(df: pd.DataFrame, days_back: int = 90) -> LinearRegression:
    """
    Train a linear regression model on NetCalories vs Weight over the most recent N days.

    Args:
        df (pd.DataFrame): Cleaned metrics with 'date', 'Weight', 'NetCalories'.
        days_back (int): Number of days of data to consider.

    Returns:
        LinearRegression: Trained regression model.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    recent_df = df[df["date"] >= df["date"].max() - pd.Timedelta(days=days_back)]

    if recent_df.empty or len(recent_df) < 14:
        raise ValueError("Not enough recent data to train model.")

    X = recent_df[["NetCalories"]].values
    y = recent_df["Weight"].values
    model = LinearRegression().fit(X, y)

    logger.info("Trained weight prediction model.")
    logger.debug(f"Model coefficients: {model.coef_}, intercept: {model.intercept_}")
    return model

def simulate_adaptation(base_tdee: float, day: int, rate: float = 0.02) -> float:
    """
    Simulate metabolic adaptation by reducing TDEE over time.

    Args:
        base_tdee (float): Starting Total Daily Energy Expenditure (TDEE).
        day (int): Day into the forecast.
        rate (float): Weekly decay rate as a fraction (e.g., 0.02 = 2%).

    Returns:
        float: Adjusted TDEE for the given day.
    """
    weeks = day // 7
    return base_tdee * (1 - rate) ** weeks

def predict_weight_trajectory(model: LinearRegression, start_weight: float, start_tdee: float,
                              daily_intake: float, days: int = 90, adaptation_rate: float = 0.02) -> list:
    """
    Predict future weights with adaptation effects.

    Args:
        model (LinearRegression): Trained weight predictor.
        start_weight (float): Most recent weight in kg.
        start_tdee (float): Estimated current TDEE in kcal.
        daily_intake (float): User's average daily caloric intake.
        days (int): Number of forecast days.
        adaptation_rate (float): Weekly TDEE adaptation rate.

    Returns:
        list of float: Forecasted weights for each day.
    """
    weights = [start_weight]
    for day in range(1, days + 1):
        adjusted_tdee = simulate_adaptation(start_tdee, day, adaptation_rate)
        net_cals = daily_intake - adjusted_tdee
        weight_change = model.predict([[net_cals]])[0]
        weights.append(weight_change)
    return weights