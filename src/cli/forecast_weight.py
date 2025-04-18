"""
forecast_weight.py

CLI script for generating a 30/60/90-day weight forecast using cleaned health metrics.

Author: Lincoln Quick
"""

import sys
import logging
import pandas as pd
from src.modeling.predict_weight import train_model, predict_weight_trajectory
from src.visualize.plot_forecast import plot_forecast  
from config.constants import MAX_MISSING_DAY_GAP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def forecast_weight():
    try:
        # Load cleaned data
        data_path = sys.argv[1] if len(sys.argv) > 1 else "output/cleaned_metrics.csv"
        df = pd.read_csv(data_path, parse_dates=["date"])
        logger.info(f"Loaded cleaned metrics from: {data_path}")

        # Train model on recent data
        model = train_model(df, days_back=90)

        # Estimate starting point
        latest = df.sort_values("date").iloc[-1]
        start_weight = latest["Weight"]
        start_tdee = latest["BasalCaloriesBurned"] + latest["ActiveCaloriesBurned"]
        avg_intake = df["CaloriesIn"].tail(30).mean()

        logger.info("--- Weight Forecast Summary ---")
        logger.info(f"Starting weight: {start_weight:.1f} kg")
        logger.info(f"Estimated TDEE: {start_tdee:.0f} kcal/day")
        logger.info(f"Average intake: {avg_intake:.0f} kcal/day")

        # Run predictions
        forecast = predict_weight_trajectory(model, start_weight, start_tdee, avg_intake)

        for days in [30, 60, 90]:
            predicted_weight = forecast[days]
            logger.info(f"Predicted weight in {days} days: {predicted_weight:.1f} kg")
        
        # Convert dict to DataFrame for plotting
        forecast_df = pd.DataFrame([
            {"DaysFromToday": days, "PredictedWeightKg": kg, "PredictedWeightLbs": kg * 2.20462}
            for days, kg in forecast.items()
        ])
        forecast_df["date"] = pd.to_datetime(df["date"].max()) + pd.to_timedelta(forecast_df["DaysFromToday"], unit="D")

        plot_forecast(forecast_df)

    except Exception as e:
        logger.error(f"Forecasting failed: {e}")

if __name__ == "__main__":
    forecast_weight()