"""
plot_utils.py

Utility functions for plotting metrics over time for the FitAssist-AI GUI.
"""

import matplotlib.pyplot as plt
import pandas as pd

def plot_metric_over_time(df: pd.DataFrame, metric: str, time_span: str = "All Time"):
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])  # Ensure datetime format
        df = df.set_index("Date")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must be indexed by datetime for time-based plotting.")

    series = df[metric].dropna()

    # Resample for aggregation
    if time_span == "Yearly":
        series = series.resample("Y").mean()
    elif time_span == "Monthly":
        series = series.resample("M").mean()
    elif time_span == "Weekly":
        series = series.resample("W-MON").mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(series.index, series.values, marker='o', linestyle='-')
    ax.set_title(f"{metric} Over Time ({time_span})")
    ax.set_xlabel("Date")
    ax.set_ylabel(metric)
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig