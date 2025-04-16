import xml.etree.ElementTree as ET
from collections import defaultdict
import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def inspect_export(xml_path: str, output_path: str = "output/record_summary.txt"):
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"File not found: {xml_path}")

    start_time = time.time()
    logging.info(f"Starting to stream-parse: {xml_path}")

    record_counts = defaultdict(int)
    units_per_type = defaultdict(set)
    seen_types = set()

    count = 0
    context = ET.iterparse(xml_path, events=("start", "end"))
    _, root = next(context)  # get root element

    for event, elem in context:
        if event == "end" and elem.tag == "Record":
            r_type = elem.get("type", "UNKNOWN")
            r_unit = elem.get("unit", "None")

            record_counts[r_type] += 1
            units_per_type[r_type].add(r_unit)

            if r_type not in seen_types:
                logging.info(f"Discovered new record type: {r_type} | Unit: {r_unit}")
                seen_types.add(r_type)

            count += 1
            if count % 100000 == 0:
                logging.info(f"Parsed {count:,} records...")

            elem.clear()  # free memory

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("Apple Health Record Summary\n")
        f.write("===========================\n")
        for r_type in sorted(record_counts.keys()):
            count = record_counts[r_type]
            units = ", ".join(sorted(units_per_type[r_type]))
            f.write(f"{r_type}: {count} entries | Units: {units}\n")

    elapsed = time.time() - start_time
    logging.info(f"Finished parsing {count:,} records in {elapsed:.2f} seconds")
    logging.info(f"Summary saved to: {output_path}")

if __name__ == "__main__":
    inspect_export("data/export.xml")