"""
watchdog.rules
──────────────
Domain-specific first-order-logic “Horn clauses” to enforce
safety and reasoning constraints *after* statistical predictions.

Each rule is a function that accepts the **latest** weekly record
plus the *entire* weekly window and returns either:

    None                     -  no issue
    (code: str, message: str)

The dispatcher collects all returned tuples in the order the rules
are registered.  New rules = just write a function and add it to
ALL_RULES at the bottom.
"""

from __future__ import annotations
from typing import Tuple, Optional

import numpy as np
import pandas as pd

from config.constants import SAFE_MIN_CALORIES, SAFE_MAX_WEIGHT_LOSS_RATE, SAFE_MAX_WEIGHT_GAIN_RATE, RMR_FLOOR, ADAPT_THRESH, GAP_THRESH


# Helper 
def _weekly_rate(kg_change: float) -> float:
    """Convert kg change over one week to absolute rate (kg/week)."""
    return abs(kg_change)

# Safety rules 
def min_calorie_rule(latest: pd.Series, *_):
    """Calories < SAFE_MIN_CALORIES → unsafe."""
    if latest["mean_cal_in"] < SAFE_MIN_CALORIES:
        return ("UnsafeIntake",
                f"Avg calories ({latest['mean_cal_in']:.0f}) "
                f"below safety floor {SAFE_MIN_CALORIES} kcal/d")
    return None


def rapid_loss_rule(latest: pd.Series, *_):
    """Weekly weight change < -SAFE_MAX_WEIGHT_LOSS_RATE → flag."""
    if latest["wt_change"] < -SAFE_MAX_WEIGHT_LOSS_RATE:
        return ("RapidWeightLoss",
                f"Loss {latest['wt_change']:.2f} kg in 7 days – "
                "exceeds recommended limit")
    return None


def rapid_gain_rule(latest: pd.Series, *_):
    """Weekly weight gain > SAFE_MAX_WEIGHT_GAIN_RATE → flag."""
    if latest["wt_change"] > SAFE_MAX_WEIGHT_GAIN_RATE:
        return ("RapidWeightGain",
                f"Gain {latest['wt_change']:.2f} kg in 7 days – "
                "exceeds recommended limit")
    return None


def rmr_floor_rule(latest: pd.Series, *_):
    """RMR slipping under physiological floor."""
    if latest["rmr"] < RMR_FLOOR:
        return ("LowRMR",
                f"Estimated RMR {latest['rmr']:.0f} kcal/d below "
                f"floor ({RMR_FLOOR}) – check data quality / health")
    return None



# Reasoning / consistency rules 
def deficit_no_loss_rule(latest: pd.Series, _weekly: pd.DataFrame):
    """
    Large caloric deficit but weight not dropping → mismatch / logging issue.
    """
    if latest["mean_net_cal"] < -500 and latest["wt_change"] > 0:
        return ("MismatchDeficit",
                "Sustained caloric deficit but weight ↑ – possible "
                "logging error or water retention")
    return None


def plateau_adaptation_rule(latest: pd.Series, _weekly: pd.DataFrame):
    """Adaptation exceeds threshold – weight loss expected to slow."""
    if latest["adaptation"] > ADAPT_THRESH:
        return ("MetabolicAdapt",
                f"Estimated adaptation {latest['adaptation']*100:.1f}% "
                "– expect plateau; consider diet break / re-feed")
    return None


def stale_data_rule(_latest: pd.Series, weekly: pd.DataFrame):
    """No readings for > GAP_THRESH days – cannot trust model."""
    gap = (pd.Timestamp.now().normalize() - weekly["week_end_date"].iloc[-1]).days
    if gap > GAP_THRESH:
        return ("StaleData",
                f"No new logs for {gap} days – predictions may be stale")
    return None

def goal_feasible_rule(
        latest: pd.Series, 
        weekly: pd.DataFrame, 
        *,
        goal_info: dict | None = None,
        df_daily: pd.DataFrame | None = None, 
        dob = None, 
        sex: str = 'male'
        ):
    """
    Side-data rule: check if forecast reaches goal_weight by goal_date.
    Requires goal_info dict with keys 'weight_kg' & 'date'.
    """
    if goal_info is None or df_daily is None:
        return None
    
    from .goal_check import assess_goal_feasibility   # local import to avoid cycles

    res = assess_goal_feasibility(
        df=df_daily,
        dob=dob,
        sex=sex,
        goal_weight_kg=goal_info["weight_kg"],
        goal_date=goal_info["date"],
    )

    if not res["feasible"]:
        return ("GoalNotReached",
                f"Forecast never reaches goal ({goal_info['weight_kg']:.1f} kg). "
                f"Weight at horizon ≈ {res['last_pred']:.1f} kg")
    if abs(res["delta_days"]) > 14:  # >2 weeks early/late
        when = "late" if res["delta_days"] > 0 else "early"
        return ("GoalTimingDrift",
                f"Goal hit {abs(res['delta_days'])} days {when} "
                f"(pred {res['pred_date'].date()})")
    return None


# Register the rule functions here (order = execution order) -------#
ALL_RULES = [
    min_calorie_rule,
    rapid_loss_rule,
    rapid_gain_rule,
    rmr_floor_rule,
    deficit_no_loss_rule,
    plateau_adaptation_rule,
    stale_data_rule,
    goal_feasible_rule
]