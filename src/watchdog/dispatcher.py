"""
watchdog.dispatcher
───────────────────
Central runner that

1. builds the weekly feature window (re-uses feature_builder),
2. executes every rule in rules.ALL_RULES,
3. returns a list of triggered alerts in (code, message) tuples.
"""

from __future__ import annotations
from typing import List, Tuple
import pandas as pd

from .feature_builder import build_watchdog_features
from .rules import ALL_RULES


def run_watchdog(df_daily: pd.DataFrame, dob, sex, goal_info: dict | None = None ) -> List[Tuple[str, str]]:
    """
    Evaluate the FOL rule set on the most-recent 12 weeks.

    Returns
    -------
    list[tuple]   e.g.  [("UnsafeIntake", "..."), ("LowRMR", "...")]
    """
    weekly = build_watchdog_features(df_daily, dob, sex)

    if weekly.empty:
        return [("NoData", "No weekly data available for watchdog checks")]

    latest = weekly.iloc[-1]

    alerts = []
    ctx = dict(goal_info=goal_info, df_daily=df_daily, dob=dob, sex=sex)

    for rule_fn in ALL_RULES:
        try:
            out = rule_fn(latest, weekly, **ctx)   # full signature
        except TypeError:
            # Rule doesn't declare those keywords – fall back to bare call
            out = rule_fn(latest, weekly)

        if out is not None:
            alerts.append(out)

    return alerts