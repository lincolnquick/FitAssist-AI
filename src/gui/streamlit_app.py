"""
Main Streamlit interface for FitAssist-AI.
Launch with: streamlit run src/gui/streamlit_app.py
"""

import streamlit as st
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from data.load_data import load_cleaned_metrics
from src.gui.tabs.summary_tab import render_summary_tab
from src.gui.tabs.visualization_tab import render_visualization_tab
from src.gui.tabs.correlation_tab import render_correlation_tab
from src.gui.tabs.forecasting_tab import render_forecasting_tab

def main():
    st.set_page_config(page_title="FitAssist AI", layout="wide")
    st.title("FitAssist AI Dashboard")

    df = load_cleaned_metrics()

    tabs = {
        "Summary": render_summary_tab,
        "Visualizations": render_visualization_tab,
        "Correlations": render_correlation_tab,
        "Forecasting": render_forecasting_tab,
    }

    selected_tab = st.sidebar.radio("Select a tab", list(tabs.keys()))
    tabs[selected_tab](df)  # Call the selected function with df

if __name__ == "__main__":
    main()