"""
watchdog.goal_check
───────────────────
Given the daily dataframe + goal info, call the existing
`forecast_metric()` for Weight, then decide whether the
goal looks achievable and by when.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

import pandas as pd

from src.predict.forecast_metric import forecast_metric
from src.tools.energy import calculate_age


def assess_goal_feasibility(
    df: pd.DataFrame,
    dob: datetime,
    sex: str,
    goal_weight_kg: float,
    goal_date: datetime,
    horizon_days: int = 730,    # 2-year maximum look-ahead
) -> Dict[str, Any]:
    """
    Returns
    -------
    {
        "feasible": bool,
        "pred_date": datetime | None,   # date forecast hits / crosses goal
        "delta_days": int | None,       # pred_date - goal_date  (- = early)
        "last_pred": float              # final weight at horizon if never reached
    }
    """
    # --------------- run weight forecast -----------------
    days_to_forecast = list(range(1, horizon_days + 1))
    forecast, *_ = forecast_metric(
        df=df,
        target_metric="Weight",
        forecast_days=days_to_forecast,
        dob=dob,
        sex=sex,
    )

    last_date = df["date"].iloc[-1]

    # Direction: decide if user is *losing* or *gaining* toward goal
    current_wt = df["TrendWeight"].iloc[-1]
    aiming_down = goal_weight_kg < current_wt

    hit_date: Optional[datetime] = None
    for d, wt in forecast.items():
        if (aiming_down and wt <= goal_weight_kg) or (not aiming_down and wt >= goal_weight_kg):
            hit_date = last_date + pd.Timedelta(days=d)
            break

    if hit_date is None:
        # never crossed
        return {
            "feasible": False,
            "pred_date": None,
            "delta_days": None,
            "last_pred": forecast[horizon_days],
        }

    delta = (hit_date - goal_date).days
    return {
        "feasible": True,
        "pred_date": hit_date,
        "delta_days": delta,    # negative = early
        "last_pred": forecast[horizon_days],
    }