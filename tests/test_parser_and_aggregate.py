import os
import sys
import logging
import pytest

# Ensure src is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parse.apple_health_parser import parse_apple_health_export
from src.parse.clean_and_aggregate import clean_and_aggregate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

TEST_FILE = "data/export.xml"

@pytest.mark.order(1)
def test_parse_apple_health_export():
    assert os.path.exists(TEST_FILE), "Test file does not exist."

    result = parse_apple_health_export(TEST_FILE)
    assert isinstance(result, dict), "Result should be a dictionary."

    data = result["data"]
    weight_unit = result["weight_unit"]

    assert "HKQuantityTypeIdentifierBodyMass" in data, "Missing BodyMass record."
    assert weight_unit in {"kg", "lb"}, "Unexpected weight unit."

    logging.info("test_parse_apple_health_export passed with unit: %s", weight_unit)

@pytest.mark.order(2)
def test_clean_and_aggregate():
    result = parse_apple_health_export(TEST_FILE)
    data = result["data"]

    df = clean_and_aggregate(data)

    assert not df.empty, "Aggregated DataFrame should not be empty."
    assert "date" in df.columns, "Missing 'date' column."
    assert "Weight" in df.columns, "Missing 'Weight' column."
    assert df["Weight"].dtype in ["float64", "float32"], "Weight column should be numeric."

    logging.info("test_clean_and_aggregate passed with %d rows", len(df))
    logging.info("Sample data:\n%s", df.head().to_string(index=False))