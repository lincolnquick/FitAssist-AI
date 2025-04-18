"""
Correlation Tab: Shows a heatmap of correlations between health metrics.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render_correlation_tab(df: pd.DataFrame):
    st.header("Metric Correlation Heatmap")

    # Filter for numeric columns
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.warning("No numeric columns available for correlation analysis.")
        return

    st.markdown("This heatmap shows the Pearson correlation between all numeric metrics.")

    corr = numeric_df.corr()

    # Dynamically size the figure
    num_vars = len(corr.columns)
    fig_width = max(8, min(2 + num_vars * 0.5, 24))
    fig_height = max(6, min(2 + num_vars * 0.5, 24))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        square=True,
        cbar_kws={"shrink": 0.75},
        ax=ax
    )

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    ax.set_title("Correlation Matrix", fontsize=14, pad=12)

    st.pyplot(fig)