import pandas as pd
import logging
from collections import defaultdict
from config.constants import (
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    MIN_DAYS_REQUIRED,
    MAX_MISSING_DAY_GAP,
    LBS_TO_KG,
    REQUIRED_METRICS,
    OPTIONAL_METRICS,
)

logger = logging.getLogger(__name__)

def clean_and_aggregate(parsed_data: dict, weight_unit: str = "kg") -> pd.DataFrame:
    data = parsed_data.get("data", {})
    
    if not data:
        raise ValueError("No valid metrics found in parsed data (empty 'data').")

    logger.debug(f"Available record types in parsed data: {list(data.keys())}")

    # Convert to DataFrames per metric
    metric_dfs = {}
    for metric, entries in data.items():
        if entries:
            df = pd.DataFrame(entries)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            metric_dfs[metric] = df.dropna()
    
    # Group and average values per date
    daily_agg = defaultdict(dict)

    # Handle required metrics
    for label, hk_type in REQUIRED_METRICS.items():
        if hk_type not in metric_dfs:
            logger.error(f"Missing required metric: {label} ({hk_type})")
            continue
        df = metric_dfs[hk_type]
        for date, group in df.groupby("date"):
            daily_agg[date][label] = group["value"].mean()

    # Handle optional metrics
    for label, hk_type in OPTIONAL_METRICS.items():
        if hk_type not in metric_dfs:
            continue
        df = metric_dfs[hk_type]
        for date, group in df.groupby("date"):
            daily_agg[date][label] = group["value"].mean()

    # Convert to DataFrame
    if not daily_agg:
        raise ValueError("No valid metrics found in parsed data.")

    daily_df = pd.DataFrame.from_dict(daily_agg, orient="index").sort_index()
    daily_df.index.name = "date"
    daily_df.reset_index(inplace=True)

    # Convert units
    if weight_unit == "lb":
        daily_df["Weight"] = daily_df["Weight"] * LBS_TO_KG
        if "LeanBodyMass" in daily_df:
            daily_df["LeanBodyMass"] = daily_df["LeanBodyMass"] * LBS_TO_KG

    # Derived metrics
    daily_df["CaloriesOut"] = daily_df.get("CaloriesOut", 0) + daily_df.get("BasalCaloriesOut", 0)
    daily_df["NetCalories"] = daily_df["CaloriesIn"] - daily_df["CaloriesOut"]

    # Filter out days missing required fields
    valid_df = daily_df.dropna(subset=REQUIRED_COLUMNS)
    logger.info(f"Aggregated daily entries: {len(valid_df)} days with data")

    if valid_df.empty or len(valid_df) < MIN_DAYS_REQUIRED:
        raise ValueError("Not enough valid data for modeling.")

    return valid_df