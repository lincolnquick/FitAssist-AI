# src/parse/apple_health_parser.py

import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict

def parse_apple_health_export(xml_path: str) -> Dict[str, pd.DataFrame]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Health records of interest
    records = {
        "Weight": [],
        "ActiveEnergyBurned": [],
        "DietaryEnergyConsumed": [],
    }

    for record in root.iter("Record"):
        record_type = record.get("type")

        if "BodyMass" in record_type:
            records["Weight"].append(record.attrib)
        elif "ActiveEnergyBurned" in record_type:
            records["ActiveEnergyBurned"].append(record.attrib)
        elif "DietaryEnergyConsumed" in record_type:
            records["DietaryEnergyConsumed"].append(record.attrib)

    return {key: pd.DataFrame(value) for key, value in records.items()}