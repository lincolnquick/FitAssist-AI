"""
Forecasting Tab: Predict future values for a selected metric using XGBoost.
"""

import streamlit as st
import pandas as pd
from src.predict.forecast_metric import forecast_metric
from config.constants import KG_TO_LBS


def render_forecasting_tab(df: pd.DataFrame):
    st.header("Forecast Future Health Metrics")

    if "date" not in df.columns:
        st.error("The input data must include a 'date' column.")
        return

    # Metric selection
    candidate_metrics = [
        col for col in df.columns
        if col.startswith("Trend") and not col.endswith("_Delta")
    ]

    if not candidate_metrics:
        st.warning("No trend metrics found for forecasting.")
        return

    selected_metric = st.selectbox("Select a metric to forecast", candidate_metrics)

    # Units and forecast options
    use_imperial = st.checkbox("Display mass in pounds (lbs)", value=False)
    span_days = st.slider("Forecast how many days ahead?", min_value=1, max_value=365, value=30)
    window_size = st.slider("Rolling window size", 7, 60, 21, step=7)
    top_n_features = st.slider("Top correlated features to use", 1, 10, 5)

    if st.button("Generate Forecast"):
        try:
            forecast_day_list = list(range(1, span_days + 1))

            predictions, features_used, r2_score = forecast_metric(
                df=df,
                target_metric=selected_metric.replace("Trend", ""),
                forecast_days=forecast_day_list,
                window=window_size,
                top_n_features=top_n_features
            )

            # Prepare output
            last_date = pd.to_datetime(df["date"].max())
            forecast_dates = [last_date + pd.Timedelta(days=d) for d in forecast_day_list]
            forecast_values = [predictions[d] for d in forecast_day_list]

            if use_imperial and any(m in selected_metric for m in ["Weight", "LeanBodyMass"]):
                forecast_values = [v * KG_TO_LBS for v in forecast_values]

            label = f"Forecasted {selected_metric}"
            if use_imperial and "Mass" in selected_metric:
                label += " (lbs)"
            elif "Mass" in selected_metric:
                label += " (kg)"

            result_df = pd.DataFrame({
                "Date": forecast_dates,
                label: forecast_values
            }).set_index("Date")

            

            # Add recent trend before predicted
            historical = df[["date", selected_metric]].dropna().tail(30).copy()
            historical = historical.set_index("date")

            # Convert to lbs if applicable
            if use_imperial and any(keyword in selected_metric for keyword in ["Weight", "Mass"]):
                historical[selected_metric] *= KG_TO_LBS

            # Combine and plot
            combined = pd.concat([historical, result_df])
            st.line_chart(combined)

            # Display
            st.subheader("Forecasted Trend")
            st.line_chart(result_df)
            st.dataframe(result_df)

            st.markdown(f"**Top features used:** {', '.join(features_used)}")
            st.markdown(f"**Training R² score:** `{r2_score:.3f}`")

        except Exception as e:
            st.error(f"Forecast generation failed: {e}")