"""
Summary Tab: Displays full table of health data and descriptive statistics.
"""

import streamlit as st
import pandas as pd

def render_summary_tab(df: pd.DataFrame):
    st.header("Summary Statistics")

    st.subheader("Full Dataset (Scroll to Explore)")
    st.dataframe(df, use_container_width=True, height=500)

    st.subheader("Descriptive Statistics")
    numeric_df = df.select_dtypes(include="number")
    st.dataframe(numeric_df.describe().transpose(), use_container_width=True)