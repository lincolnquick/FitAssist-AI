# tests/test_apple_health_parser.py

import os
import pytest
import pandas as pd
import logging
from src.parse.apple_health_parser import parse_apple_health_export
from src.parse.clean_and_aggregate import clean_and_aggregate

logging.basicConfig(level=logging.INFO)

def test_parse_export_file():
    file_path = "data/export.xml"
    assert os.path.exists(file_path), "Apple Health export file not found at data/export.xml."

    data = parse_apple_health_export(file_path)

    expected_keys = {"Weight", "ActiveEnergyBurned", "DietaryEnergyConsumed"}
    for key in expected_keys:
        assert key in data
        assert isinstance(data[key], pd.DataFrame)

    logging.info("Parsed Apple Health export successfully.")


def test_clean_and_aggregate_output():
    file_path = "data/export.xml"
    raw_data = parse_apple_health_export(file_path)
    daily_df = clean_and_aggregate(raw_data)

    assert isinstance(daily_df, pd.DataFrame), "Output should be a DataFrame."
    assert "Weight" in daily_df.columns or "CaloriesIn" in daily_df.columns or "CaloriesOut" in daily_df.columns

    if not daily_df.empty:
        logging.info("Cleaned and aggregated data sample:")
        logging.info(daily_df.head(3).to_string(index=False))
    else:
        logging.warning("Aggregated DataFrame is empty.")