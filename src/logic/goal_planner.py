from datetime import datetime
import pandas as pd

def prompt_for_goal():
    print("\n--- Goal Setup ---")
    goal_weight_lbs = float(input("Enter your target weight (lbs): "))
    goal_weight_kg = goal_weight_lbs * 0.453592
    goal_date_str = input("Enter your target date (YYYY-MM-DD): ")
    goal_date = datetime.strptime(goal_date_str, "%Y-%m-%d").date()
    return goal_weight_kg, goal_date

def evaluate_goal(df: pd.DataFrame, goal_weight_kg: float, goal_date: datetime.date):
    """
    Compares user goal to predicted weight.
    Assumes df has 'Date', 'PredictedWeight', and 'PredictedWeightLbs'.
    """
    goal_day = df[df["date"] == goal_date]

    if goal_day.empty:
        print("Goal date is outside of prediction range.")
        return

    predicted_kg = goal_day["PredictedWeight"].values[0]
    predicted_lbs = goal_day["PredictedWeightLbs"].values[0]
    goal_weight_lbs = goal_weight_kg / 0.453592
    delta_kg = round(predicted_kg - goal_weight_kg, 2)
    delta_lbs = round(predicted_lbs - goal_weight_lbs, 2)

    print(f"\n--- Goal Evaluation ---")
    print(f"Predicted weight on {goal_date}: {predicted_lbs:.1f} lbs ({predicted_kg:.1f} kg)")
    print(f"Your goal: {goal_weight_lbs:.1f} lbs ({goal_weight_kg:.1f} kg)")

    if abs(delta_kg) < 0.5:
        print("You are on track to meet your goal.")
    elif delta_kg > 0:
        print(f"You're predicted to be {delta_lbs:.1f} lbs ({delta_kg:.1f} kg) above your goal.")
    else:
        print(f"You're predicted to be {-delta_lbs:.1f} lbs ({-delta_kg:.1f} kg) below your goal.")