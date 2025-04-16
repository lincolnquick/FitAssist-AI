from datetime import datetime
import pandas as pd

def prompt_for_goal():
    print("\n--- Goal Setup ---")
    goal_weight = float(input("Enter your target weight (kg): "))
    goal_date_str = input("Enter your target date (YYYY-MM-DD): ")
    goal_date = datetime.strptime(goal_date_str, "%Y-%m-%d").date()
    return goal_weight, goal_date


def evaluate_goal(df: pd.DataFrame, goal_weight: float, goal_date: datetime.date):
    """
    Compares user goal to predicted weight.
    Assumes df has 'Date' and 'PredictedWeight'.
    """
    goal_day = df[df["Date"] == goal_date]

    if goal_day.empty:
        print("Goal date is outside of prediction range.")
        return

    predicted = goal_day["PredictedWeight"].values[0]
    delta = round(predicted - goal_weight, 2)

    print(f"\n--- Goal Evaluation ---")
    print(f"Predicted weight on {goal_date}: {predicted:.2f} kg")
    print(f"Your goal: {goal_weight:.2f} kg")

    if abs(delta) < 0.5:
        print("You are on track to meet your goal.")
    elif delta > 0:
        print(f"You're predicted to be {delta:.2f} kg above your goal.")
    else:
        print(f"You're predicted to be {-delta:.2f} kg below your goal.")