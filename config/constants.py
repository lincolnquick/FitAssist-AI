"""
Configuration constants for FitAssist AI.
This file stores required fields, safety thresholds, and other tunable values
used throughout the pipeline.
"""

# Required metric types parsed from Apple Health data
REQUIRED_METRICS = {
    "HKQuantityTypeIdentifierBodyMass": "Weight",
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": "CaloriesIn",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "ActiveCaloriesOut",
    "HKQuantityTypeIdentifierBasalEnergyBurned": "BasalCaloriesOut"
}

# Optional metrics that may be useful for future modeling or analysis
OPTIONAL_METRICS = {
    "HKQuantityTypeIdentifierBodyFatPercentage": "BodyFat",
    "HKQuantityTypeIdentifierLeanBodyMass": "LeanBodyMass",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "DistanceWalkingRunning",
    "HKQuantityTypeIdentifierStepCount": "StepCount"
}

# Required columns in final DataFrame for modeling
REQUIRED_COLUMNS = ["Weight", "CaloriesIn", "CaloriesOut"]

# Optional columns to pass through if available
OPTIONAL_COLUMNS = [
    "BasalCaloriesOut",
    "StepCount",
    "BodyFat",
    "LeanBodyMass",
    "DistanceWalkingRunning"
]

# Minimum number of days of data required to attempt modeling
MIN_DAYS_REQUIRED = 30

# Maximum allowed consecutive missing days in daily time series
MAX_MISSING_DAY_GAP = 7

# Default weight unit (fallback)
DEFAULT_WEIGHT_UNIT = "kg"

# Safety constraints
SAFE_MIN_CALORIES = 1200  # kcal/day
SAFE_MAX_WEIGHT_LOSS_RATE = 2.0  # lbs/week
SAFE_MAX_WEIGHT_GAIN_RATE = 2.0  # lbs/week

# Unit conversions
LBS_TO_KG = 0.453592
KG_TO_LBS = 2.20462