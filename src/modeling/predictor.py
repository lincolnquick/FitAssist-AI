import pandas as pd
import numpy as np
import logging
from datetime import timedelta
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from src.config.constants import (
    MIN_DAYS_REQUIRED,
    MAX_MISSING_DAY_GAP,
    REQUIRED_COLUMNS,
    LBS_TO_KG,
    KG_TO_LBS
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def preprocess_for_modeling(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preprocessing data for modeling...")

    if df is None or df.empty:
        logger.error("DataFrame is empty or None.")
        return None

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return None

    if len(df) < MIN_DAYS_REQUIRED:
        logger.warning(f"Insufficient data: {len(df)} days (minimum required: {MIN_DAYS_REQUIRED}).")
        return None

    df = df.copy()
    df["DaysFromStart"] = (df["date"] - df["date"].min()).dt.days

    # Check for large gaps in data
    gaps = df["date"].diff().dt.days.fillna(1)
    if (gaps > MAX_MISSING_DAY_GAP).any():
        logger.warning("Detected large gaps in data. Model accuracy may be reduced.")

    return df


def train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Training linear regression model...")

    if df is None or df.empty:
        logger.error("Cannot train model: DataFrame is empty or None.")
        return None

    model = LinearRegression()
    X = df[["DaysFromStart"]]
    y = df["Weight"]

    model.fit(X, y)
    logger.info("Model training complete.")

    # Predict next 90 days
    last_day = df["DaysFromStart"].max()
    forecast_days = [30, 60, 90]
    future_days = [last_day + d for d in forecast_days]

    future_dates = [df["date"].max() + timedelta(days=d) for d in forecast_days]
    predictions = model.predict(np.array(future_days).reshape(-1, 1))

    prediction_df = pd.DataFrame({
        "Date": future_dates,
        "DaysFromToday": forecast_days,
        "PredictedWeightKg": predictions,
        "PredictedWeightLbs": predictions * KG_TO_LBS
    })

    return prediction_df


def plot_predictions(df: pd.DataFrame, prediction_df: pd.DataFrame):
    if df is None or df.empty or prediction_df is None:
        logger.error("Cannot plot predictions: missing or invalid data.")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["Weight"], label="Historical Weight", color="blue", marker="o", markersize=3)
    plt.plot(prediction_df["Date"], prediction_df["PredictedWeightKg"], label="Predicted Weight", color="red", linestyle="--", marker="x", markersize=5)

    plt.xlabel("Date")
    plt.ylabel("Weight (kg)")
    plt.title("Weight Forecast")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()