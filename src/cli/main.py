import pandas as pd
from src.parse.apple_health_parser import parse_apple_health_export
from src.parse.clean_and_aggregate import clean_and_aggregate
from src.modeling.predictor import preprocess_for_modeling, train_and_predict, plot_predictions
from src.logic.goal_planner import prompt_for_goal, evaluate_goal

def display_forecast_summary(prediction_df: pd.DataFrame, input_df: pd.DataFrame):
    if prediction_df is None or input_df is None:
        print("\nUnable to generate forecast due to missing data.")
        return

    avg_calories_in = input_df['NetCalories'].mean() + input_df['CaloriesOut'].mean()
    avg_calories_out = input_df['CaloriesOut'].mean()

    print("\n--- Weight Forecast Summary ---\n")
    for day in [30, 60, 90]:
        result = prediction_df[prediction_df['DaysFromToday'] == day]
        if not result.empty:
            row = result.iloc[0]
            print(
                f"Predicted weight in {day} days: "
                f"{row['PredictedWeightLbs']:.1f} lbs "
                f"({row['PredictedWeightKg']:.1f} kg)"
            )

    print(
        f"\nAssumptions:\n"
        f"- Avg. Daily Caloric Intake: {avg_calories_in:.0f} kcal\n"
        f"- Avg. Daily Caloric Expenditure: {avg_calories_out:.0f} kcal\n"
        f"- Net Daily Surplus/Deficit: {(avg_calories_in - avg_calories_out):.0f} kcal\n"
    )

def main():
    print("=== FitAssist AI ===")
    print("Loading Apple Health data...")

    try:
        raw_data = parse_apple_health_export("data/export.xml")
        daily_df = clean_and_aggregate(raw_data)

        if daily_df.empty:
            print("Error: No valid daily data found. Check your Health export for completeness.")
            return

        model_df = preprocess_for_modeling(daily_df)
        prediction_df = train_and_predict(model_df)

        plot_predictions(prediction_df)

        display_forecast_summary(prediction_df, daily_df)

        goal_weight, goal_date = prompt_for_goal()
        evaluate_goal(prediction_df, goal_weight, goal_date)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()