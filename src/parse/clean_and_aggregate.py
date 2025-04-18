import pandas as pd
from collections import defaultdict
import logging
from config.constants import (
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    MIN_DAYS_REQUIRED,
    MAX_MISSING_DAY_GAP,
    LBS_TO_KG,
    M_TO_KM,
    REQUIRED_METRICS,
    OPTIONAL_METRICS,
)

logger = logging.getLogger(__name__)


def clean_and_aggregate(parsed_data: dict, weight_unit: str = "kg") -> pd.DataFrame:
    data = parsed_data
    if not data:
        raise ValueError("No valid metrics found in parsed data (empty 'data').")

    logger.info("Starting data cleaning and aggregation...")

    # Step 1: Normalize entries and drop duplicates
    metric_dfs = {}
    for metric, entries in data.items():
        try:
            df = pd.DataFrame(entries)
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df.dropna(subset=["date", "value"], inplace=True)
            df.drop_duplicates(subset=["date", "value"], inplace=True)
            metric_dfs[metric] = df
        except Exception as e:
            logger.warning(f"Skipping metric {metric} due to error: {e}")

    # Step 2: Aggregate values per day
    daily_agg = defaultdict(dict)

    def aggregate_metric(df, label):
        for date, group in df.groupby("date"):
            if str(date.date()) in {"2025-04-13", "2025-04-14", "2025-04-15"}:
                logger.debug(f"[AGGREGATE] {label} on {date.date()}: "
                            f"entries={len(group)}, values={group['value'].tolist()}, "
                            f"{'mean' if label in ['Weight', 'BodyFat', 'LeanBodyMass'] else 'sum'}={daily_agg[date][label]}")
            daily_agg[date][label] = group["value"].mean()

    for hk_type, label in REQUIRED_METRICS.items():
        if hk_type not in metric_dfs:
            logger.error(f"Missing required metric: {label} ({hk_type})")
            continue
        aggregate_metric(metric_dfs[hk_type], label)

    for hk_type, label in OPTIONAL_METRICS.items():
        if hk_type not in metric_dfs:
            logger.info(f"Optional metric not found: {label}")
            continue
        aggregate_metric(metric_dfs[hk_type], label)

    if not daily_agg:
        raise ValueError("No valid metrics found in parsed data.")

    daily_df = pd.DataFrame.from_dict(daily_agg, orient="index").sort_index()
    daily_df.index.name = "date"
    daily_df.reset_index(inplace=True)

    # Step 3: Unit conversions
    if weight_unit == "lb":
        if "Weight" in daily_df.columns and daily_df["Weight"].mean() > 130:
            daily_df["Weight"] *= LBS_TO_KG
        if "LeanBodyMass" in daily_df.columns and daily_df["LeanBodyMass"].mean() > 130:
            daily_df["LeanBodyMass"] *= LBS_TO_KG

    if "DistanceWalkingRunning" in daily_df.columns:
        daily_df["DistanceWalkingRunning"] *= M_TO_KM

    # Step 4: Derived fields
    daily_df["CaloriesOut"] = (
        daily_df[["CaloriesOut", "BasalCaloriesOut"]]
        .fillna(0)
        .sum(axis=1)
    )
    daily_df["NetCalories"] = daily_df["CaloriesIn"] - daily_df["CaloriesOut"]

    # Step 5: Interpolate missing weights
    daily_df = daily_df.sort_values("date")
    if "Weight" in daily_df.columns:
        daily_df.set_index("date", inplace=True)
        missing_before = daily_df["Weight"].isna().sum()
        daily_df["Weight"] = daily_df["Weight"].interpolate(method="time", limit_direction="both")
        missing_after = daily_df["Weight"].isna().sum()
        daily_df.reset_index(inplace=True)
        logger.info(f"Interpolated Weight: {missing_before - missing_after} values filled")

    # Step 6: Final cleanup
    valid_df = daily_df.dropna(subset=REQUIRED_COLUMNS)
    logger.info(f"Valid modeling rows: {len(valid_df)} / {len(daily_df)}")
    logger.info(f"Aggregated daily entries: {len(valid_df)} days with data")

    if valid_df.empty or len(valid_df) < MIN_DAYS_REQUIRED:
        raise ValueError("Not enough valid data for modeling.")

    # Step 7: Export cleaned data
    output_path = "output/cleaned_data.csv"
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data exported to {output_path}")

    return valid_df