"""
Train and benchmark multiple machine learning models for Email Fraud & Phishing Detection.
Evaluates:
- Multinomial Naive Bayes
- Logistic Regression (with calibrated probabilities and L2 regularization)
- Linear Support Vector Machine (with CalibratedClassifierCV)
- Random Forest Classifier

Saves:
- models/best_fraud_detector.joblib
- outputs/fraud_model_comparison.csv
- outputs/fraud_best_model_classification_report.csv
- outputs/fraud_best_model_confusion_matrix.csv
- outputs/fraud_top_keywords.csv
- outputs/fraud_sample_predictions.csv
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "fraud_detection_dataset.csv"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def train_and_evaluate():
    print("=" * 65)
    print("TRAINING & BENCHMARKING EMAIL FRAUD / PHISHING DETECTORS")
    print("=" * 65)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH).dropna(subset=["text", "label"])
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(int)

    print(f"Total dataset size: {len(df):,} samples")
    print(f"Class distribution:\n{df['label_name'].value_counts().to_string()}\n")

    # 80/20 Stratified Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.20,
        random_state=42,
        stratify=df["label"]
    )

    print(f"Training set: {len(X_train):,} samples")
    print(f"Held-out test set: {len(X_test):,} samples\n")

    # Shared TF-IDF Vectorizer parameters
    # Sublinear TF dampens effect of repeated words; (1, 2) n-grams capture phrases like 'click here'
    tfidf_params = dict(
        sublinear_tf=True,
        max_df=0.85,
        min_df=3,
        ngram_range=(1, 2),
        stop_words="english",
        max_features=20000
    )

    candidates = {
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.1),
        "Logistic Regression": LogisticRegression(C=2.0, max_iter=1000, random_state=42),
        "Linear SVM (Calibrated)": CalibratedClassifierCV(
            estimator=LinearSVC(C=1.0, random_state=42, dual=False, max_iter=2000),
            cv=3
        ),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=30, random_state=42, n_jobs=-1)
    }

    comparison_rows = []
    trained_pipelines = {}
    test_predictions = {}
    test_probabilities = {}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, clf in candidates.items():
        print(f"--> Training and evaluating: {name}...")
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(**tfidf_params)),
            ("clf", clf)
        ])

        # 5-Fold Cross Validation on Train Split
        scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]
        cv_res = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)

        # Fit on full training set
        pipeline.fit(X_train, y_train)
        trained_pipelines[name] = pipeline

        # Evaluate on Held-out Test Set
        y_pred = pipeline.predict(X_test)
        test_predictions[name] = y_pred

        if hasattr(pipeline, "predict_proba"):
            y_proba = pipeline.predict_proba(X_test)[:, 1]
        else:
            y_proba = pipeline.decision_function(X_test)
        test_probabilities[name] = y_proba

        test_acc = accuracy_score(y_test, y_pred)
        test_prec = precision_score(y_test, y_pred)
        test_rec = recall_score(y_test, y_pred)
        test_f1 = f1_score(y_test, y_pred)
        test_auc = roc_auc_score(y_test, y_proba)

        comparison_rows.append({
            "model": name,
            "cv_accuracy_mean": round(float(np.mean(cv_res["test_accuracy"])), 4),
            "cv_f1_mean": round(float(np.mean(cv_res["test_f1"])), 4),
            "test_accuracy": round(float(test_acc), 4),
            "test_precision": round(float(test_prec), 4),
            "test_recall": round(float(test_rec), 4),
            "test_f1": round(float(test_f1), 4),
            "test_roc_auc": round(float(test_auc), 4),
        })

    comparison_df = pd.DataFrame(comparison_rows).sort_values(by="test_f1", ascending=False)
    comparison_path = OUTPUT_DIR / "fraud_model_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)

    print("\n" + "=" * 65)
    print("MODEL COMPARISON RESULTS (ON HELD-OUT TEST SET)")
    print("=" * 65)
    print(comparison_df.to_string(index=False))

    best_model_name = comparison_df.iloc[0]["model"]
    best_pipeline = trained_pipelines[best_model_name]
    best_preds = test_predictions[best_model_name]
    best_probas = test_probabilities[best_model_name]

    print(f"\n★ Best Performing Model: {best_model_name}")

    # Save Best Model
    best_model_path = MODEL_DIR / "best_fraud_detector.joblib"
    joblib.dump(best_pipeline, best_model_path)
    print(f"Saved best model pipeline to: {best_model_path}")

    # Classification Report
    target_names = ["Legitimate", "Fraudulent"]
    report_dict = classification_report(y_test, best_preds, target_names=target_names, output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose().round(4)
    report_path = OUTPUT_DIR / "fraud_best_model_classification_report.csv"
    report_df.to_csv(report_path)

    print("\nDetailed Classification Report:")
    print(classification_report(y_test, best_preds, target_names=target_names))

    # Confusion Matrix
    cm = confusion_matrix(y_test, best_preds)
    cm_df = pd.DataFrame(
        cm,
        index=["Actual_Legitimate", "Actual_Fraudulent"],
        columns=["Predicted_Legitimate", "Predicted_Fraudulent"]
    )
    cm_path = OUTPUT_DIR / "fraud_best_model_confusion_matrix.csv"
    cm_df.to_csv(cm_path)
    print("Confusion Matrix:")
    print(cm_df)

    # Extract Top Predictive Features (Keywords / Phrases)
    # Using Logistic Regression pipeline or Best Model's vectorizer
    lr_pipe = trained_pipelines.get("Logistic Regression", best_pipeline)
    vec = lr_pipe.named_steps["tfidf"]
    classifier = lr_pipe.named_steps.get("clf")

    if hasattr(classifier, "coef_"):
        feature_names = np.array(vec.get_feature_names_out())
        coefs = classifier.coef_[0]

        top_fraud_idx = np.argsort(coefs)[-30:][::-1]
        top_legit_idx = np.argsort(coefs)[:30]

        keywords_df = pd.DataFrame({
            "top_fraud_indicators": feature_names[top_fraud_idx],
            "fraud_weight": coefs[top_fraud_idx],
            "top_legitimate_indicators": feature_names[top_legit_idx],
            "legitimate_weight": -coefs[top_legit_idx]
        })
        keywords_path = OUTPUT_DIR / "fraud_top_keywords.csv"
        keywords_df.to_csv(keywords_path, index=False)
        print("\nTop Fraud vs Legitimate Keywords saved to:", keywords_path)

    # Sample Predictions for Human Inspection
    test_df = df.iloc[X_test.index].copy()
    test_df["predicted_label"] = best_preds
    test_df["predicted_status"] = np.where(best_preds == 1, "Fraudulent", "Legitimate")
    test_df["fraud_confidence_pct"] = (best_probas * 100).round(1)
    test_df["correct"] = test_df["label"] == test_df["predicted_label"]

    # Select representative samples
    samples = []
    # 5 True Negatives (Correct Legitimate)
    tn_samples = test_df[(test_df["label"] == 0) & (test_df["correct"])].head(4)
    # 5 True Positives (Correct Fraudulent)
    tp_samples = test_df[(test_df["label"] == 1) & (test_df["correct"])].head(4)
    # Any false positives / false negatives if present
    err_samples = test_df[~test_df["correct"]].head(2)

    sample_output_df = pd.concat([tn_samples, tp_samples, err_samples]).copy()
    sample_output_df["email_snippet"] = sample_output_df["text"].str[:180] + "..."
    sample_cols = [
        "source", "label_name", "predicted_status", "fraud_confidence_pct", "correct", "email_snippet"
    ]
    sample_path = OUTPUT_DIR / "fraud_sample_predictions.csv"
    sample_output_df[sample_cols].to_csv(sample_path, index=False)
    print(f"Sample test predictions saved to: {sample_path}")

    print("\n" + "=" * 65)
    print("ALL TRAINING & EVALUATION TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    train_and_evaluate()
