from src.parse.apple_health_parser import parse_apple_health_export
from src.parse.clean_and_aggregate import clean_and_aggregate
from src.modeling.predictor import preprocess_for_modeling, train_and_predict, plot_predictions
from src.logic.goal_planner import prompt_for_goal, evaluate_goal

def main():
    print("=== FitAssist AI ===")
    print("Loading Apple Health data...")

    try:
        raw_data = parse_apple_health_export("data/export.xml")
        daily_df = clean_and_aggregate(raw_data)
        
        # Debugging output
        print("\n--- Aggregated Columns ---")
        print(daily_df.columns)
        print(daily_df.head())

        model_df = preprocess_for_modeling(daily_df)
        model_df = train_and_predict(model_df)

        plot_predictions(model_df)

        goal_weight, goal_date = prompt_for_goal()
        evaluate_goal(model_df, goal_weight, goal_date)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()