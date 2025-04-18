import pandas as pd
import numpy as np
import logging
from datetime import timedelta
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from config.constants import (
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
    # Ensure 'date' column is datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop any rows where date conversion failed
    df = df.dropna(subset=["date"])

    df["DaysFromStart"] = (df["date"] - df["date"].min()).dt.days

    # Check for large gaps in data
    gaps = df["date"].diff().dt.days.fillna(1)
    if (gaps > MAX_MISSING_DAY_GAP).any():
        logger.warning("Detected large gaps in data. Model accuracy may be reduced.")

    return df


def train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trains a linear regression model to predict weight based on time (DaysFromStart),
    emphasizing more recent data using sample weights.
    Returns predictions for 30, 60, and 90 days into the future.
    """
    if df.empty:
        logger.error("Cannot train model: DataFrame is empty or None.")
        return None

    logger.info("Training linear regression model...")

    # Copy and prepare data
    df = df.copy()
    df["DaysFromStart"] = (df["date"] - df["date"].min()).dt.days
    df = df.dropna(subset=["Weight", "DaysFromStart"])

    # Emphasize more recent data using sample weights
    max_day = df["DaysFromStart"].max()
    df["SampleWeight"] = df["DaysFromStart"] / max_day  # Newer data gets higher weight

    X = df[["DaysFromStart"]]
    y = df["Weight"]
    weights = df["SampleWeight"]

    model = LinearRegression()
    model.fit(X, y, sample_weight=weights)
    logger.info("Model training complete.")

    # Predict for 30, 60, 90 days into the future
    last_day = df["DaysFromStart"].max()
    future_days = [30, 60, 90]
    future_days_absolute = [last_day + d for d in future_days]
    X_future = pd.DataFrame(future_days_absolute, columns=["DaysFromStart"])
    predictions = model.predict(X_future)

    # Create prediction DataFrame
    prediction_df = pd.DataFrame({
        "DaysFromToday": future_days,
        "PredictedWeightKg": predictions,
    })
    prediction_df["PredictedWeightLbs"] = prediction_df["PredictedWeightKg"] * KG_TO_LBS

    # Estimate future dates
    prediction_df["date"] = df["date"].max() + pd.to_timedelta(prediction_df["DaysFromToday"], unit="D")

    return prediction_df


def plot_predictions(df: pd.DataFrame, prediction_df: pd.DataFrame):
    if df is None or df.empty or prediction_df is None or prediction_df.empty:
        logger.error("Cannot plot predictions: missing or invalid data.")
        return

    # Rename any column that looks like a date column
    for col in df.columns:
        if col.lower() == "date":
            df.rename(columns={col: "date"}, inplace=True)
            break
    for col in prediction_df.columns:
        if col.lower() == "date":
            prediction_df.rename(columns={col: "date"}, inplace=True)
            break

    print("Plotting with columns:")
    print("df:", df.columns.tolist())
    print("prediction_df:", prediction_df.columns.tolist())

    plt.figure(figsize=(10, 6))
    plt.plot(df["date"], df["Weight"], label="Historical Weight", color="blue", marker="o", markersize=3)
    plt.plot(prediction_df["date"], prediction_df["PredictedWeightKg"], label="Predicted Weight", color="red", linestyle="--", marker="x", markersize=5)

    plt.xlabel("Date")
    plt.ylabel("Weight (kg)")
    plt.title("Weight Forecast")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()