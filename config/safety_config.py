# config/safety_config.py

# This file contains tunable thresholds and settings used across the FitAssist AI project.
# Modify these values to customize safety thresholds and modeling behaviors.

# Minimum number of valid records required for modeling
MINIMUM_VALID_RECORDS = 30

# Maximum allowable gap (in days) between logged entries before raising a warning
MAX_ALLOWED_LOGGING_GAP_DAYS = 7

# Safe human weight range (kg) for inclusion in modeling
MIN_WEIGHT_KG = 30
MAX_WEIGHT_KG = 300

# Safe caloric intake range (kcal/day)
MIN_CALORIES_IN = 500
MAX_CALORIES_IN = 7000

# Safe caloric expenditure range (kcal/day)
MIN_CALORIES_OUT = 0
MAX_CALORIES_OUT = 10000

# Weight unit conversion
KG_TO_LBS = 2.20462