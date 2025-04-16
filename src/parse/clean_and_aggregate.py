import pandas as pd
import logging
from config.constants import (
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    MIN_DAYS_REQUIRED,
    MAX_MISSING_DAY_GAP,
    LBS_TO_KG
)

logger = logging.getLogger(__name__)


def clean_and_aggregate(parsed_data: dict, weight_unit: str) -> pd.DataFrame:
    """
    Cleans and aggregates Apple Health data.
    Handles required and optional metrics, applies unit conversions, and returns
    a daily dataframe suitable for modeling.
    """
    logger.info("Starting data cleaning and aggregation...")

    daily_frames = {}

    for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if column not in parsed_data:
            continue

        df = pd.DataFrame(parsed_data[column])
        if df.empty:
            continue

        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        # Apply conversion for weight if recorded in pounds
        if column == "Weight" and weight_unit.lower() == "lb":
            df["value"] = df["value"] * LBS_TO_KG
        elif column == "BodyFat" and df["value"].max() < 1.0:
            df["value"] = df["value"] * 100  # Convert fraction to percent

        # Daily average
        daily = df.groupby("date")["value"].mean().reset_index()
        daily.rename(columns={"value": column}, inplace=True)
        daily_frames[column] = daily

    if not daily_frames:
        raise ValueError("No valid metrics found in parsed data.")

    # Merge all daily frames
    merged_df = None
    for df in daily_frames.values():
        merged_df = df if merged_df is None else pd.merge(merged_df, df, on="date", how="outer")

    if merged_df is None or merged_df.empty:
        raise ValueError("No valid daily data found. Check your Health export for completeness.")

    merged_df.sort_values("date", inplace=True)
    merged_df.reset_index(drop=True, inplace=True)

    logger.info(f"Aggregated daily entries: {merged_df.shape[0]} days with data")
    return merged_df