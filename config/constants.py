"""
Configuration constants for FitAssist AI.
This file stores required fields, safety thresholds, and other tunable values
used throughout the pipeline.
"""

# Required fields for training and predictions
REQUIRED_COLUMNS = ["Weight", "CaloriesIn", "CaloriesOut"]

# Optional fields we support if present
OPTIONAL_COLUMNS = [
    "BasalCaloriesOut",
    "StepCount",
    "BodyFat",
    "LeanBodyMass",
    "DistanceWalkingRunning"
]

# Minimum number of days of data required to attempt modeling
MIN_DAYS_REQUIRED = 30

# Maximum allowed consecutive missing days (in the cleaned series)
MAX_MISSING_DAY_GAP = 7

# Default weight unit
DEFAULT_WEIGHT_UNIT = "kg"

# Minimum and maximum safe calorie intake (can be used in goal evaluations)
SAFE_MIN_CALORIES = 1200  # kcal/day
SAFE_MAX_WEIGHT_LOSS_RATE = 2.0  # lbs/week
SAFE_MAX_WEIGHT_GAIN_RATE = 2.0  # lbs/week

# Unit conversions
LBS_TO_KG = 0.453592
KG_TO_LBS = 2.20462