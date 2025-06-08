# ────────────────────────────────────────────────────────────────
# src/watchdog/feature_builder.py
#
# Produce the per-week context dictionary that the first-order-logic
# watchdog layer needs.  Nothing in here touches the NB classifier.
# ────────────────────────────────────────────────────────────────
from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple, Any

import pandas as pd
import numpy  as np

from datetime       import datetime
from src.tools.energy      import calculate_age, calculate_rmr
from config.constants      import (
    SAFE_MIN_CALORIES,
    RMR_FLOOR,
    ADAPT_THRESH,
    GAP_THRESH,
)

# helper: make sure TrendNetCalories exists so we can aggregate it
def _ensure_trend_net(df: pd.DataFrame) -> pd.DataFrame:
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
            df["TrendNetCalories"] = 0.0       
    return df


# ----------------------------------------------------------------
# public entry-point
# ----------------------------------------------------------------
def build_watchdog_features(df: pd.DataFrame, dob, sex) -> pd.DataFrame:
    """
    Return a 12-row weekly DataFrame with extra columns:
        mean_cal_in   – avg CaloriesIn/d
        mean_net_cal  – avg NetCal/d (derived if missing)
        mean_pa       – avg ActiveCal/d
        wt_change     – Δ weight (kg) within week
        rmr           – mean RMR for the week
        adaptation    – relative ΔRMR vs. peak (0-1)
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # --------- guarantee net-calories field ----------
    if "TrendNetCalories" not in df.columns:
        df["TrendNetCalories"] = (
            df["TrendCaloriesIn"]
            - df["TrendBasalCaloriesBurned"]
            - df["TrendActiveCaloriesBurned"]
        )

    # ISO week tag
    df["iso_year"] = df["date"].dt.isocalendar().year
    df["iso_week"] = df["date"].dt.isocalendar().week

    # ---------- RMR & adaptation ---------------------
    df["Age"] = df["date"].apply(lambda d: calculate_age(dob, d))
    df["RMR"] = df.apply(lambda r: calculate_rmr(r["TrendWeight"], r["Age"], sex), axis=1)

    peak_rmr = df["RMR"].max()
    df["adapt"] = 1.0 - (df["RMR"] / peak_rmr)

    # ---------- weekly aggregation -------------------
    w = (
        df.groupby(["iso_year", "iso_week"], as_index=False)
        .agg(
            week_end_date=("date", "max"),
            mean_cal_in=("TrendCaloriesIn", "mean"),
            mean_net_cal=("TrendNetCalories", "mean"),
            mean_pa=("TrendActiveCaloriesBurned", "mean"),
            start_wt=("TrendWeight", "first"),
            end_wt=("TrendWeight", "last"),
            mean_rmr=("RMR", "mean"),
            mean_adapt=("adapt", "mean"),
        )
        .sort_values("week_end_date")
    )

    w["wt_change"] = w["end_wt"] - w["start_wt"]

    # Rename to the names expected by rules.py
    w = w.rename(
        columns={
            "mean_rmr": "rmr",
            "mean_adapt": "adaptation",
        }
    )

    return w.tail(12)   # only 12 most-recent weeks