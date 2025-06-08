"""
src.tools.goal_info
~~~~~~~~~~~~~~~~~~~
Persistently store (or prompt for) a user's goal weight and goal date.

File created on first run:  data/goal_info.csv   e.g.

GoalWeightKG,GoalDate
79.38,2025-12-31
"""
from __future__ import annotations
import os, csv
from datetime import datetime
from config.constants import KG_TO_LBS


def _prompt_float(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Please enter a number.")


def _prompt_date(prompt: str) -> datetime.date:
    while True:
        txt = input(prompt + " (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(txt, "%Y-%m-%d").date()
        except ValueError:
            print("Date format must be YYYY-MM-DD.")


def load_or_prompt_goal(path: str, use_imperial: bool = True) -> dict[str, str | float]:
    """
    Returns {'weight_kg': float, 'date': datetime.date}.  Saves to CSV if absent.
    """
    if os.path.exists(path):
        with open(path, newline="") as f:
            row = next(csv.DictReader(f))
            return {
                "weight_kg": float(row["GoalWeightKG"]),
                "date":     datetime.strptime(row["GoalDate"], "%Y-%m-%d").date()
            }

    # ------- interactive prompts -------------------------------------------
    unit = "lbs" if use_imperial else "kg"
    w = _prompt_float(f"\nEnter your **goal weight** in {unit}: ")
    if use_imperial:            # convert silently for storage
        w /= KG_TO_LBS
    d = _prompt_date("Enter the **target date** for reaching that weight")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["GoalWeightKG", "GoalDate"])
        wr.writerow([f"{w:.2f}", d.isoformat()])

    return {"weight_kg": w, "date": d}