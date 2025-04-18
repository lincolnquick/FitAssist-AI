from itertools import combinations
import os
import pandas as pd
import numpy as np

output_dir = "output"
correlation_csv = os.path.join(output_dir, "correlation_summary.csv")
correlation_txt = os.path.join(output_dir, "correlation_report.txt")


def correlate_metrics(df: pd.DataFrame, output_dir: str) -> list[str]:
    """
    Compute Pearson correlation coefficients between all reasonable combinations of numeric health metrics.
    Prefers trend-based or delta metrics if available. Saves full correlation results to CSV and
    top correlations (by absolute value) to a human-readable text file.

    Parameters:
        df (pd.DataFrame): Cleaned and smoothed health metrics.
        output_dir (str): Path to save output files.

    Returns:
        list[str]: Top 10 correlation summary lines sorted by absolute r-value.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Use only numeric columns
    numeric_df = df.select_dtypes(include=[np.number]).copy()

    # Prefer trend columns if available
    for col in list(numeric_df.columns):
        if not col.startswith("Trend") and f"Trend{col}" in numeric_df.columns:
            numeric_df.drop(columns=[col], inplace=True)

    corr_pairs = []
    for col1, col2 in combinations(numeric_df.columns, 2):
        series1 = numeric_df[col1].dropna()
        series2 = numeric_df[col2].dropna()
        combined = pd.concat([series1, series2], axis=1, join='inner').dropna()

        if len(combined) >= 2:
            r = combined.corr(method="pearson").iloc[0, 1]
            corr_pairs.append({
                "Metric1": col1,
                "Metric2": col2,
                "Correlation": r,
                "AbsCorrelation": abs(r)
            })

    corr_df = pd.DataFrame(corr_pairs).sort_values(by="AbsCorrelation", ascending=False)
    corr_df.to_csv(correlation_csv, index=False)

    summary_lines = ["\n--- Strongest Correlation of Metrics ---"]
    top = corr_df.head(10)
    for _, row in top.iterrows():
        summary_lines.append(f"{row['Metric1']} vs {row['Metric2']}: r = {row['Correlation']:.3f}")

    # Save full correlation report
    with open(correlation_txt, "w") as f:
        f.write("--- Correlation Report (All Metrics) ---\n\n")
        for _, row in corr_df.iterrows():
            f.write(f"{row['Metric1']} vs {row['Metric2']}: r = {row['Correlation']:.3f}\n")

    return summary_lines
