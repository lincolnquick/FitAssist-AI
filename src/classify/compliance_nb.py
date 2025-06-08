# ────────────────────────────────────────────────────────────────
# src/classify/compliance_nb.py
#
# Weekly-compliance classifier for FitAssist-AI.
# ---------------------------------------------------------------
# • Features are week-level aggregates taken from the last
#   12 non-empty weeks of data.
# • A persisted scikit-learn Naïve Bayes model (pickle) is used.
# • The function returns the predicted state plus class
#   probabilities in a stable (on, risk, off) order.
# ────────────────────────────────────────────────────────────────

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np
import pickle

# ----------------------------------------------------------------
# Canonical class order.  ALL downstream code (run.py, GUI, etc.)
# assumes the probabilities are returned in exactly this order.
# ----------------------------------------------------------------
CLASSES = ["on_track", "at_risk", "off_track"]

# Pickled NB model expected to live next to this file
MODEL_PATH = Path(__file__).with_suffix(".pkl")


def _prepare_weekly_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse daily rows to weekly aggregates and engineer
    the minimal feature set used by the NB model.

    Returns
    -------
    pd.DataFrame
        One row per ISO week with the following columns
        (rename to match whatever was used during training):

        - week_end_date
        - mean_net_cal
        - mean_pa
        - wt_change
    """
    if "date" not in df.columns:
        raise ValueError("DataFrame must contain a 'date' column")
    
    df = _ensure_features(df)

    # keep only the fields we need
    subset = df[
        [
            "date",
            "TrendNetCalories",
            "TrendActiveCaloriesBurned",
            "TrendWeight",
        ]
    ].dropna()

    # ISO week label – easier than resample when dates are not continuous
    subset["iso_week"] = subset["date"].dt.isocalendar().week
    subset["year"] = subset["date"].dt.isocalendar().year

    # aggregate
    weekly = (
        subset.groupby(["year", "iso_week"], as_index=False)
        .agg(
            week_end_date=("date", "max"),
            mean_net_cal=("TrendNetCalories", "mean"),
            mean_pa=("TrendActiveCaloriesBurned", "mean"),
            start_wt=("TrendWeight", "first"),
            end_wt=("TrendWeight", "last"),
        )
        .sort_values("week_end_date")
    )
    weekly["wt_change"] = weekly["end_wt"] - weekly["start_wt"]

    return weekly[
        ["week_end_date", "mean_net_cal", "mean_pa", "wt_change"]
    ]

def _ensure_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee that the core feature columns exist.
    If `TrendNetCalories` is missing we derive it from
    CaloriesIn - TDEE (preferred) or CaloriesIn - Basal - Active.
    The function returns a *copy* with new columns where necessary.

    """
    df = df.copy()

    if "TrendNetCalories" not in df.columns:
        if "TrendTDEE" in df.columns:
            df["TrendNetCalories"] = df["TrendCaloriesIn"] - df["TrendTDEE"]
        elif (
            "TrendBasalCaloriesBurned" in df.columns
            and "TrendActiveCaloriesBurned" in df.columns
        ):
            df["TrendNetCalories"] = (
                df["TrendCaloriesIn"]
                - df["TrendBasalCaloriesBurned"]
                - df["TrendActiveCaloriesBurned"]
            )
        else:
            # Still missing?  fall back to zero so NB still runs
            df["TrendNetCalories"] = 0.0

            

    return df

def predict_weekly_state(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Classify the user's most-recent compliance state.

    Parameters
    ----------
    df : pd.DataFrame
        Daily, cleaned FitAssist-AI metrics (must include
        TrendNetCalories, TrendActiveCaloriesBurned, TrendWeight, date).

    Returns
    -------
    dict
        {
            "state": "on_track" | "at_risk" | "off_track" | "unknown",
            "proba": [on_track_prob, at_risk_prob, off_track_prob],
            "weeks": int   # number of aggregated weeks considered
        }
    """
    weekly = _prepare_weekly_features(df)

    if weekly.empty:
        return {"state": "unknown", "proba": [0.0, 0.0, 0.0], "weeks": 0}

    # Use only the most-recent 12 *non-empty* weeks
    weekly_recent = weekly.tail(12)
    n_weeks = len(weekly_recent)

    # Require at least 4 weeks to make a meaningful prediction
    if n_weeks < 4:
        return {
            "state": "unknown",
            "proba": [0.0, 0.0, 0.0],
            "weeks": n_weeks,
        }

    # Feature matrix expected by the persisted model
    # (order must match training script)
    X_recent = weekly_recent[["mean_net_cal", "mean_pa", "wt_change"]].values

    # Load the NB model (lazy load so import works even if pickle absent)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained NB model not found at {MODEL_PATH}. "
            "Run train_compliance_nb.py to create it."
        )

    with open(MODEL_PATH, "rb") as fh:
        nb_model = pickle.load(fh)

    # Predict probability distribution
    raw_proba = nb_model.predict_proba(X_recent)[-1]  # last week is what we care about

    # nb_model.classes_ may be in any order and may even miss a class.
    # Map to our canonical vector (pads missing classes with 0.0).
    proba_dict = dict(zip(nb_model.classes_, raw_proba))
    proba = [float(proba_dict.get(c, 0.0)) for c in CLASSES]

    # Determine the winning class
    state = CLASSES[int(np.argmax(proba))]

    return {"state": state, "proba": proba, "weeks": n_weeks}