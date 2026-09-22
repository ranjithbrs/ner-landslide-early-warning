"""
Model Training, Cross-Validation, Evaluation, and Serialization for Landslide Risk.
Follows ML Best Practices:
- Strict featurization ordering (split before fit)
- Multiple model comparisons: Naive baseline vs Logistic Regression vs Random Forest
- Comprehensive evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix)
- Feature importance analysis and serialization of model artifacts
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline

from backend.ml_engine.synthetic_generator import generate_synthetic_ner_dataset
from backend.ml_engine.pipeline import (
    build_preprocessor,
    extract_feature_matrix,
    ALL_MODEL_FEATURES,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
)


def evaluate_model_pipeline(name: str, pipeline: Pipeline, X_test: pd.DataFrame, y_test: np.ndarray) -> Dict[str, Any]:
    """Evaluates a fitted pipeline on the holdout test set and computes standardized metrics."""
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else y_pred.astype(float)

    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_name": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": cm,
    }
    return metrics


def train_and_evaluate_models(
    n_samples: int = 6000,
    test_size: float = 0.20,
    random_state: int = 42,
    output_dir: str = "backend/ml_engine/models",
    data_dir: str = "data",
) -> Dict[str, Any]:
    """
    Full ML training workflow:
    1. Generates prototype dataset
    2. Splits into Train and Test sets
    3. Builds and compares:
       - Baseline 1: Dummy (Majority Class)
       - Baseline 2: Logistic Regression
       - Target Model: Random Forest Classifier
    4. Evaluates and exports serialized pipeline and metadata
    """
    print("=" * 70)
    print("NER LANDSLIDE RISK PREDICTION - MACHINE LEARNING PIPELINE")
    print("=" * 70)

    # 1. Dataset Generation
    print(f"[*] Generating synthetic geomorphic and meteorological dataset (n={n_samples})...")
    df = generate_synthetic_ner_dataset(n_samples=n_samples, random_seed=random_state)
    
    raw_path = Path(data_dir) / "raw" / "ner_landslide_simulated_dataset.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)
    print(f"    Saved raw dataset to: {raw_path}")

    # 2. Train / Test Split (Strict featurization ordering: split BEFORE fitting)
    X, y = extract_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Save train/test partitions for reproducibility
    proc_dir = Path(data_dir) / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    X_train.assign(landslide_occurred=y_train).to_csv(proc_dir / "train_data.csv", index=False)
    X_test.assign(landslide_occurred=y_test).to_csv(proc_dir / "test_data.csv", index=False)
    print(f"    Train samples: {len(X_train)} (Positives: {y_train.sum()})")
    print(f"    Test samples:  {len(X_test)} (Positives: {y_test.sum()})")

    # 3. Model 1: Naive Baseline (Dummy Classifier)
    print("\n[*] Training Model 1: Naive Baseline (Majority Class)...")
    dummy_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", DummyClassifier(strategy="most_frequent")),
    ])
    dummy_pipe.fit(X_train, y_train)
    dummy_metrics = evaluate_model_pipeline("Naive Baseline (Majority)", dummy_pipe, X_test, y_test)
    print(f"    Accuracy: {dummy_metrics['accuracy']:.4f} | F1: {dummy_metrics['f1_score']:.4f} | ROC-AUC: {dummy_metrics['roc_auc']:.4f}")

    # 4. Model 2: Linear ML Baseline (Logistic Regression)
    print("\n[*] Training Model 2: Linear Baseline (Logistic Regression)...")
    lr_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", LogisticRegression(max_iter=1000, random_state=random_state)),
    ])
    lr_cv_scores = cross_val_score(lr_pipe, X_train, y_train, cv=5, scoring="roc_auc")
    lr_pipe.fit(X_train, y_train)
    lr_metrics = evaluate_model_pipeline("Logistic Regression", lr_pipe, X_test, y_test)
    print(f"    CV 5-fold ROC-AUC: {lr_cv_scores.mean():.4f} (+/- {lr_cv_scores.std():.4f})")
    print(f"    Test Accuracy: {lr_metrics['accuracy']:.4f} | F1: {lr_metrics['f1_score']:.4f} | ROC-AUC: {lr_metrics['roc_auc']:.4f}")

    # 5. Model 3: Primary Ensemble (Random Forest Classifier)
    print("\n[*] Training Model 3: Random Forest Classifier...")
    rf_classifier = RandomForestClassifier(
        n_estimators=120,
        max_depth=14,
        min_samples_split=6,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    rf_pipe = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", rf_classifier),
    ])
    rf_cv_scores = cross_val_score(rf_pipe, X_train, y_train, cv=5, scoring="roc_auc")
    rf_pipe.fit(X_train, y_train)
    rf_metrics = evaluate_model_pipeline("Random Forest Classifier", rf_pipe, X_test, y_test)
    print(f"    CV 5-fold ROC-AUC: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std():.4f})")
    print(f"    Test Accuracy: {rf_metrics['accuracy']:.4f} | F1: {rf_metrics['f1_score']:.4f} | ROC-AUC: {rf_metrics['roc_auc']:.4f}")
    print(f"    Precision: {rf_metrics['precision']:.4f} | Recall: {rf_metrics['recall']:.4f}")

    # 6. Extract Feature Importances
    preprocessor = rf_pipe.named_steps["preprocessor"]
    classifier = rf_pipe.named_steps["classifier"]
    
    # Get encoded feature names
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = NUMERICAL_FEATURES + cat_feature_names
    
    importances = classifier.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    feature_ranking = [
        {"feature": all_feature_names[i], "importance": round(float(importances[i]), 4)}
        for i in sorted_idx
    ]

    print("\n[*] Top 8 Most Critical Landslide Predictor Features:")
    for rank, item in enumerate(feature_ranking[:8], 1):
        print(f"    {rank}. {item['feature']:<30} {item['importance']*100:.2f}%")

    # 7. Model Serialization
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_file = out_dir / "landslide_rf_model.joblib"
    joblib.dump(rf_pipe, model_file)
    print(f"\n[*] Serialized trained model pipeline to: {model_file}")

    metadata = {
        "model_type": "RandomForestClassifier",
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "source": "Synthetically generated prototype calibrated for NER terrain",
            "total_samples": n_samples,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "target": TARGET_COLUMN,
            "positive_ratio": round(float(y.mean()), 4),
        },
        "model_comparison": {
            "naive_baseline": dummy_metrics,
            "logistic_regression": {
                **lr_metrics,
                "cv_roc_auc_mean": round(float(lr_cv_scores.mean()), 4),
                "cv_roc_auc_std": round(float(lr_cv_scores.std()), 4),
            },
            "random_forest": {
                **rf_metrics,
                "cv_roc_auc_mean": round(float(rf_cv_scores.mean()), 4),
                "cv_roc_auc_std": round(float(rf_cv_scores.std()), 4),
            },
        },
        "feature_importances": feature_ranking,
        "features": {
            "numerical": NUMERICAL_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "all_features": all_feature_names,
        },
    }

    meta_file = out_dir / "model_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[*] Saved model evaluation metadata to: {meta_file}")

    return metadata


if __name__ == "__main__":
    train_and_evaluate_models()
