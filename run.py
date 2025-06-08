"""
run.py

Main entry point for analyzing, visualizing, and forecasting health metrics from Apple Health data.

Performs:
1. User info validation and loading
2. Conditional data extraction from Apple Health export
3. Visualization and analysis
4. Forecasting with derived metric interpretation

Author: Lincoln Quick
"""

import os
import ast
import glob
import logging
import subprocess
from datetime import datetime
import shutil

from data.load_data import load_cleaned_metrics
from src.tools.user_info import load_or_prompt_user_info
from src.visualize.plot_metrics import plot_metrics
from src.analyze.describe_data import describe_data
from src.analyze.correlate_metrics import correlate_metrics
from src.analyze.body_composition import analyze_body_composition
from src.predict.forecast_metric import forecast_metric
from src.tools.goal_info import load_or_prompt_goal
from src.classify.compliance_nb import predict_weekly_state, MODEL_PATH
from src.classify.train_compliance_nb import main as train_nb
from src.watchdog.dispatcher import run_watchdog
from src.tools.forecast_helpers import add_trend_columns, batch_derive_dependent_metrics
from config.constants import KG_TO_LBS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def file_is_fresher(newer: str, older: str) -> bool:
    return os.path.exists(newer) and (
        not os.path.exists(older) or os.path.getmtime(newer) > os.path.getmtime(older)
    )

def plots_are_fresh(plot_dir: str, data_path: str) -> bool:
    if not os.path.exists(data_path):
        return False
    data_mtime = os.path.getmtime(data_path)
    plot_files = glob.glob(os.path.join(plot_dir, "**", "*.png"), recursive=True)
    return all(os.path.getmtime(p) <= data_mtime for p in plot_files)

def run_extraction():
    logger.info("Running data extraction pipeline from Apple Health export...")
    try:
        subprocess.run(["python", "-m", "src.cli.extract_metrics"], check=True)
        logger.info("Extraction complete.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Extraction failed: {e}")
        raise

def main():
    data_dir = "data"
    output_dir = "output"
    plot_dir = os.path.join(output_dir, "plots")
    csv_path = os.path.join(data_dir, "cleaned_metrics.csv")
    export_path = os.path.join(data_dir, "export.xml")
    default_path = os.path.join(data_dir, "default.xml")
    user_info_path = os.path.join(data_dir, "user_characteristics.csv")
    goal_info_path = os.path.join(data_dir, "goal_info.csv")

    use_imperial = True
    plot_periods = ["full", "year", "month"]

    # ---------- Load or prompt for user characterists: DOB, sex, height ----------
    user_info = load_or_prompt_user_info(user_info_path)
    if not user_info:
        logger.error("Unable to load user characteristics.")
        return

    # ---------- Ensure Apple Health data exists ----------
    if not os.path.exists(export_path):
        if os.path.exists(default_path):
            logger.warning(
                "No export.xml found – using bundled default.xml demo data.\n"
                "➡  To use your own data: on your iPhone open Health → "
                "profile photo → Export Health Data, unzip the file, and place "
                "export.xml in the data/ folder, then rerun."
            )
            # copy demo file to the canonical name so the extractor can find it
            shutil.copy2(default_path, export_path)      # <── NEW LINE
        else:
            logger.error(
                "Missing Apple Health export: data/export.xml\n"
                "Place your own export.xml (see instructions above) and rerun."
            )
            return
    
    # ---------- Load or Prompt user for goal ----------
    goal = load_or_prompt_goal(goal_info_path, use_imperial=True)
    logger.info(f"User goal: {goal['weight_kg']*KG_TO_LBS:.2f} lbs by {goal['date']}")

    # ---------- Refresh cleaned_metrics.csv if needed ----------
    if file_is_fresher(export_path, csv_path):
        logger.info("New export.xml detected. Re-running extraction.")
        os.environ["FITASSIST_USER_INFO"] = str(user_info)
        run_extraction()

    try:
        df = load_cleaned_metrics(csv_path)
        df = add_trend_columns(df)
        dob = datetime.strptime(user_info["dob"], "%Y-%m-%d")
        sex = user_info["sex"].lower()

        # ---------- Visualization ----------
        if plots_are_fresh(plot_dir, csv_path):
            logger.info("Plots up to date. Skipping generation.")
        else:
            logger.info("Generating visualizations...")
            plot_metrics(df, output_dir=plot_dir, periods=plot_periods, use_imperial_units=use_imperial)

        # ---------- Description ----------
        logger.info("Running summary analysis...")
        summary_lines = describe_data(df, output_dir)
        for line in summary_lines:
            print(line)

        # ---------- Correlation ----------
        logger.info("Generating correlation matrix...")
        corr_lines = correlate_metrics(df, output_dir)
        for line in corr_lines:
            print(line)

        # ---------- Body Composition Trends ----------
        analyze_body_composition(df)

        # ───────────────────── Classification  +  Watch-dog ──────────────────────
        # 1. train NB model on first run
        if not MODEL_PATH.exists():
            logger.info("NB model absent - training on current dataset …")
            train_nb()

        # 2. Naive-Bayes weekly compliance prediction
        nb_out = predict_weekly_state(df)           # {'state', 'proba', 'weeks'}

        # 3. rule-based watchdog (returns a list of (code, -) tuples)
        wd_alerts = run_watchdog(df, dob, sex, goal_info=goal)

        # 4. combine: escalate NB state when a critical alert is raised
        final_state = nb_out["state"]
        CRITICAL = {"UnsafeIntake", "RapidWeightLoss", "RapidWeightGain", "LowRMR"}
        if any(code in CRITICAL for code, *_ in wd_alerts):
            final_state = "off_track"
        elif any(code == "MetabolicAdapt" for code, *_ in wd_alerts):
            # plateau / adaptation is serious but not as critical
            final_state = "at_risk"

        # 5. console report -------------------------------------------------------
        print("\n--- Weekly Compliance Classification ---")
        if nb_out["state"] == "unknown":
            print(f"Only {nb_out['weeks']} weeks of data available - need ≥4 to classify.")
        else:
            p_on, p_risk, p_off = nb_out["proba"]
            print(f"NB state            : {nb_out['state'].upper()}  "
                f"(on={p_on*100:4.1f}%, risk={p_risk*100:4.1f}%, off={p_off*100:4.1f}%)")
            print(f"Watch-dog final     : {final_state.upper()}")

            if wd_alerts:
                print("Rule triggers:")
                for tup in wd_alerts:
                    code = tup[0]
                    msg  = tup[-1]      # message is always the last element
                    print(f" • {code}: {msg}")
            else:
                print("No watchdog rules fired.")
        # ─────────────────────────────────────────────────────────────────────────
        # ---------- Forecasting ----------
        logger.info("Launching CLI forecast module...")

        forecast_log_path = os.path.join(output_dir, "forecast_session.txt")
        forecast_log_lines = []

        available_trends = [col for col in df.columns if col.startswith("Trend")]
        base_metrics = sorted(set(col.replace("Trend", "") for col in available_trends))

        while True:
            print("\n--- Forecast Menu ---")
            for i, m in enumerate(base_metrics, 1):
                print(f"{i}. {m}")

            choice = input("\nSelect a metric by name or number (q to quit): ").strip()
            if choice.lower() == "q":
                break
            selected = None
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(base_metrics):
                    selected = base_metrics[index]
            elif choice in base_metrics:
                selected = choice

            if not selected:
                logger.warning("Invalid selection.")
                continue

            days_input = input("Enter forecast days (e.g., 30 or [7,14,30]): ").strip()
            try:
                forecast_days = ast.literal_eval(days_input) if "[" in days_input else list(range(1, int(days_input)+1))
            except:
                logger.warning("Invalid forecast day input.")
                continue

            try:
                forecast, features, r2 = forecast_metric(df, selected, forecast_days, dob, sex)
                # Compute derived fields for each forecasted day
                derived = batch_derive_dependent_metrics(forecast, df, selected, dob, sex)

                print(f"\nForecast for {selected}")
                for day in forecast_days:
                    row = derived[day]
                    line = f"{day} days: "
                    line += ", ".join(f"{k}={v:.2f}" for k, v in row.items())
                    print(line)
                    forecast_log_lines.append(line)

                forecast_log_lines.append(f"Top features: {', '.join(features)}")
                forecast_log_lines.append(f"Model R² score: {r2:.3f}\n")

            except Exception as e:
                logger.error(f"Forecasting failed: {e}")

        if forecast_log_lines:
            with open(forecast_log_path, "w") as f:
                f.write("\n".join(forecast_log_lines))
            logger.info(f"Forecast session saved to: {forecast_log_path}")

    except Exception as e:
        logger.error(f"CLI failed: {e}")

if __name__ == "__main__":
    main()