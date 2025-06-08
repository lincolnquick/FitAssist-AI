# ────────────────────────────────────────────────────────────────
# src/classify/train_compliance_nb.py
#
# Train a weekly-compliance Naïve Bayes model for FitAssist-AI
# and persist it to src/classify/compliance_nb.pkl
# ────────────────────────────────────────────────────────────────
from __future__ import annotations

from pathlib import Path
import pickle

import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from src.classify.compliance_nb import (
    _prepare_weekly_features,
    CLASSES,
    MODEL_PATH,
)

# ----------------------------------------------------------------
# 1.  Load *any* cleaned daily-metrics CSV files you want to use
#     as labelled training data.  The more, the better.
#     One file per subject is fine – just append them.
# ----------------------------------------------------------------
DATA_FILES = [
    "data/cleaned_metrics.csv",  # you can add more paths here
]

# ----------------------------------------------------------------
# 2.  For a quick demo we’ll fabricate labels from weight
#     change and caloric deficit.  In production you would
#     manually label each week or use an external study dataset.
# ----------------------------------------------------------------
def label_week(row: pd.Series) -> str:
    if row["wt_change"] < -0.3 and row["mean_net_cal"] < -250:
        return "on_track"
    if row["wt_change"] > 0.3 and row["mean_net_cal"] > 250:
        return "off_track"
    return "at_risk"


def main() -> None:
    # ────────────────────────────────
    # Aggregate *all* data to week-level
    # ────────────────────────────────
    weekly_frames = []
    for fp in DATA_FILES:
        df = pd.read_csv(fp, parse_dates=["date"])
        wk = _prepare_weekly_features(df)
        weekly_frames.append(wk)

    weekly_all = pd.concat(weekly_frames, ignore_index=True)

    # ────────────────────────────────
    # Attach synthetic labels
    # ────────────────────────────────
    weekly_all["target"] = weekly_all.apply(label_week, axis=1)

    X = weekly_all[["mean_net_cal", "mean_pa", "wt_change"]].values
    y = weekly_all["target"].values

    # Consistent ordering of class indices
    gnb = GaussianNB()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, test_size=0.2, random_state=0
    )
    gnb.fit(X_train, y_train)

    print("▸ Validation on held-out 20 %:")
    print(classification_report(y_test, gnb.predict(X_test), labels=CLASSES, zero_division=0))

    # ────────────────────────────────
    # Persist model next to compliance_nb.py
    # ────────────────────────────────
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as fh:
        pickle.dump(gnb, fh)

    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()