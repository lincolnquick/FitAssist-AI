import xml.etree.ElementTree as ET
from collections import defaultdict
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def parse_apple_health_export(xml_path: str) -> dict:
    """
    Parses Apple Health XML export to extract relevant health metrics.

    Args:
        xml_path (str): Path to the exported Apple Health XML file.

    Returns:
        dict: A dictionary containing:
            - "data": Dictionary mapping record type to list of date-value dicts
            - "weight_unit": Original unit used for weight ("kg" or "lb")
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"File not found: {xml_path}")

    logging.info(f"Parsing Apple Health data from {xml_path}...")

    # Record types to extract
    target_types = {
        'HKQuantityTypeIdentifierBodyMass',
        'HKQuantityTypeIdentifierDietaryEnergyConsumed',
        'HKQuantityTypeIdentifierActiveEnergyBurned',
        'HKQuantityTypeIdentifierBasalEnergyBurned',
        'HKQuantityTypeIdentifierBodyFatPercentage',
        'HKQuantityTypeIdentifierLeanBodyMass',
        'HKQuantityTypeIdentifierDistanceWalkingRunning',
        'HKQuantityTypeIdentifierStepCount',
    }

    data = defaultdict(list)
    weight_unit = None

    context = ET.iterparse(xml_path, events=("start", "end"))
    _, root = next(context)  # Get root element

    for event, elem in context:
        if event == "end" and elem.tag == "Record":
            r_type = elem.get("type")
            if r_type not in target_types:
                continue

            unit = elem.get("unit")
            value = elem.get("value")
            start_date = elem.get("startDate")

            if not (value and start_date):
                continue

            try:
                value = float(value)
            except ValueError:
                continue

            # Normalize weight units to kg
            if r_type == 'HKQuantityTypeIdentifierBodyMass':
                if weight_unit is None:
                    weight_unit = unit
                    logging.info(f"Detected weight unit: {weight_unit}")
                if unit == "lb":
                    value *= 0.45359237
                unit = "kg"

            data[r_type].append({
                "date": start_date[:10],  # Extract only date (YYYY-MM-DD)
                "value": value
            })

            elem.clear()  # Free memory

    logging.info("Finished parsing records.")
    return {
        "data": data,
        "weight_unit": weight_unit or "unknown"
    }