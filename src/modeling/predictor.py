import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def preprocess_for_modeling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the dataset by computing net calories, interpolating missing weights,
    and shifting net calories for predictive modeling.
    """
    df = df.copy()
    
    # Check necessary columns
    required = {"Date", "Weight", "CaloriesIn", "CaloriesOut"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame is missing one of the required columns: {required}")

    df["NetCalories"] = df["CaloriesIn"] - df["CaloriesOut"]
    
    # Interpolate missing weights
    df["Weight"] = df["Weight"].interpolate(method="linear")
    
    # Drop days with missing net calorie info
    df = df.dropna(subset=["NetCalories"])
    
    # Shift net calories by 1 day to model delayed effect
    df["NetCaloriesShifted"] = df["NetCalories"].shift(1)
    df = df.dropna(subset=["Weight", "NetCaloriesShifted"])

    logging.info(f"Prepared dataset with {len(df)} rows after cleaning and shifting.")
    return df


def train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trains a linear regression model using NetCaloriesShifted to predict weight.
    Adds predictions to the dataframe.
    """
    X = df[["NetCaloriesShifted"]]
    y = df["Weight"]

    model = LinearRegression()
    model.fit(X, y)

    df["PredictedWeight"] = model.predict(X)
    mae = mean_absolute_error(y, df["PredictedWeight"])
    logging.info(f"Trained regression model. MAE: {mae:.2f} kg")

    return df


def plot_predictions(df: pd.DataFrame, title: str = "Weight Prediction vs. Actual"):
    """
    Plots actual vs predicted weight over time.
    """
    if "PredictedWeight" not in df.columns:
        raise ValueError("PredictedWeight column not found. Did you run train_and_predict()?")

    plt.figure(figsize=(10, 5))
    plt.plot(df["Date"], df["Weight"], label="Actual Weight", linewidth=2)
    plt.plot(df["Date"], df["PredictedWeight"], label="Predicted Weight", linestyle="--")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Weight (kg)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()