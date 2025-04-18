import xml.etree.ElementTree as ET
from datetime import datetime
import os

def trim_apple_health_export(input_path: str, output_path: str, year: int, month: int):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Trimming Apple Health export for {year}-{month:02d}...")

    new_root = ET.Element("HealthData")
    context = ET.iterparse(input_path, events=("start", "end"))
    context = iter(context)
    _, root = next(context)

    count = 0
    for event, elem in context:
        if event == "end" and elem.tag == "Record":
            start_date = elem.get("startDate")
            if start_date:
                try:
                    record_date = datetime.strptime(start_date[:10], "%Y-%m-%d")
                    if record_date.year == year and record_date.month == month:
                        # Copy attributes manually
                        new_elem = ET.Element("Record", attrib=elem.attrib.copy())
                        new_root.append(new_elem)
                        count += 1
                except Exception:
                    pass
            elem.clear()

    print(f"Copied {count} records to trimmed file.")

    tree = ET.ElementTree(new_root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

# Example usage
if __name__ == "__main__":
    trim_apple_health_export(
        input_path="data/export.xml",
        output_path="data/export_april_2025.xml",
        year=2025,
        month=4
    )