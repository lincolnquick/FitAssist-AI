import pandas as pd
from collections import defaultdict
import logging
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def clean_and_aggregate(parsed_data: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    Cleans and aggregates parsed Apple Health data by date.
    
    Args:
        parsed_data (Dict): Dictionary of lists keyed by Apple Health record type.
    
    Returns:
        pd.DataFrame: Aggregated daily metrics with user-friendly column names.
    """
    logging.info("Starting data cleaning and aggregation...")

    # Map Apple Health record types to output column names
    type_to_column = {
        'HKQuantityTypeIdentifierBodyMass': 'Weight',  # in kg
        'HKQuantityTypeIdentifierDietaryEnergyConsumed': 'CaloriesIn',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'CaloriesOut',
        'HKQuantityTypeIdentifierBasalEnergyBurned': 'BasalCaloriesOut',
        'HKQuantityTypeIdentifierBodyFatPercentage': 'BodyFatPercentage',
        'HKQuantityTypeIdentifierLeanBodyMass': 'LeanBodyMass',  # in kg
        'HKQuantityTypeIdentifierDistanceWalkingRunning': 'DistanceWalkingRunning',  # in km
        'HKQuantityTypeIdentifierStepCount': 'StepCount',
    }

    daily_data = defaultdict(lambda: defaultdict(float))

    # Aggregate values by date
    for r_type, records in parsed_data.items():
        column_name = type_to_column.get(r_type)
        if not column_name:
            continue

        for entry in records:
            date = entry["date"]
            value = entry["value"]
            daily_data[date][column_name] += value

    # Create DataFrame
    df = pd.DataFrame.from_dict(daily_data, orient='index')
    df.index.name = "date"
    df.reset_index(inplace=True)
    df.sort_values(by="date", inplace=True)

    logging.info(f"Aggregated daily entries: {len(df)} days with data")
    logging.debug(f"Columns available: {df.columns.tolist()}")

    return df