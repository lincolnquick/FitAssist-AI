# src/predict/forecast_weight.py

"""
forecast_weight.py

Forecasts future weight by predicting weight deltas using a trained model.

Author: Lincoln Quick
"""

import logging
from data.load_data import load_cleaned_metrics
from src.modeling.train_baseline_model import train_weight_delta_model

logger = logging.getLogger(__name__)

def forecast_from_cleaned_csv(path: str = "output/cleaned_metrics.csv"):
    """
    Loads cleaned metrics, trains a delta model, and generates a weight forecast.
    """
    logger.info("Forecasting weight trajectory...")
    df = load_cleaned_metrics(path)

    model, window = train_weight_delta_model(df)

    # Most recent values
    latest = df.sort_values("date").iloc[-1]
    recent_values = {
        "RecentWeight": latest["Weight"],
        "NetCaloriesRolling": df["NetCalories"].rolling(window).mean().iloc[-1],
        "CaloriesInRolling": df["CaloriesIn"].rolling(window).mean().iloc[-1],
        "BasalRolling": df["BasalCaloriesBurned"].rolling(window).mean().iloc[-1],
        "ActiveRolling": df["ActiveCaloriesBurned"].rolling(window).mean().iloc[-1],
    }

    current_weight = latest["Weight"]
    logger.info(f"Starting weight: {current_weight:.2f} kg")
    logger.info(f"Recent net calorie trend: {recent_values['NetCaloriesRolling']:.0f} kcal/day")

    forecast = {}
    for days in [30, 60, 90]:
        # Scale the predicted delta from model’s window size to requested days
        predicted_delta = model.predict([list(recent_values.values())])[0] * (days / window)
        forecast[days] = current_weight + predicted_delta

    logger.info("\n--- Weight Forecast ---")
    for days, weight in forecast.items():
        logger.info(f"{days} days: {weight:.2f} kg")

    return forecast