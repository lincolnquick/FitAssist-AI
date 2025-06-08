# ── src/watchdog/safety.py ───────────────────────────────────────
from typing import List, Tuple, Dict
import pandas as pd
from datetime import datetime
from config.constants import (
    SAFE_MIN_CALORIES, SAFE_MAX_WEIGHT_LOSS_RATE,
    SAFE_MAX_WEIGHT_GAIN_RATE, RMR_FLOOR
)

# Helper ------------------------------------------------------------------
def _weekly_weight_change(df: pd.DataFrame) -> float:
    last7 = df.sort_values("date").tail(7)
    if len(last7) < 2:
        return 0.0
    return last7["TrendWeight"].iloc[-1] - last7["TrendWeight"].iloc[0]

# Public API --------------------------------------------------------------
def safety_checks(
    df: pd.DataFrame,
    dob: datetime,
    sex: str,
    goal: Dict
) -> List[Tuple[str, str]]:
    """
    Run rule-based safety / consistency checks.
    Returns a list of (rule_code, human_message) tuples.
    """
    alerts: List[Tuple[str, str]] = []

    # --- Rule 1: unsafe low intake ---------------------------------------
    if (df["TrendCaloriesIn"].tail(7) < SAFE_MIN_CALORIES).any():
        alerts.append((
            "UnsafeIntake",
            f"At least one day in the last week is below "
            f"{SAFE_MIN_CALORIES} kcal intake."
        ))

    # --- Rule 2: rapid weight loss / gain --------------------------------
    wt_delta = _weekly_weight_change(df)
    if wt_delta < -SAFE_MAX_WEIGHT_LOSS_RATE:
        alerts.append((
            "RapidLoss",
            f"Weight is dropping {abs(wt_delta):.1f} kg/week "
            f"(>{SAFE_MAX_WEIGHT_LOSS_RATE} kg safety limit)."
        ))
    if wt_delta >  SAFE_MAX_WEIGHT_GAIN_RATE:
        alerts.append((
            "RapidGain",
            f"Weight is climbing {wt_delta:.1f} kg/week "
            f"(>{SAFE_MAX_WEIGHT_GAIN_RATE} kg safety limit)."
        ))

    # --- Rule 3: RMR sanity check ----------------------------------------
    latest_rmr = df["RMR"].iloc[-1] if "RMR" in df.columns else None
    if latest_rmr is not None and latest_rmr < RMR_FLOOR:
        alerts.append((
            "LowRMR",
            f"Calculated RMR ({latest_rmr:.0f} kcal) is below "
            f"physiological floor ({RMR_FLOOR})."
        ))

    # --- Rule 4: goal feasibility (simple heuristic) ---------------------
    if goal:
        goal_wt   = goal["weight_kg"]
        goal_date = pd.to_datetime(goal["date"])

        horizon_wt = df["TrendWeight"].iloc[-1]              # today
        # crude linear projection: last-30-day change
        last30 = df.sort_values("date").tail(30)
        if len(last30) >= 2:
            trend_30 = ( last30["TrendWeight"].iloc[-1]
                        - last30["TrendWeight"].iloc[0] ) / 30.0
            days_left = (goal_date - df["date"].iloc[-1]).days
            proj_wt   = horizon_wt + trend_30 * days_left
            if proj_wt > goal_wt:
                alerts.append((
                    "GoalNotReachable",
                    f"Linear trend projects {proj_wt:.1f} kg by target date "
                    f"(goal is {goal_wt:.1f} kg). Consider revising plan."
                ))

    return alerts