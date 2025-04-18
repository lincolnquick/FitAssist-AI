"""
Apple Health XML Parser for FitAssist AI

This module parses an Apple Health export XML file and extracts health metrics.
It handles source prioritization, deduplication, unit conversion, and daily
aggregation (sum or average) for supported metrics.

Metrics include: Weight, Lean Body Mass, Body Fat %, Calories, Steps, Distance, etc.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from config.constants import (
    TARGET_METRICS,
    SUM_METRICS,
    SOURCE_PRIORITY,
    LBS_TO_KG
)
import logging
import os

logger = logging.getLogger(__name__)

def get_source_priority(source: str, device: str) -> int:
    """
    Assigns priority to a data source. Apple Watch > iPhone > default (3 > 2 > 1).
    """
    if "Apple Watch" in device:
        return SOURCE_PRIORITY.get("Apple Watch", 1)
    if "iPhone" in source:
        return SOURCE_PRIORITY.get("iPhone", 1)
    return SOURCE_PRIORITY.get("default", 1)

def parse_record(elem, weight_unit):
    """
    Parses a single <Record> element to extract metric data.

    Returns:
        tuple: (date_str, metric_name, (value, timestamp), priority, weight_unit)
        or None if the element is invalid or irrelevant.
    """
    r_type = elem.get("type")
    if r_type not in TARGET_METRICS:
        return None

    metric = TARGET_METRICS[r_type]
    date_str = (elem.get("startDate") or "")[:10]
    value_str = elem.get("value")
    timestamp = elem.get("startDate") or ""
    source = elem.get("sourceName") or ""
    device = elem.get("device") or ""

    if not value_str or not date_str:
        return None

    try:
        value = float(value_str)
    except ValueError:
        return None

    unit = elem.get("unit")
    if r_type == "HKQuantityTypeIdentifierBodyMass":
        if weight_unit is None and unit:
            weight_unit = unit
            logger.info(f"Detected weight unit: {weight_unit}")
        if unit == "lb":
            value *= LBS_TO_KG
    elif r_type == "HKQuantityTypeIdentifierLeanBodyMass" and unit == "lb":
        value *= LBS_TO_KG

    priority = get_source_priority(source, device)
    return date_str, metric, (value, timestamp), priority, weight_unit

def parse_health_metrics(xml_path: str) -> dict:
    """
    Parses the Apple Health export XML file and returns a dictionary of cleaned, daily metrics.

    Args:
        xml_path (str): Path to Apple Health export XML file.

    Returns:
        dict: {date: {metric: aggregated_value, ...}, ...}
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"File not found: {xml_path}")

    logger.info(f"Parsing health metrics from {xml_path}...")
    temp = defaultdict(lambda: defaultdict(lambda: {"priority": 0, "seen": set(), "values": []}))
    weight_unit = None
    context = ET.iterparse(xml_path, events=("start", "end"))
    _, root = next(context)

    for idx, (event, elem) in enumerate(context):
        if event == "end" and elem.tag == "Record":
            result = parse_record(elem, weight_unit)
            if result is None:
                elem.clear()
                continue
            date, metric, (value, timestamp), priority, weight_unit = result

            record_key = (timestamp, value)
            slot = temp[date][metric]

            if priority > slot["priority"]:
                temp[date][metric] = {"priority": priority, "seen": {record_key}, "values": [value]}
            elif priority == slot["priority"] and record_key not in slot["seen"]:
                slot["seen"].add(record_key)
                slot["values"].append(value)

            elem.clear()

        if idx % 1_000_000 == 0 and idx > 0:
            logger.info(f"Parsed {idx:,} records...")

    final = {}
    for date, metrics in temp.items():
        daily = {}
        for metric, data in metrics.items():
            values = data["values"]
            daily[metric] = sum(values) if metric in SUM_METRICS else sum(values) / len(values)
        if daily:
            final[date] = daily

    logger.info(f"Finished parsing {len(final)} unique dates.")
    return final