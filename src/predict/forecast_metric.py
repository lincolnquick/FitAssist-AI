"""
forecast_metric.py
────────────────────────────────────────────────────────────────────────────
Forecast future values of a health metric using an XGBoost regressor fitted
to Apple-Health trend data plus engineered physiological features.

* Rolling-window deltas model short-term momentum.
* Automatic Pearson-correlation feature selection (top-K).
* Optional RMR-based metabolic-adaptation damping.
* Designed for both CLI and Streamlit GUI front-ends.

Author: Lincoln Quick
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

from src.tools.energy import calculate_rmr, calculate_age


# ────────────────────────────────────────────────────────────────────────────
# 1. Physiological helper
# ────────────────────────────────────────────────────────────────────────────
def estimate_rmr_adaptation(
    weight_start: float, age_start: float,
    weight_now: float,   age_now: float,
    sex: str
) -> float:
    """Return fractional drop in RMR (clamped 0-1) between start and now."""
    rmr_start = calculate_rmr(weight_start, age_start, sex)
    rmr_now   = calculate_rmr(weight_now,   age_now,   sex)
    adapt = 1.0 - (rmr_now / rmr_start)
    return max(0.0, min(adapt, 1.0))


# ────────────────────────────────────────────────────────────────────────────
# 2. Main forecasting routine
# ────────────────────────────────────────────────────────────────────────────
def forecast_metric(
    df: pd.DataFrame,
    target_metric: str,
    forecast_days: List[int],
    dob: datetime,
    sex: str,
    window: int = 21,
    top_n_features: int = 5
) -> Tuple[Dict[int, float], List[str], float]:
    """
    Predict *Trend<target_metric>* for the day offsets in *forecast_days*.

    Returns
    -------
    predictions : {day_offset: value}
    top_features : list of column names used by the model
    r2 : training-set coefficient of determination
    """
    # ── sanity & preprocessing ───────────────────────────────────────────
    if "date" not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column.")

    df = df.sort_values("date").copy()
    trend_target = f"Trend{target_metric}"
    if trend_target not in df.columns:
        raise ValueError(f"Column '{trend_target}' not found.")

    delta_target = f"{trend_target}_Delta"

    # ── basic cleaning / domain rules ────────────────────────────────────
    df["TrendCaloriesIn"] = df["TrendCaloriesIn"].clip(lower=1250)
    df["Age"]  = df["date"].apply(lambda d: calculate_age(dob, d))
    df["RMR"]  = df.apply(lambda r: calculate_rmr(r["TrendWeight"], r["Age"], sex), axis=1)
    df[delta_target] = df[trend_target].diff(window)

    # ── feature selection ────────────────────────────────────────────────
    derived  = {"TrendNetCalories", "TrendTDEE", "TrendLeanBodyMass"}
    num_kinds = {"i", "u", "f", "c", "b"}                                   # ★ keep only numeric dtypes
    candidate_features = [
        col for col in df.columns
        if col.startswith("Trend")
        and col not in {trend_target, delta_target}
        and col not in derived
        and df[col].dtype.kind in num_kinds                                 # ★ filter applied
    ]

    corr = df[candidate_features + [delta_target]].corr()
    best = (corr[delta_target]
            .drop(index=delta_target)
            .abs()
            .sort_values(ascending=False)
            .head(top_n_features))
    top_features = best.index.tolist()

    # ── design matrix ────────────────────────────────────────────────────
    F = df[top_features].rolling(window).mean()
    F[f"Recent{target_metric}"] = df[trend_target].shift(1)
    aligned = F.dropna().join(df[delta_target].dropna(), how="inner")

    X = aligned[top_features + [f"Recent{target_metric}"]]
    y = aligned[delta_target]

    # ── model fit ────────────────────────────────────────────────────────
    model = XGBRegressor()
    model.fit(X, y)
    r2 = r2_score(y, model.predict(X))

    # ── recent snapshot for inference ────────────────────────────────────
    last_row = F.iloc[-1].copy()
    last_row[f"Recent{target_metric}"] = df[trend_target].iloc[-2]
    X_live = last_row[top_features + [f"Recent{target_metric}"]].to_frame().T
    now_val  = df[trend_target].iloc[-1]
    last_dt  = df["date"].iloc[-1]

    # baseline for adaptation
    idx_peak   = df["TrendWeight"].expanding().max().idxmax()
    peak_wt    = df["TrendWeight"].iloc[idx_peak]
    peak_age   = df["Age"].iloc[idx_peak]

    # ── iterative forecasting loop ───────────────────────────────────────
    preds: Dict[int, float] = {}
    for d in forecast_days:
        # straight XGB delta extrapolated to horizon
        raw_delta   = model.predict(X_live)[0] * (d / window)

        # metabolic adaptation dampening
        future_dt   = last_dt + timedelta(days=d)
        future_age  = calculate_age(dob, future_dt)
        future_wt   = now_val + raw_delta
        adapt       = estimate_rmr_adaptation(peak_wt, peak_age, future_wt, future_age, sex)
        adj_delta   = raw_delta * (1 - adapt)

        preds[d] = now_val + adj_delta

    return preds, top_features, r2