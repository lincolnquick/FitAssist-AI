"""
run.py

Entry point for analyzing and visualizing Apple Health metrics.

Author: Lincoln Quick
"""

import os
import logging
import time
from data.load_data import load_cleaned_metrics
from src.visualize.plot_metrics import plot_metrics
from src.analyze.describe_data import describe_data
from src.analyze.correlate_metrics import correlate_metrics
from src.analyze.caloric_efficiency import analyze_efficiency
from src.analyze.body_composition import analyze_body_composition
from src.predict.forecast_weight import forecast_from_cleaned_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    csv_path = "output/cleaned_metrics.csv"
    output_dir = "output"
    plot_dir = os.path.join(output_dir, "plots")
    use_imperial = True
    plot_periods = ["full", "year", "month"]

    if not os.path.exists(csv_path):
        logger.error(f"Missing required file: {csv_path}")
        logger.info("Please run extract_metrics.py to generate cleaned_metrics.csv first.")
        return

    try:
        df = load_cleaned_metrics(csv_path)

        # # Step 1: Visualization
        # logger.info("Generating visualizations...")
        # plot_metrics(df, output_dir=plot_dir, periods=plot_periods, use_imperial_units=use_imperial)
        # logger.info("All plots generated successfully.")

        # # Step 2: Description
        # logger.info("Analyzing descriptive statistics...")
        # describe_data(df=df, output_dir=output_dir)

        # # Step 3: Correlation
        # logger.info("Generating correlation report...")
        # correlate_metrics(df=df, output_dir=output_dir)

        # # Step 4: Efficiency analysis
        # logger.info("Estimating caloric efficiency...")
        # eff_result = analyze_efficiency(df)
        # monthly_eff = eff_result.get("monthly_summary")
        # if monthly_eff is not None:
        #     print(monthly_eff[["CaloriesPerPound"]])

        # # Step 5: Body composition
        # logger.info("Analyzing body composition trends...")
        # analyze_body_composition(df)

        # Step 6: Forecasting
        logger.info("Forecasting weight trajectory...")
        forecast = forecast_from_cleaned_csv()
        if forecast:
            print("\n--- Weight Forecast ---")
            for days, weight in forecast.items():
                print(f"{days} days: {weight:.2f} kg")
        else:
            logger.error("Weight forecast failed.")
        

    except Exception as e:
        logger.error(f"Execution failed: {e}")

if __name__ == "__main__":
    main()