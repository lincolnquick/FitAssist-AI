# src/parse/clean_and_aggregate.py

import pandas as pd
import logging
from typing import Dict

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def clean_and_aggregate(records: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    logging.info("Starting data cleaning and aggregation...")

    # Standardize and process each dataframe
    for key in records:
        df = records[key].copy()
        if df.empty:
            logging.warning(f"No data found for {key}")
            continue

        # Use startDate or creationDate if available
        df["timestamp"] = pd.to_datetime(df["startDate"] if "startDate" in df.columns else df["creationDate"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        df["date"] = df["timestamp"].dt.date
        records[key] = df

    # Daily aggregation
    weight_daily = records["Weight"].sort_values("timestamp").groupby("date")["value"].last().rename("Weight")
    intake_daily = records["DietaryEnergyConsumed"].groupby("date")["value"].sum().rename("CaloriesIn")
    burn_daily = records["ActiveEnergyBurned"].groupby("date")["value"].sum().rename("CaloriesOut")

    # Merge all into one daily dataframe
    daily = pd.concat([weight_daily, intake_daily, burn_daily], axis=1).dropna(how="all")

    logging.info(f"Aggregated daily entries: {len(daily)} days with data")

    return daily.reset_index().rename(columns={"index": "Date"})