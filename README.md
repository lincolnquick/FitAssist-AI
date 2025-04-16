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
├── data/                     # Apple Health XML exports (excluded from version control)
├── src/                      # Source code modules
│   ├── parse/                # XML parser for Apple Health data
│   ├── modeling/             # Weight prediction and metabolic modeling
│   ├── logic/                # Symbolic planning and goal evaluation
│   └── cli/                  # Command-line interface
├── milestones/               # Weekly milestone markdown files
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

1. Export your health data from Apple Health on iPhone.
2. Place the `export.xml` file inside the `data/` directory.
3. Run the CLI tool (WIP):
   ```bash
   python src/cli/main.py
   ```

*Note: Do not commit Apple Health exports to version control. They are automatically excluded via `.gitignore`.*

## Portfolio Milestones

| Week | Deliverable           | File                                      |
|------|------------------------|-------------------------------------------|
| 2    | Use-Case Scenario      | `milestones/milestone_02_use_case.md`     |
| 3    | Neural Networks        | `milestones/milestone_03_neural_networks.md` *(TBD)* |
| 4    | Intelligent Search     | `milestones/milestone_04_search_methods.md` *(TBD)* |
| 5    | Classification         | `milestones/milestone_05_classification.md` *(TBD)* |
| 6    | First-Order Logic      | `milestones/milestone_06_first_order_logic.md` *(TBD)* |
| 8    | Final Submission       | `milestones/final_report.md` *(TBD)* |

## License

This project is licensed under the [MIT License](./LICENSE).

## Disclaimer

This project is intended for academic and experimental use only. It is not a substitute for professional medical or dietary advice.
