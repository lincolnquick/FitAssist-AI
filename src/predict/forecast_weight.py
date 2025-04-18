# src/predict/forecast_weight.py

"""
forecast_weight.py

Forecasts future weight by predicting weight deltas using a trained model
based on trend-smoothed metrics.

Author: Lincoln Quick
"""

import logging
from data.load_data import load_cleaned_metrics
from src.modeling.train_baseline_model import train_weight_delta_model

logger = logging.getLogger(__name__)

def forecast_from_cleaned_csv(
    path: str = "output/cleaned_metrics.csv",
    days_list: list[int] = [7, 14, 30, 60, 90, 120, 150, 180]
) -> dict:
    """
    Loads cleaned trend-smoothed metrics, trains a delta model, and generates a weight forecast.

    Args:
        path (str): Path to the cleaned metrics CSV.
        days_list (list[int]): List of future day intervals to forecast.

    Returns:
        dict: {day_offset: predicted_weight}
    """
    logger.info("Forecasting weight trajectory...")
    df = load_cleaned_metrics(path)

    # Train model using trend features
    model, window = train_weight_delta_model(df)

    # Most recent values
    df = df.sort_values("date")
    latest = df.iloc[-1]

    required_trend_columns = [
        "TrendWeight", "TrendNetCalories",
        "TrendCaloriesIn", "TrendBasalCaloriesBurned", "TrendActiveCaloriesBurned"
    ]
    for col in required_trend_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required trend column: {col}")

    recent_values = {
        "RecentWeight": latest["TrendWeight"],
        "NetCaloriesRolling": df["TrendNetCalories"].rolling(window).mean().iloc[-1],
        "CaloriesInRolling": df["TrendCaloriesIn"].rolling(window).mean().iloc[-1],
        "BasalRolling": df["TrendBasalCaloriesBurned"].rolling(window).mean().iloc[-1],
        "ActiveRolling": df["TrendActiveCaloriesBurned"].rolling(window).mean().iloc[-1],
    }

    current_weight = latest["TrendWeight"]
    logger.info(f"Starting weight: {current_weight:.2f} kg")
    logger.info(f"Recent net calorie trend: {recent_values['NetCaloriesRolling']:.0f} kcal/day")

    forecast = {}
    for days in days_list:
        # Scale predicted delta from model window to the requested future range
        predicted_delta = model.predict([list(recent_values.values())])[0]
        scaled_delta = predicted_delta * (days / window)
        forecast[days] = current_weight + scaled_delta

    logger.info("\n--- Weight Forecast ---")
    for days, weight in forecast.items():
        logger.info(f"{days} days: {weight:.2f} kg")

    return forecast