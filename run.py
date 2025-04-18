"""
run.py

Main entry point for analyzing, visualizing, and forecasting health metrics from Apple Health data.

This script performs the following tasks:
1. Checks freshness of data/export.xml vs data/cleaned_metrics.csv.
2. If export.xml is newer or cleaned_metrics.csv is missing, triggers the extract pipeline.
3. Ensures user_characteristics.csv exists (DOB, sex, height), prompting the user if necessary.
4. Loads cleaned data and generates:
    - Visualizations (full, yearly, monthly)
    - Descriptive statistics
    - Correlation reports
    - Caloric efficiency trends
    - Body composition analysis
    - Weight forecast

Author: Lincoln Quick
"""

import os
import ast
import glob
import logging
import subprocess

from data.load_data import load_cleaned_metrics
from src.tools.user_info import load_or_prompt_user_info
from src.visualize.plot_metrics import plot_metrics
from src.analyze.describe_data import describe_data
from src.analyze.correlate_metrics import correlate_metrics
from src.analyze.caloric_efficiency import analyze_efficiency
from src.analyze.body_composition import analyze_body_composition
from src.predict.forecast_weight import forecast_from_cleaned_csv
from src.predict.forecast_metric import forecast_metric
from config.constants import KG_TO_LBS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def plots_are_fresh(plot_dir: str, data_path: str) -> bool:
    """
    Returns True if any plot PNG file is newer than the cleaned metrics CSV.

    Parameters:
        plot_dir (str): Root plot directory.
        data_path (str): Path to cleaned_metrics.csv.

    Returns:
        bool: True if at least one plot is newer than the data file.
    """
    if not os.path.exists(data_path):
        return False

    data_mtime = os.path.getmtime(data_path)
    plot_files = glob.glob(os.path.join(plot_dir, "**", "*.png"), recursive=True)

    if not plot_files:
        return False

    for plot in plot_files:
        if os.path.getmtime(plot) > data_mtime:
            return True  # At least one plot is newer → skip regeneration

    return False  # All plots are older → need to regenerate

def file_is_fresher(newer: str, older: str) -> bool:
    """
    Returns True if `newer` exists and is more recent than `older`.
    """
    return os.path.exists(newer) and (
        not os.path.exists(older) or os.path.getmtime(newer) > os.path.getmtime(older)
    )


def run_extraction():
    """
    Runs the extract_metrics.py pipeline as a module to ensure imports work correctly.
    """
    logger.info("Running data extraction pipeline from Apple Health export...")
    try:
        result = subprocess.run(
            ["python", "-m", "src.cli.extract_metrics"],
            check=True
        )
        logger.info("Extraction complete.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract metrics: {e}")
        raise

def format_summary_lines(lines: list[str], use_imperial: bool = False) -> list[str]:
    """
    Optionally converts metric values to imperial units for display.
    Only applies to weight-related metrics (e.g., Weight, LeanBodyMass).

    Args:
        lines (list[str]): Raw summary lines.
        use_imperial (bool): Whether to convert weight values to pounds.

    Returns:
        list[str]: Formatted summary lines for display.
    """
    converted = []
    for line in lines:
        if use_imperial and any(kw in line for kw in ["Weight", "LeanBodyMass"]):
            parts = line.split(":")
            try:
                value = float(parts[1].strip().split()[0])
                lbs = value * 2.20462
                converted.append(f"{parts[0]:<35}: {lbs:.2f} lbs")
            except Exception:
                converted.append(line)
        else:
            converted.append(line)
    return converted

def main():
    data_dir = "data"
    output_dir = "output"
    plot_dir = os.path.join(output_dir, "plots")

    csv_path = os.path.join(data_dir, "cleaned_metrics.csv")
    export_path = os.path.join(data_dir, "export.xml")
    user_info_path = os.path.join(data_dir, "user_characteristics.csv")

    use_imperial = True
    plot_periods = ["full", "year", "month"]

    # Step 1: Check if cleaned metrics need to be regenerated
    if file_is_fresher(export_path, csv_path):
        logger.info("Detected newer export.xml or missing cleaned_metrics.csv.")
        run_extraction()
    else:
        logger.info("Using existing cleaned_metrics.csv.")

    if not os.path.exists(csv_path):
        logger.error(f"Missing required file: {csv_path}")
        logger.info("Please make sure export.xml exists and try again.")
        return

    # Step 2: Ensure user info is available
    user_info = load_or_prompt_user_info(user_info_path)
    if not user_info:
        logger.error("Unable to load or generate user characteristics.")
        return

    try:
        df = load_cleaned_metrics(csv_path)

        # Step 3: Visualization
        if plots_are_fresh(plot_dir, csv_path):
            logger.info(f"Existing plots are up-to-date. Skipping plot generation. See: {plot_dir}")
        else:
            logger.info("Generating visualizations...")
            plot_metrics(df, output_dir=plot_dir, periods=plot_periods, use_imperial_units=use_imperial)
            logger.info("All plots generated successfully.")

        # Step 4: Description
        logger.info("Analyzing descriptive statistics...")
        summary_lines = describe_data(df=df, output_dir=output_dir)
        print("")
        for line in format_summary_lines(summary_lines, use_imperial=use_imperial):
            print(line)

        print("")
        # Step 5: Correlation
        logger.info("Generating correlation report...")
        corr_lines = correlate_metrics(df=df, output_dir=output_dir)
        for line in corr_lines:
            print(line)

        # Step 6: Efficiency analysis
        logger.info("Estimating caloric efficiency...")
        eff_result = analyze_efficiency(df)
        monthly_eff = eff_result.get("monthly_summary")
        
        if monthly_eff is not None:
            print("\n--- Monthly Caloric Efficiency ---")
            print(monthly_eff[["CaloriesPerPound"]])

        print("")
        
        # Step 7: Body composition
        logger.info("Analyzing body composition trends...")
        analyze_body_composition(df)

        # Step 8: Forecasting
        logger.info("Starting generalized forecasting...")

        available_trends = [col for col in df.columns if col.startswith("Trend")]
        metric_choices = sorted(set(col.replace("Trend", "") for col in available_trends))

        print("\n--- Forecast Setup ---")
        print("Available metrics to forecast:")
        for i, m in enumerate(metric_choices, 1):
            print(f"{i}. {m}")

        selected_input = input("\nEnter the metric to forecast (e.g., Weight or 8): ").strip()

        # Check if input is a digit and map to index
        if selected_input.isdigit():
            index = int(selected_input) - 1
            if 0 <= index < len(metric_choices):
                selected = metric_choices[index]
            else:
                logger.error(f"Invalid number selection: {selected_input}")
                return
        elif selected_input in metric_choices:
            selected = selected_input
        else:
            logger.error(f"Invalid metric: {selected_input}")
            return

        # Get forecast days from user
        days_input = input("Enter days to forecast (e.g., 30 or [7,14,30]): ").strip()

        try:
            if days_input.startswith("[") and days_input.endswith("]"):
                forecast_days = ast.literal_eval(days_input)
                if not all(isinstance(day, int) and day > 0 for day in forecast_days):
                    raise ValueError
            else:
                span = int(days_input)
                if span <= 0:
                    raise ValueError
                forecast_days = list(range(1, span + 1))  # Predict every day from 1 to span
        except Exception:
            logger.error("Invalid forecast day format. Use a number (e.g., 30) or list (e.g., [7,14,30])")
            return

        try:
            result = forecast_metric(df, target_metric=selected, forecast_days=forecast_days)
            if result:
                forecast, used_features, r2 = result

                print(f"\n--- {selected} Forecast ---")
                for d, val in forecast.items():
                    if use_imperial and selected in ["Weight", "LeanBodyMass"]:
                        print(f"{d} days: {val * KG_TO_LBS:.2f} lbs")
                    else:
                        print(f"{d} days: {val:.2f}")

                print(f"\nFeatures used: {', '.join(used_features)}")
                print(f"Model R² score (train): {r2:.3f}")
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")

    except Exception as e:
        logger.error(f"Execution failed: {e}")


if __name__ == "__main__":
    main()