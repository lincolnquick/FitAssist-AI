import streamlit as st
from src.tools.gui_wrappers import generate_and_load_plots
from datetime import datetime

def render_visualization_tab(df):
    st.header("Visualize Metrics by Group and Time")

    # Time period selector
    period = st.selectbox("Select Time Period", ["full", "year", "month"])
    use_imperial = st.checkbox("Use Imperial Units (e.g., lbs)", value=False)

    period_label = "full"
    filter_label = None  # Used for filtering plots later

    if period == "year":
        years = df["date"].dt.year.dropna().unique().astype(int)
        year_options = ["All"] + sorted([str(y) for y in years], reverse=True)
        selected_year = st.selectbox("Select Year", year_options)
        if selected_year != "All":
            filter_label = selected_year
        period_label = "year"

    elif period == "month":
        df["YearMonth"] = df["date"].dt.to_period("M")
        months = sorted(df["YearMonth"].unique().astype(str), reverse=True)
        month_options = ["All"] + months
        selected_month = st.selectbox("Select Month", month_options)
        if selected_month != "All":
            filter_label = selected_month
        period_label = "month"

    # Generate plots for the selected period type
    plot_groups = generate_and_load_plots(df, [period_label], use_imperial)

    for group_name, image_list in plot_groups.items():
        with st.expander(f"{group_name.title()} Metrics"):
            cols = st.columns(2)

            # Filter image list based on selected label
            filtered_images = [
                (name, img) for name, img in image_list
                if filter_label is None or filter_label in name
            ]

            for i, (img_name, img_obj) in enumerate(filtered_images):
                with cols[i % 2]:
                    st.image(img_obj, caption=img_name, use_container_width=True)