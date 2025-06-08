# src/tools/forecast_helpers.py

import pandas as pd
from datetime import timedelta
from src.tools.energy import calculate_age, calculate_rmr

def derive_dependent_metrics(weight, body_fat_percentage, age, sex):
    lean_mass = weight * (1 - body_fat_percentage)
    fat_mass = weight * body_fat_percentage
    rmr = calculate_rmr(weight, age, sex)
    return {
        "LeanBodyMass": lean_mass,
        "FatMass": fat_mass,
        "RMR": rmr
    }

def format_forecast_results(forecast: dict, df, target_metric: str, dob, sex: str, use_imperial: bool = False) -> list[str]:
    """
    Formats forecast results with optional derived metrics and unit conversion.

    Parameters:
        forecast (dict): {day_offset: predicted_value}.
        df (pd.DataFrame): Historical data including trend values.
        target_metric (str): e.g., "Weight".
        dob (datetime): Date of birth.
        sex (str): "male" or "female".
        use_imperial (bool): Whether to convert weight values to lbs.

    Returns:
        list[str]: Output lines for display or logging.
    """
    output_lines = []
    latest_row = df.dropna(subset=["TrendBodyFatPercentage", "TrendWeight", "date"]).iloc[-1]
    latest_date = latest_row["date"]
    base_weight = float(latest_row["TrendWeight"])
    body_fat_percentage = float(latest_row["TrendBodyFatPercentage"])

    for day_offset, predicted_value in forecast.items():
        try:
            predicted_value = float(predicted_value)
            forecast_date = latest_date + timedelta(days=day_offset)
            age = calculate_age(dob, forecast_date)
            used_weight = predicted_value if target_metric == "Weight" else base_weight

            derived = derive_dependent_metrics(
                weight=used_weight,
                body_fat_percentage=body_fat_percentage,
                age=age,
                sex=sex
            )

            # Primary value
            if use_imperial and target_metric in {"Weight", "LeanBodyMass"}:
                line = f"{day_offset} days: {predicted_value * 2.20462:.2f} lbs"
            else:
                line = f"{day_offset} days: {predicted_value:.2f}"
            output_lines.append(line)

            # Derived values for Weight forecasts
            if target_metric == "Weight":
                output_lines.extend([
                    f"  → Fat Mass: {derived['FatMass']:.2f} kg",
                    f"  → Lean Mass: {derived['LeanBodyMass']:.2f} kg",
                    f"  → RMR: {derived['RMR']:.0f} kcal/day"
                ])

        except Exception as e:
            output_lines.append(f"{day_offset} days: ERROR - {e}")

    return output_lines


def batch_derive_dependent_metrics(
    forecast_dict, df, target_metric, dob, sex
):
    """
    Compute derived metrics (RMR, LeanBodyMass, FatMass) for each forecasted day.
    """
    last_known = df.iloc[-1]
    results = {}

    for day, val in forecast_dict.items():
        if target_metric == "Weight":
            weight = val
            bf = last_known["TrendBodyFatPercentage"]
        elif target_metric == "BodyFatPercentage":
            weight = last_known["TrendWeight"]
            bf = val
        else:
            weight = last_known["TrendWeight"]
            bf = last_known["TrendBodyFatPercentage"]

        lean = weight * (1 - bf)
        fat = weight * bf
        future_date = last_known["date"] + pd.Timedelta(days=day)
        age = calculate_age(dob, future_date)
        rmr = calculate_rmr(weight, age, sex)

        results[day] = {
            target_metric: val,
            "LeanBodyMass": lean,
            "FatMass": fat,
            "RMR": rmr
        }

    return results

def add_trend_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the three *derived* trend columns exist.

    The function is **idempotent** – if a column is already present
    it is left untouched, so calling it multiple times is safe.

    Returns a *new* DataFrame (does not mutate the original in-place).
    """
    df = df.copy()

    if "TrendTDEE" not in df.columns:
        df["TrendTDEE"] = (
            df["TrendBasalCaloriesBurned"] + df["TrendActiveCaloriesBurned"]
        )

    if "TrendNetCalories" not in df.columns:
        # positive  => surplus, negative => deficit
        df["TrendNetCalories"] = df["TrendCaloriesIn"] - df["TrendTDEE"]

    if "TrendLeanBodyMass" not in df.columns:
        df["TrendLeanBodyMass"] = (
            df["TrendWeight"] * (1 - df["TrendBodyFatPercentage"])
        )

    return df