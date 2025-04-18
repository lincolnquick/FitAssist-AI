"""
Extract Metrics CLI for FitAssist AI

This command-line script orchestrates the pipeline for extracting, cleaning, and exporting
health metrics from an Apple Health XML export.

Pipeline:
1. Parses XML data to extract relevant metrics (weight, body fat, calories, etc.).
2. Cleans the parsed data:
   - Drops rows without CaloriesIn.
   - Interpolates missing weight-related fields with a gap limit.
   - Computes Total Daily Energy Expenditure (TDEE) and NetCalories.
3. Exports the cleaned data to a CSV file in the output directory.

Usage:
    python3 -m src.cli.extract_metrics [optional path/to/export.xml]

If no path is provided, it defaults to "data/export.xml".

Output:
    Saves cleaned and preprocessed data to: output/cleaned_metrics.csv
"""
import sys
import logging
from src.parse.parser import parse_health_metrics
from src.clean.clean_metrics import clean_metrics

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    # Determine path to XML export
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "data/export.xml"
    logger.info(f"Loading Apple Health export from: {xml_path}")

    # Parse metrics
    metrics = parse_health_metrics(xml_path)

    # Clean metrics
    cleaned_df = clean_metrics(metrics)

    # Export cleaned metrics to CSV
    output_path = "output/cleaned_metrics.csv"
    try:
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Cleaned metrics successfully saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save cleaned metrics: {e}")

if __name__ == "__main__":
    main()