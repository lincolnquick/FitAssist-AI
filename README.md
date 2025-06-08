# FitAssist AI

**FitAssist AI** is a rule-augmented, ML-powered decision-support tool for personal health data.  
It parses an Apple Health export, cleans & visualises trends, forecasts future metrics, classifies weekly compliance, and enforces domain-safety rules through an interpretable first-order-logic watchdog.

This project is developed as part of the **CSC510: Foundations of Artificial Intelligence** portfolio at **Colorado State University Global**.

---

## Features

| Category | Highlights |
|----------|------------|
| **Parsing & Cleaning** | • Dedupes Apple Health records<br>• Smooths noisy metrics & fills gaps |
| **Visual Analytics** | • Auto-generated PNGs for full history / yearly / monthly views<br>• Summary & delta tables |
| **Machine Learning** | • XGBoost regression for multi-metric forecasting<br>• Persisted Naive-Bayes model classifies weekly state (`on_track`, `at_risk`, `off_track`) |
| **Hybrid Reasoning** | • First-order-logic watchdog layer (Horn clauses) enforcing:<br> — safe calorie floor<br> — rapid-loss/gain limits<br> — RMR sanity<br> — metabolic-adaptation plateaus<br> — goal-feasibility check |
| **Interactive CLI** | • Menu-driven forecast wizard<br>• Results logged to `output/forecast_session.txt` |
| **Fail-safe Demo Mode** | • If `data/export.xml` is missing, a bundled **`default.xml`** is substituted so the program always runs |

---

## Project Structure

```
FitAssist-AI/
├─ config/               # Constants (unit factors, safety thresholds, etc.)
├─ data/
│  ├─ export.xml         # your real Apple Health export (optional)
│  ├─ default.xml        # demo data shipped with repo
│  ├─ cleaned_metrics.csv
│  └─ user_characteristics.csv
├─ output/               # Plots, reports, forecast logs
├─ src/
│  ├─ analyze/           # descriptive stats, correlations
│  ├─ classify/          # Naïve-Bayes model + trainer
│  ├─ cli/               # extraction pipeline
│  ├─ predict/           # XGB forecasting
│  ├─ watchdog/          # FOL rules, dispatcher, feature builder
│  └─ tools/             # utilities (energy eqns, user prompts, …)
├─ run.py                # ――― main entry point ―――
└─ REQUIREMENTS.txt
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

## Using the Forecast Wizard
```
--- Forecast Menu ---
1. Weight
2. CaloriesIn
3. TDEE
...

Select a metric by name or number (q to quit): 1
Enter forecast days (e.g., 90 or [7,14,30]): [7,14,30,90]
```
Daily predictions plus derived RMR and body composition stats are printed to `output/forecast_session.txt`

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

 ---

## Safety & Watchdog FOL

| Rule Code | Trigger Condition |
|----------|------------|
| UnsafeIntake | any day < 1200 kcal |
| RapidWeightLoss | Weekly weight change < -2 kg |
| RapidWeightGain | Weekly weight change > +2 kg |
| LowRMR | calculated RMR < 1000 kcal/day |
| MetabolicAdapt | adaptation > 8% |
| GoalNotReached / GoalTimingDrift | forecast misses or drifts from goal |
| MismatchDeficit | consistency checks |
| StaleData, etc. | data-quality checks |

Critical rules escalate the compliance state to `OFF_TRACK` even if the model predicts otherwise.

## License

This project is licensed under the [MIT License](./LICENSE).

## Disclaimer

This project is intended for academic and experimental use only. It is not a substitute for professional medical or dietary advice.


