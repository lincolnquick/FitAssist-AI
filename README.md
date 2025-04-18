# FitAssist AI

**FitAssist AI** is a predictive health forecasting system powered by AI techniques. It analyzes Apple Health export data to visualize trends, forecast future metrics like weight or TDEE, and identify meaningful correlations between calorie balance, activity, and body composition. The system supports user-driven forecasting of any supported metric and logs predictions to a session file for review.

This project is developed as part of the **CSC510: Foundations of Artificial Intelligence** portfolio at **Colorado State University Global**.

---

## Features

- Parses and deduplicates Apple Health export XML data.
- Calculates and smooths daily metrics such as:
  - Total Daily Energy Expenditure (TDEE)
  - Net Calories (Calories In – TDEE)
  - Basal and Active Calories Burned
  - Step Count and Distance
- Visualizes data across full history, calendar years, and months.
- Generates descriptive summaries, including deltas and rolling statistics.
- Analyzes correlations across all metrics and their trends.
- Estimates caloric efficiency (kcal per pound of weight lost).
- Detects changes in body composition over time.
- Trains XGBoost models for:
  - Weight change prediction
  - Generalized forecasting of any metric (e.g., LeanBodyMass, TDEE)
- Forecasts over custom time intervals or spans (e.g., 90 days or [7, 14, 30, 60]).
- Logs all forecast results to `output/forecast_session.txt`.

---

## Project Structure

```
FitAssist-AI/
├── config/                     # Constants and thresholds (e.g., unit conversions)
├── data/                       # Input files (Apple Health export.xml, user info)
│   ├── export.xml              # Apple Health data (not included in repo)
│   ├── cleaned_metrics.csv     # Output from parser pipeline
│   └── user_characteristics.csv # DOB, height, biological sex
├── milestones/                 # Weekly milestone documentation
├── output/                     # Generated visualizations, reports, forecast logs
│   ├── plots/                  # PNG plots by metric and period
│   ├── summary_report.txt      # Descriptive statistics output
│   ├── correlation_report.txt  # Ranked metric correlations
│   ├── caloric_efficiency.csv  # kcal/lb summary
│   ├── forecast_session.txt    # All user forecasts this session
│   └── composition_analysis.png/csv # Lean/Fat trends
├── src/                        # Source modules
│   ├── analyze/                # Descriptive stats, correlations, efficiency
│   ├── clean/                  # Smoothing and imputation of missing values
│   ├── cli/                    # Pipeline scripts (e.g., extract_metrics)
│   ├── modeling/               # XGBoost regression training
│   ├── parse/                  # Apple Health XML parsing
│   ├── predict/                # Forecasting logic (weight and general metrics)
│   ├── tools/                  # Utility modules (e.g., user info, energy)
│   └── visualize/              # Plot generation
├── tests/                      # Unit tests (WIP)
├── run.py                      # Main script to run full analysis + forecasting
├── README.md                   # This file
├── LICENSE
└── REQUIREMENTS.txt            # Python dependencies
```
---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Pip or a virtual environment tool (e.g., `venv`)

### Clone the Repository

```bash
cd ~/Projects
git clone https://github.com/lincolnquick/FitAssist-AI.git
cd FitAssist-AI
```

### Set Up a Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
```

## Usage

### Step 1: Export Data from Apple Health
1. Open the Health app on your iPhone.
2. Tap your profile photo > Export All Health Data.
3. AirDrop or transfer the `export.zip` to your Mac, unzip it, and place `export.xml` into the `data/` directory.

> **Important:** Do not commit this file to GitHub. It is excluded by `.gitignore`.

---

### Step 2: Run FitAssist AI


####  Run the main script (`run.py`)

```bash
python run.py
```

## Usage Overview

Upon running run.py, the system will:
 - Detect if Apple Health data has changed and reprocess if needed.
 - Ensure user profile is defined (height, sex, DOB).
 - Generate plots, summary statistics, correlations, and caloric efficiency.
 - Prompt you to forecast a health metric.

You can:
 - Enter a metric name or number (e.g., Weight or 8).
 - Enter a single number (e.g., 90) to predict daily for the next 90 consecutive days.
 - Enter a list (e.g., [7,14,30,60]) to forecast specific intervals.

All predictions are logged to output/forecast_session.txt.

⸻

### Example Forecast Interaction
```bash
Enter the metric to forecast (e.g., Weight or 8): 8
Enter days to forecast (e.g., 30 or [7,14,30]): 90
```
Outputs:
 - Daily predictions from Day 1 to Day 90
 - Features used in training
 - R^2 score of the model
 - Appends forecast to session log

## Portfolio Milestones

| Week | Deliverable            | File                                      | Due Date |
|------|------------------------|-------------------------------------------|---------|
| 2    | Use-Case Scenario      | `milestones/milestone_02_use_case.md`     | 2025-04-27 |
| 3    | Neural Networks        | `milestones/milestone_03_neural_networks.md` | 2025-05-04 |
| 4    | Intelligent Search     | `milestones/milestone_04_search_methods.md` | 2025-05-11 |
| 5    | Classification         | `milestones/milestone_05_classification.md` | 2025-05-18 |
| 6    | First-Order Logic      | `milestones/milestone_06_first_order_logic.md` | 2025-05-25 |
| 8    | Final Submission       | `milestones/final_report.md` | 2025-06-08 |

## License

This project is licensed under the [MIT License](./LICENSE).

## Disclaimer

This project is intended for academic and experimental use only. It is not a substitute for professional medical or dietary advice.

