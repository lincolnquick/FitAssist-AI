"""
Configuration constants for FitAssist AI.

This module centralizes tunable parameters for parsing, cleaning, and modeling
Apple Health data.
"""

# HealthKit -> internal metric name mapping
TARGET_METRICS = {
    "HKQuantityTypeIdentifierBodyMass": "Weight",
    "HKQuantityTypeIdentifierLeanBodyMass": "LeanBodyMass",
    "HKQuantityTypeIdentifierBodyFatPercentage": "BodyFatPercentage",
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": "CaloriesIn",
    "HKQuantityTypeIdentifierBasalEnergyBurned": "BasalCaloriesBurned",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "ActiveCaloriesBurned",
    "HKQuantityTypeIdentifierStepCount": "StepCount",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "DistanceWalkingRunning",
}

# Metrics that should be summed over the day
SUM_METRICS = {
    "CaloriesIn",
    "BasalCaloriesBurned",
    "ActiveCaloriesBurned",
    "StepCount",
    "DistanceWalkingRunning",
}

# Metrics that should be averaged if multiple entries exist
AVERAGE_METRICS = {
    "Weight",
    "LeanBodyMass",
    "BodyFatPercentage",
}

# Prioritization for overlapping records (used for deduplication)
SOURCE_PRIORITY = {
    "Apple Watch": 3,
    "iPhone": 2,
    "default": 1,  # Third-party or unknown devices
}

# Columns required for modeling
REQUIRED_COLUMNS = ["date", "Weight" ,"BodyFatPercentage", "LeanBodyMass",
                    "StepCount", "DistanceWalkingRunning", "BasalCaloriesBurned", 
                    "ActiveCaloriesBurned", "CaloriesIn"]

# Columns that are computed from other metrics
COMPUTED_COLUMNS = ["TDEE", "NetCalories"]

# Optional fields used in visualization or extended metrics
OPTIONAL_COLUMNS = [
    "BasalCaloriesBurned",
    "StepCount",
    "BodyFatPercentage",
    "LeanBodyMass",
    "DistanceWalkingRunning",
]

# Interpolation / modeling thresholds
MIN_DAYS_REQUIRED = 30
MAX_MISSING_DAY_GAP = 7

# Unit conversions
LBS_TO_KG = 0.453592
KG_TO_LBS = 2.20462
M_TO_KM = 0.001

# Default unit if none detected
DEFAULT_WEIGHT_UNIT = "kg"

# ────────────────────────────────────────────────────────────────
# Safety / Watch-dog thresholds
# ────────────────────────────────────────────────────────────────
SAFE_MIN_CALORIES         = 1200     # kcal / day
SAFE_MAX_WEIGHT_LOSS_RATE = 2.0      # kg / week
SAFE_MAX_WEIGHT_GAIN_RATE = 2.0      # kg / week

RMR_FLOOR   = 1000      # kcal / day  
ADAPT_THRESH = 0.08     # 8 % drop in RMR triggers “adaptation” rule
GAP_THRESH   = 5        # kg above goal before we warn


# Suggested additional constants (not yet used but might be useful):
# - MAX_INTERPOLATION_DAYS = 14
# - PREFERRED_METRIC_SOURCES = ["Apple Watch", "iPhone"]