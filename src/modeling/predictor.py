import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from sklearn.linear_model import LinearRegression
from typing import Tuple, Optional
from config import safety_config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def preprocess_for_modeling(df: pd.DataFrame, interpolate_missing: bool = True) -> Optional[pd.DataFrame]:
    logging.info("Preprocessing data for modeling...")

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')

    required_cols = ['date', 'Weight', 'CaloriesIn', 'CaloriesOut']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        return None

    df = df[required_cols]

    if interpolate_missing:
        df[['Weight', 'CaloriesIn', 'CaloriesOut']] = df[['Weight', 'CaloriesIn', 'CaloriesOut']].interpolate(limit_direction='both')

    df.dropna(subset=required_cols, inplace=True)

    if len(df) < cfg.MINIMUM_VALID_RECORDS:
        logging.warning(f"Insufficient data: less than {cfg.MINIMUM_VALID_RECORDS} days of complete entries.")

    df['NetCalories'] = df['CaloriesIn'] - df['CaloriesOut']
    df['DaysSinceStart'] = (df['date'] - df['date'].min()).dt.days

    max_gap = df['date'].diff().dt.days.max()
    if max_gap > cfg.MAX_ALLOWED_LOGGING_GAP_DAYS:
        logging.warning(f"Detected large gap in logging: {max_gap} days.")

    # Filter out unrealistic values
    df = df[
        (df['Weight'] >= cfg.MIN_WEIGHT_KG) & (df['Weight'] <= cfg.MAX_WEIGHT_KG) &
        (df['CaloriesIn'] >= cfg.MIN_CALORIES_IN) & (df['CaloriesIn'] <= cfg.MAX_CALORIES_IN) &
        (df['CaloriesOut'] >= cfg.MIN_CALORIES_OUT) & (df['CaloriesOut'] <= cfg.MAX_CALORIES_OUT)
    ]

    logging.info(f"Data ready for modeling: {len(df)} records.")
    return df[['DaysSinceStart', 'Weight', 'NetCalories']]

def train_and_predict(df: pd.DataFrame, future_days: int = 90) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        logging.error("Cannot train model: DataFrame is empty or None.")
        return None

    logging.info("Training linear regression model...")
    X = df[['DaysSinceStart', 'NetCalories']]
    y = df['Weight']

    model = LinearRegression()
    model.fit(X, y)

    max_day = df['DaysSinceStart'].max()
    future_days_range = np.arange(max_day + 1, max_day + future_days + 1)
    avg_net_calories = df['NetCalories'].mean()

    future_X = pd.DataFrame({
        'DaysSinceStart': future_days_range,
        'NetCalories': [avg_net_calories] * future_days
    })

    predicted_weights = model.predict(future_X)
    prediction_df = pd.DataFrame({
        'DaysFromToday': future_days_range - max_day,
        'PredictedWeightKg': predicted_weights,
        'PredictedWeightLbs': predicted_weights * cfg.KG_TO_LBS
    })

    logging.info("Prediction complete.")
    return prediction_df

def plot_predictions(df: pd.DataFrame, prediction_df: pd.DataFrame):
    logging.info("Plotting predictions...")

    if df is None or prediction_df is None:
        logging.error("Cannot plot: input data missing.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df['DaysSinceStart'], df['Weight'], label='Actual Weight (kg)')
    plt.plot(
        df['DaysSinceStart'].iloc[-1] + prediction_df['DaysFromToday'],
        prediction_df['PredictedWeightKg'],
        label='Predicted Weight (kg)',
        linestyle='--'
    )
    plt.xlabel('Days')
    plt.ylabel('Weight (kg)')
    plt.title('Weight Forecast')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    logging.info("Plot displayed.")