from pathlib import Path
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import r2_score
import logging

logger = logging.getLogger(__name__)

def forecast_metric(
    df: pd.DataFrame,
    target_metric: str,
    forecast_days: list[int],
    window: int = 21,
    top_n_features: int = 5
) -> tuple[dict, list[str], float]:
    """
    Forecasts a metric by training an XGBoost model to predict deltas using the most
    correlated trend features.

    Args:
        df (pd.DataFrame): Cleaned and smoothed health metrics DataFrame.
        target_metric (str): Metric to forecast (e.g., "Weight").
        forecast_days (list[int]): List of future day offsets to predict.
        window (int): Rolling window size to compute deltas and features.
        top_n_features (int): Number of most correlated features to use for prediction.

    Returns:
        tuple:
            - dict: {day_offset: predicted_value}
            - list[str]: Names of top correlated features used
            - float: R² score on training set
    """
    if "date" not in df.columns:
        raise ValueError("The DataFrame must include a 'date' column for sorting.")

    assert isinstance(df, pd.DataFrame), f"df is not a DataFrame: {type(df)}"
    df = df.sort_values(by="date").copy()

    trend_target = f"Trend{target_metric}"
    delta_target = f"{trend_target}_Delta"

    if trend_target not in df.columns:
        raise ValueError(f"Target trend column not found: {trend_target}")

    # Compute delta target
    df[delta_target] = df[trend_target].diff(periods=window)

    # Identify trend-based features excluding the target itself and its delta
    candidate_features = [
        col for col in df.columns 
        if col.startswith("Trend") and col not in [trend_target, delta_target]
    ]

    # Compute correlations with delta target
    corr = df[candidate_features + [delta_target]].corr()
    if delta_target not in corr.columns:
        raise ValueError(f"Correlation calculation failed for {delta_target}")
    
    corr_series = corr[delta_target].drop(index=delta_target)
    top_features = corr_series.abs().sort_values(ascending=False).head(top_n_features).index.tolist()
    logger.info(f"Top correlated features with {target_metric}: {top_features}")

    # Compute rolling mean of selected features
    feature_df = df[top_features].rolling(window).mean()
    feature_df[f"Recent{target_metric}"] = df[trend_target].shift(1)
    
    features = feature_df.dropna()
    
    # Remove delta_target if it somehow ended up in features
    if delta_target in features.columns:
        features = features.drop(columns=[delta_target])
        
    target = df[delta_target].dropna()
    aligned = features.join(target, how='inner')

    X = aligned[top_features + [f"Recent{target_metric}"]]
    y = aligned[delta_target]

    model = XGBRegressor()
    model.fit(X, y)

    # Evaluate model
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    logger.info(f"R² score on training set: {r2:.3f}")

    # Forecast using latest values
    latest_row = feature_df.iloc[-1].copy()
    latest_row[f"Recent{target_metric}"] = df[trend_target].iloc[-2]
    X_latest = latest_row[top_features + [f"Recent{target_metric}"]].values.reshape(1, -1)
    current_value = df[trend_target].iloc[-1]

    predictions = {}
    for days in forecast_days:
        predicted_delta = model.predict(X_latest)[0]
        scaled_delta = predicted_delta * (days / window)
        predictions[days] = current_value + scaled_delta

    return predictions, top_features, r2