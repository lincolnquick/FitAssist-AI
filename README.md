# FitAssist AI

**FitAssist AI** is a predictive weight forecasting and personalized goal planning assistant. It uses AI techniques to analyze health data exported from Apple Health and predict future weight trends. The system adjusts for metabolic adaptation—such as reduced non-exercise activity thermogenesis (NEAT), decreased thermic effect of food (TEF), and improved exercise efficiency—and recommends actionable strategies for reaching user-defined goals in a safe and realistic manner.

This project is developed as part of the **CSC510: Foundations of Artificial Intelligence** portfolio at **Colorado State University Global**.

---

## Features

- Predict weight change over 30, 60, and 90-day intervals
- Simulate adaptive metabolic changes over time
- Accept user-defined weight goals and timelines
- Evaluate goal feasibility based on current trends
- Recommend personalized adjustments to diet and activity
- Use symbolic logic, intelligent search, and AI modeling

---

## Project Structure

```
FitAssist-AI/
|── config/                   # Configuration constants, safety thresholds, etc.
├── data/                     # Apple Health XML exports (excluded from version control)
├── milestones/               # Weekly milestone markdown files
├── output/                   # Output files from execution for testing
├── src/                      # Source code modules
│   ├── parse/                # XML parser for Apple Health data
│   ├── modeling/             # Weight prediction and metabolic modeling
│   ├── logic/                # Symbolic planning and goal evaluation
│   ├── tools/                # Tools used for planning project
│   └── cli/                  # Command-line interface
├── tests/                    # Unit tests
├── .gitignore                # Excludes sensitive and unnecessary files
├── LICENSE                   # MIT License
├── README.md                 # Project overview
└── REQUIREMENTS.txt          # Python dependencies
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

From the project root, activate your virtual environment:

```bash
source venv/bin/activate
```
Then run the main run script:
```bash
python run.py
```

This script will:
- Parse your Apple Health data
- Aggregate daily values
- Predict future weight trends based on net calorie balance
- Prompot you for a target weight and date
- Evaluate whether your goal is on track and display results

### Example Output

```bash
=== FitAssist AI ===
Loading Apple Health data...
Training model...
MAE: 1.23 kg
Enter your target weight (kg): 72
Enter your target date (YYYY-MM-DD): 2025-07-01

Predicted weight on 2025-07-01: 74.3 kg
Your goal: 72.0 kg
You're predicted to be 2.3 kg above your goal.
```

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
