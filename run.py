"""
run.py

Entry point for generating health metric visualizations from cleaned data.

Checks for the presence of cleaned CSV data and uses plotting modules
to generate time series visualizations.

Author: Lincoln Quick
"""

import os
import logging
from data.load_data import load_cleaned_metrics
from src.visualize.plot_metrics import plot_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    csv_path = "output/cleaned_metrics.csv"
    plot_output_dir = "output/plots"
    plot_periods = ["full", "year", "month"]
    use_imperial_units = True

    if not os.path.exists(csv_path):
        logger.error(f"Missing required file: {csv_path}")
        logger.info("Please run extract_metrics.py to generate cleaned_metrics.csv first.")
        return

    try:
        df = load_cleaned_metrics(csv_path)
        plot_metrics(df, plot_output_dir, plot_periods, use_imperial_units)
        logger.info("All plots generated successfully.")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")

if __name__ == "__main__":
    main()