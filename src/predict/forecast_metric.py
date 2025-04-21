"""
forecast_metric.py

This module provides functionality to forecast future values of a specified health metric
(e.g., weight, lean mass) using a rolling window XGBoost regression model trained on 
Apple Health data and engineered features.

Key Features:
- Calculates rolling deltas of a trend-smoothed target metric.
- Automatically selects top correlated features for modeling.
- Adjusts predictions using a physiological adaptation factor derived from changes in Resting Metabolic Rate (RMR).
- Supports forecast horizons defined by arbitrary day offsets.

Dependencies:
- XGBoost for regression modeling
- Custom RMR and age calculation utilities (energy.py)

Author: Lincoln Quick
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from xgboost import XGBRegressor
from sklearn.metrics import r2_score
from src.tools.energy import calculate_rmr, calculate_age
from config.constants import SAFE_MIN_CALORIES

# ---------------------------
# STEP 1: Estimate Metabolic Adaptation
# ---------------------------

def estimate_rmr_adaptation(weight_start, age_start, weight_now, age_now, sex: str) -> float:
    """
    Approximates metabolic adaptation as the relative drop in RMR between starting and current states.
    Adaptation is clamped between 0.0 (no adaptation) and 1.0 (full adaptation).
    """
    rmr_start = calculate_rmr(weight=weight_start, age=age_start, sex=sex)
    rmr_now = calculate_rmr(weight=weight_now, age=age_now, sex=sex)
    adaptation = 1.0 - (rmr_now / rmr_start)
    return max(0.0, min(adaptation, 1.0))


# ---------------------------
# STEP 2: Forecasting Interface
# ---------------------------

def forecast_metric(
    df: pd.DataFrame,
    target_metric: str,
    forecast_days: list[int],
    dob: datetime,
    sex: str,
    window: int = 21,
    top_n_features: int = 5
) -> tuple[dict, list[str], float]:
    """
    Forecasts a specified health metric over a list of future day offsets using a trained XGBoost model.

    Parameters:
        df (pd.DataFrame): Input DataFrame with a 'date' column and trend-smoothed health metrics.
        target_metric (str): Metric name (e.g., 'Weight') to forecast.
        forecast_days (list[int]): List of future day offsets to predict (e.g., [7, 14, 30]).
        dob (datetime): User's date of birth for age calculation.
        sex (str): Biological sex ("male" or "female") used in RMR calculations.
        window (int): Size of the rolling window for feature and delta calculations.
        top_n_features (int): Number of top correlated features to use for training.

    Returns:
        predictions (dict): Mapping of forecast days to predicted metric values.
        top_features (list[str]): Selected feature names used for modeling.
        r2 (float): Training R² score for model fit assessment.
    """
    
    # Ensure chronological order and copy data
    assert "date" in df.columns, "Missing 'date' column"
    df = df.sort_values("date").copy()

    # Define trend and delta columns
    trend_target = f"Trend{target_metric}"
    delta_target = f"{trend_target}_Delta"
    if trend_target not in df.columns:
        raise ValueError(f"Missing trend column: {trend_target}")

    # ---------------------------
    # STEP 3: Prepare Physiological Inputs
    # ---------------------------

    # Enforce physiological floor for CaloriesIn
    df["TrendCaloriesIn"] = df["TrendCaloriesIn"].clip(lower=SAFE_MIN_CALORIES)

    # Derived composition fields
    df["TrendFatMass"] = df["TrendWeight"] * df["TrendBodyFatPercentage"]
    df["TrendLeanBodyMass"] = df["TrendWeight"] * (1 - df["TrendBodyFatPercentage"])

    # Compute dynamic age and resting metabolic rate (RMR) for each row
    df["Age"] = df["date"].apply(lambda d: calculate_age(dob, d))
    df["RMR"] = df.apply(lambda row: calculate_rmr(row["TrendWeight"], row["Age"], sex), axis=1)

    # Compute delta over rolling window
    df[delta_target] = df[trend_target].diff(periods=window)

    # If forecasting body fat %, scale deltas for better regression behavior
    if target_metric == "BodyFatPercentage":
        df[delta_target] = df[delta_target] * 100  # Convert decimal delta to percentage delta

    # ---------------------------
    # STEP 4: Feature Selection
    # ---------------------------

    # Exclude derived or dependent metrics
    exclude = {}
    if target_metric == "BodyFatPercentage":
        exclude = {"TrendNetCalories", "TrendTDEE", "TrendLeanBodyMass", "TrendFatMass", "TrendWeight"}
    else:
        exclude = {"TrendNetCalories", "TrendTDEE", "TrendLeanBodyMass"}
        
    candidate_features = [col for col in df.columns if col.startswith("Trend")
                          and col not in [trend_target, delta_target] and col not in exclude]

    # Correlate features with target delta
    corr = df[candidate_features + [delta_target]].corr()
    corr_series = corr[delta_target].drop(index=delta_target)
    top_features = corr_series.abs().sort_values(ascending=False).head(top_n_features).index.tolist()

    # ---------------------------
    # STEP 5: Construct Feature Matrix
    # ---------------------------

    # Include 30-day and 60-day rolling average features
    for col in top_features:
        df[f"{col}_30d"] = df[col].rolling(30).mean()
        df[f"{col}_60d"] = df[col].rolling(60).mean()

    # Use rolling averages to smooth feature values
    extended_features = top_features + [f"{col}_30d" for col in top_features] + [f"{col}_60d" for col in top_features]
    feature_df = df[extended_features].rolling(window).mean()
    feature_df[f"Recent{target_metric}"] = df[trend_target].shift(1)

    # Align features and target deltas
    features = feature_df.dropna()
    target = df[delta_target].dropna()
    aligned = features.join(target, how="inner")

    # Extract input matrix and labels
    X = aligned[top_features + [f"Recent{target_metric}"]]
    y = aligned[delta_target]

    # ---------------------------
    # STEP 6: Train XGBoost Model
    # ---------------------------

    model = XGBRegressor()
    model.fit(X, y)

    # Evaluate model on training data
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)

    # ---------------------------
    # STEP 7: Prepare Prediction Inputs
    # ---------------------------

    # Get most recent values to use for forecasting
    latest_row = feature_df.iloc[-1].copy()
    latest_row[f"Recent{target_metric}"] = df[trend_target].iloc[-2]
    X_latest = latest_row[top_features + [f"Recent{target_metric}"]].values.reshape(1, -1)

    current_value = df[trend_target].iloc[-1]
    last_date = df["date"].iloc[-1]

    # Reference values for metabolic adaptation baseline
    peak_idx = df["TrendWeight"].expanding().max().idxmax()
    peak_weight = df["TrendWeight"].iloc[peak_idx]
    peak_age = df["Age"].iloc[peak_idx]

    # ---------------------------
    # STEP 8: Forecast Future Values
    # ---------------------------

    predictions = {}
    for days in forecast_days:
        future_date = last_date + timedelta(days=days)
        sim_age = calculate_age(dob, future_date)

        # Predict future delta scaled by forecast horizon
        predicted_delta = model.predict(X_latest)[0]
        scaled_delta = predicted_delta * (days / window)

        # Apply metabolic adaptation ONLY for weight-related forecasts
        if target_metric in {"Weight", "FatMass", "LeanBodyMass"}:
            sim_weight = current_value + scaled_delta
            adaptation = estimate_rmr_adaptation(peak_weight, peak_age, sim_weight, sim_age, sex)
            scaled_delta *= (1 - adaptation)

        # Final prediction
        final_value = current_value + scaled_delta

        # Clip BodyFatPercentage to a plausible range (3% to 60%)
        if target_metric == "BodyFatPercentage":
            final_value = np.clip(final_value, 0.03, 0.60)

        predictions[days] = final_value

    return predictions, top_features, r2