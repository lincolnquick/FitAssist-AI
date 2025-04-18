import xml.etree.ElementTree as ET
from collections import defaultdict
from config.constants import LBS_TO_KG
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

# Metrics that should be summed across the day (additive)
SUM_METRICS = {
    'HKQuantityTypeIdentifierDietaryEnergyConsumed',
    'HKQuantityTypeIdentifierActiveEnergyBurned',
    'HKQuantityTypeIdentifierBasalEnergyBurned',
    'HKQuantityTypeIdentifierStepCount',
    'HKQuantityTypeIdentifierDistanceWalkingRunning',
}

# Metrics that should be averaged per day (point-in-time or snapshot)
AVERAGE_METRICS = {
    'HKQuantityTypeIdentifierBodyMass',
    'HKQuantityTypeIdentifierBodyFatPercentage',
    'HKQuantityTypeIdentifierLeanBodyMass',
}

ALL_METRICS = SUM_METRICS | AVERAGE_METRICS

def parse_apple_health_export(xml_path: str) -> dict:
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"File not found: {xml_path}")

    logging.info(f"Parsing Apple Health data from {xml_path}...")

    records_by_type_and_date = defaultdict(lambda: defaultdict(list))
    weight_unit = None

    context = ET.iterparse(xml_path, events=("start", "end"))
    _, root = next(context)

    for event, elem in context:
        if event == "end" and elem.tag == "Record":
            r_type = elem.get("type")
            if r_type not in ALL_METRICS:
                continue

            unit = elem.get("unit")
            value = elem.get("value")
            date = elem.get("startDate")[:10]

            if not (value and date):
                continue

            try:
                value = float(value)
            except ValueError:
                continue

            # For debugging specific dates
            target_dates = {"2025-04-13", "2025-04-14", "2025-04-15"}
            if date in target_dates:
                logging.debug(f"[PARSE] {r_type} on {date}: value={value}, unit={unit}")

            if r_type == "HKQuantityTypeIdentifierBodyMass":
                if weight_unit is None:
                    weight_unit = unit
                    logging.info(f"Detected weight unit: {weight_unit}")
                if unit == "lb":
                    value *= LBS_TO_KG

            records_by_type_and_date[r_type][date].append(value)
            elem.clear()

    # Aggregate data
    data = defaultdict(list)
    for r_type, daily_values in records_by_type_and_date.items():
        for date, values in daily_values.items():
            if r_type in SUM_METRICS:
                aggregated = sum(values)
            elif r_type in AVERAGE_METRICS:
                aggregated = sum(values) / len(values)
            else:
                continue  # Shouldn't happen
            data[r_type].append({"date": date, "value": aggregated})

    logging.info("Finished parsing records.")
    return {
        "data": data,
        "weight_unit": weight_unit or "unknown"
    }