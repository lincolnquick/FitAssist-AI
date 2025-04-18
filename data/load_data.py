"""
load_data.py

Utility module for loading and validating cleaned Apple Health metrics.

Author: Lincoln Quick
"""

import os
import pandas as pd
import logging
from config.constants import REQUIRED_COLUMNS

logger = logging.getLogger(__name__)

def load_cleaned_metrics(path: str = "output/cleaned_metrics.csv") -> pd.DataFrame:
    """
    Loads the cleaned metrics CSV into a DataFrame and parses dates.

    Args:
        path (str): Path to the cleaned_metrics.csv file.

    Returns:
        pd.DataFrame: Loaded DataFrame with parsed dates.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_csv(path, parse_dates=["date"])
    logger.info(f"Loaded cleaned metrics from: {path}")

    # Inspect the loaded DataFrame
    logger.debug("--- Loaded DataFrame Inspection ---")
    logger.debug(f"Shape: {df.shape}")
    logger.debug(f"Columns: {df.columns.tolist()}")
    logger.debug(f"Weight NaN count: {df['Weight'].isnull().sum()}")
    logger.debug(f"First 5 rows:\n{df.head()}")
    logger.debug(f"Last 5 rows:\n{df.tail()}")
    logger.debug(f"Date range: {df['date'].min()} to {df['date'].max()}")

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")

    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df