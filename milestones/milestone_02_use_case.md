# Milestone 2: Use-Case Scenario

**Project Title:**  
FitAssist AI – Predictive Weight Forecasting and Personalized Goal Planning

**Student:**  
Lincoln Quick

**Course:**  
CSC510 – Foundations of Artificial Intelligence  
Colorado State University Global

**Instructor:**  
Dr. Luis Gonzalez

**Date:**  
April 15, 2025

---

## 1. Problem Statement

Weight loss tools often fail to provide personalized or realistic expectations, leaving users frustrated by slow progress or unachievable goals. Most fitness apps track behavior but do not project outcomes or account for adaptive metabolic responses. As individuals diet or increase exercise, their bodies adjust through reductions in NEAT (non-exercise activity thermogenesis), the thermic effect of food (TEF), and exercise efficiency. These changes decrease total energy expenditure over time, making static calorie-based recommendations less effective. To address these issues, this project introduces **FitAssist AI**, a Python-based decision support system that models future weight change, simulates adaptive metabolic response, and provides goal-aligned, safe, and actionable feedback based on user health data.

---

## 2. Actors

| Actor             | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| **User**         | Individual providing Apple Health data and defining target weight goals.     |
| **FitAssist AI** | Python application that parses health data, forecasts outcomes, evaluates goals, and provides recommendations. |

---

## 3. Goals

- Predict user’s future weight change over time intervals (e.g., 30, 60, and 90 days).
- Allow users to define desired weight and a target timeline.
- Assess whether user-defined goals are realistic and within safe limits.
- If goals are not on track, suggest feasible changes in caloric intake or physical activity.
- Simulate metabolic adaptation to ensure forecasts reflect real physiological responses.

---

## 4. Inputs

- **User Health Data** (from Apple Health XML):
  - Weight history
  - Caloric intake
  - Active energy (calories burned)
  - Steps and activity minutes
- **User Goal Input**:
  - Target weight
  - Target date or timeframe

---

## 5. Outputs

- Weight change predictions over the next 30, 60, and 90 days.
- Estimated average caloric intake and expenditure over those periods.
- Feasibility analysis of the goal based on safety and guidelines.
- Recommended changes if predicted weight does not align with user-defined goals:
  - Suggested caloric intake and/or activity adjustments.
  - Alternative safe timeline to reach goal.
- Retrospective model validation: use historical data to simulate predictions and compare against actual outcomes.

---

## 6. AI Methods Used

| Method              | Use Case                                                                 |
|---------------------|--------------------------------------------------------------------------|
| Regression Modeling | Forecast weight trends from past intake, output, and weight changes.     |
| Knowledge Representation | Encode safety rules (e.g., 1–2 lbs/week loss, minimum calorie levels). |
| First-Order Logic   | Apply safety checks and logic to goal evaluations.                       |
| Symbolic Planning   | Suggest daily/weekly behavior adjustments if predicted path deviates.    |
| Intelligent Search  | Find optimal intervention strategies to help users reach their goals.    |
| Neural Networks (optional) | Refine predictions or identify nonlinear behavior from historical data. |

---

## 7. Success Criteria

- Use partial historical data to predict future outcomes (e.g., use data from 1 year ago to 6 months ago, then validate against real data from 6 months ago to today).
- Provide accurate weight change projections using real Apple Health data.
- Correctly identify whether a user-defined goal is feasible and healthy.
- Deliver safe, actionable feedback with realistic timelines and energy balance adjustments.

---

## 8. Limitations and Assumptions

| Limitation              | Explanation                                                              |
|-------------------------|--------------------------------------------------------------------------|
| Data Quality            | Accuracy depends on completeness of Apple Health export.                 |
| Physiological Assumptions | Simplified metabolic model based on Hall and Thomas approximations.     |
| Prediction Range        | Less accuracy for long-term projections due to data variability.         |
| User Compliance         | Recommendations assume user will follow changes consistently.            |

---

## 9. Summary

**FitAssist AI** bridges the gap between passive health tracking and intelligent guidance. By using historical Apple Health data, adaptive modeling, and core AI techniques, it forecasts likely outcomes and recommends appropriate, user-aligned adjustments. The system is designed to educate users on realistic expectations while helping them safely reach their weight goals through informed, data-driven strategies.

---

## References

- Hall, K. D., Sacks, G., Chandramohan, D., Chow, C. C., Wang, Y. C., Gortmaker, S. L., & Swinburn, B. A. (2011). Quantification of the effect of energy imbalance on bodyweight. *The Lancet, 378*(9793), 826–837.

- Thomas, D. M., Martin, C. K., Heymsfield, S., Redman, L. M., Schoeller, D. A., & Levine, J. A. (2011). A simple model predicting individual weight change in humans. *Journal of Biological Dynamics, 5*(6), 579–599.