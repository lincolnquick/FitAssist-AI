import pandas as pd
import pytest
import os

# Tolerances
TOLERANCES = {
    "Weight": 0.1,
    "LeanBodyMass": 0.1,
    "DistanceWalkingRunning": 0.1,  # <- increased tolerance
    "StepCount": 10,
    "CaloriesIn": 1,
    "BasalCaloriesOut": 1,
    "CaloriesOut": 1,
}

# Expected values for testing
EXPECTED_DATA = {
    "2025-04-15": {
        "Weight": 87.81,
        "LeanBodyMass": 67.64,
        "DistanceWalkingRunning": 13.4,
        "StepCount": 18583,
        "CaloriesIn": 1550,
        "BasalCaloriesOut": 2189,
        "CaloriesOut": 769 + 2189,  # Total output
    },
    "2025-04-13": {
        "Weight": 87.63,
        "LeanBodyMass": 67.27,
        "DistanceWalkingRunning": 12.9,
        "StepCount": 17803,
        "CaloriesIn": 2002,
        "BasalCaloriesOut": 2116,
        "CaloriesOut": 476 + 2116,
    }
}

@pytest.mark.parametrize("date_str, expected", EXPECTED_DATA.items())
def test_cleaned_data_values(date_str, expected):
    csv_path = "output/cleaned_data.csv"
    assert os.path.exists(csv_path), "cleaned_data.csv not found"

    df = pd.read_csv(csv_path, parse_dates=["date"])
    row = df[df["date"] == pd.to_datetime(date_str)]

    assert not row.empty, f"No data found for {date_str}"

    row = row.iloc[0]  # Get the first (and expected only) row

    # Check values with tolerances
    for field, expected_value in expected.items():
        actual_value = row.get(field)
        assert actual_value is not None, f"{field} missing for {date_str}"

        delta = abs(actual_value - expected_value)
        tolerance = TOLERANCES.get(field, 0.1)

        assert delta <= tolerance, (
            f"{field} mismatch for {date_str}:\n"
            f"  Expected: {expected_value}\n"
            f"  Actual:   {actual_value}\n"
            f"  Allowed Tolerance: {tolerance}\n"
            f"  Difference: {delta:.4f}"
        )