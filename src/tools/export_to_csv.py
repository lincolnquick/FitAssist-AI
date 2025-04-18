"""
CSV Exporter for FitAssist AI

This module provides a function to export cleaned or parsed Apple Health metrics
to a CSV file. It accepts a dictionary in the format {date: {metric: value}} and
converts it into a DataFrame sorted by date.

Features:
- Automatically creates the output directory if it doesn't exist.
- Filenames include the date range (e.g., metrics_for_2022-01-01_to_2023-01-01.csv).
- Supports debugging via logger output.

Used in preprocessing and analysis pipelines to persist metric data in human-readable format.
"""
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

def export_metrics_to_csv(data: dict, output_dir: str = "output") -> str:
    """
    Exports aggregated health metrics to a CSV file.

    Args:
        data (dict): Dictionary of {date: {metric: value}}
        output_dir (str): Directory where the CSV will be saved.

    Returns:
        str: Full path to the saved CSV file.
    """
    if not data:
        logger.error("No data provided for export.")
        return ""

    logger.info("Preparing to export health metrics to CSV...")

    os.makedirs(output_dir, exist_ok=True)

    # Convert to DataFrame
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = "date"
    df = df.sort_index()
    df.reset_index(inplace=True)

    # Generate filename
    start_date = df["date"].min()
    end_date = df["date"].max()
    filename = f"metrics_for_{start_date}_to_{end_date}.csv"
    output_path = os.path.join(output_dir, filename)

    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Exported metrics to {output_path}")
    logger.debug(f"First few rows:\n{df.head()}")

    return output_path