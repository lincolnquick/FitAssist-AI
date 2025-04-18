# src/tools/energy.py
"""
energy.py

Provides energy-related physiological calculations for the FitAssist-AI project.

This module includes:
- Resting Metabolic Rate (RMR) calculation using the Livingston-Kohlstadt formula
- Caloric imbalance estimation based on changes in fat and lean mass
- Precise age calculation in years from date of birth to a target date

Intended for use in model prediction, analysis, and personalization tools.

Author: Lincoln Quick
"""

from datetime import datetime

# Constants from Thomas et al. (2010)
CF = 1020  # kcal/kg for fat-free mass (lean)
CL = 9500  # kcal/kg for fat mass

# RMR constants for Livingston-Kohlstadt formula (kcal/day)
RMR = {
    "male": {"c": 293, "p": 0.433, "y": 5.92},
    "female": {"c": 248, "p": 0.4356, "y": 5.09}
}

def calculate_rmr(weight: float, age: float, sex: str, a: float = 0) -> float:
    """
    Calculate Resting Metabolic Rate (RMR) in kcal/day.

    Parameters:
        weight (float): Weight in kg
        age (float): Age in years (float, accurate to day)
        sex (str): 'male' or 'female'
        a (float): Optional metabolic adaptation factor (0 ≤ a ≤ 1)

    Returns:
        float: RMR in kcal/day
    """
    c, p, y = RMR[sex].values()
    rmr = (1 - a) * c * (max(weight, 0) ** p) - y * age
    return max(rmr, 0)

def calculate_age(dob: datetime, target_date: datetime) -> float:
    """
    Calculate precise age in years between dob and target_date.

    Parameters:
        dob (datetime): Date of birth
        target_date (datetime): Date to calculate age at

    Returns:
        float: Age in years
    """
    delta_days = (target_date - dob).days
    return delta_days / 365.25

def estimate_caloric_imbalance(delta_fm: float, delta_ffm: float) -> float:
    """
    Estimate the caloric imbalance required to achieve given changes in mass.

    Parameters:
        delta_fm (float): Change in fat mass (kg)
        delta_ffm (float): Change in fat-free mass (kg)

    Returns:
        float: Estimated net caloric imbalance (kcal)
    """
    return (delta_fm * CL) + (delta_ffm * CF)