"""
plot_forecast.py

Generates a line plot of predicted weight over time.

Author: Lincoln Quick
"""

import matplotlib.pyplot as plt
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def plot_forecast(forecast: dict, output_dir: str = "output") -> str:
    """
    Plots the weight forecast over time.

    Args:
        forecast (dict): Dictionary mapping day offsets (int) to predicted weights (float).
        output_dir (str): Directory where the plot will be saved.

    Returns:
        str: Path to saved plot image.
    """
    if not forecast:
        logger.error("No forecast data to plot.")
        return ""

    # Prepare data
    df = pd.DataFrame(list(forecast.items()), columns=["Day", "PredictedWeight"])
    df.sort_values("Day", inplace=True)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(df["Day"], df["PredictedWeight"], marker="o", linestyle="-", linewidth=2)
    plt.title("Predicted Weight Forecast (30/60/90 Days)")
    plt.xlabel("Days from Today")
    plt.ylabel("Weight (kg)")
    plt.grid(True)
    plt.tight_layout()

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, "weight_forecast.png")
    plt.savefig(plot_path)
    plt.close()

    logger.info(f"Saved forecast plot to {plot_path}")
    return plot_path