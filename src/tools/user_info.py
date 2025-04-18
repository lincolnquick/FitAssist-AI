# src/tools/user_info.py
"""
user_info.py

This module handles user-specific information required for metabolic calculations
and personalized health analysis in the FitAssist-AI project. It provides functionality
to:

- Prompt the user for demographic and physical characteristics (date of birth, sex, height)
- Save and load this information from a standardized CSV file for reuse
- Compute the user’s age as a floating-point value in years, specific to any given date

This information supports downstream processes such as calculating Resting Metabolic Rate (RMR),
evaluating trends in basal calorie burn, and generating personalized predictions.

Typical usage:
    from src.tools.user_info import load_or_prompt_user_info, calculate_age

Author: Lincoln Quick  
"""
import os
import csv
from datetime import datetime
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

# Default path for user characteristics CSV
USER_CSV_PATH = "user_characteristics.csv"

def load_or_prompt_user_info(path: str = USER_CSV_PATH) -> dict:
    """
    Load user characteristics from a CSV file or prompt the user to enter them
    if the file does not exist.

    Parameters:
        path (str): Path to the user characteristics CSV file.

    Returns:
        dict: A dictionary containing 'dob', 'sex', and 'height_cm'.
    """
    if os.path.exists(path):
        logger.info(f"Loading user characteristics from: {path}")
        with open(path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            user_info = next(reader)
            user_info["height_cm"] = float(user_info["height_cm"])
            return user_info

    logger.info("User characteristics file not found. Prompting for input...")
    dob = input("Enter your date of birth (YYYY-MM-DD): ").strip()
    sex = input("Enter your biological sex ('male' or 'female'): ").strip().lower()
    height_cm = float(input("Enter your height in cm: ").strip())

    user_info = {
        "dob": dob,
        "sex": sex,
        "height_cm": height_cm
    }

    with open(path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=user_info.keys())
        writer.writeheader()
        writer.writerow(user_info)

    logger.info(f"User characteristics saved to: {path}")
    return user_info


def calculate_age(dob_str: str, reference_date: datetime) -> float:
    """
    Calculate age as a float given a date of birth and reference date.

    Parameters:
        dob_str (str): Date of birth in YYYY-MM-DD format.
        reference_date (datetime): The date to calculate age as of.

    Returns:
        float: Age in years (e.g., 33.52).
    """
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    delta_days = (reference_date - dob).days
    return delta_days / 365.25  # average year length with leap years