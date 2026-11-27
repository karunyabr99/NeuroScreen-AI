"""
NeuroScreen AI - Paper 2 (2022) Random Forest Training Pipeline
Implements:
- RandomForestClassifier with configurable hyperparameters
- 3-fold Stratified Cross-Validation with leak-free preprocessing
- Independent holdout test set evaluation: ROC-AUC, AUPRC, Sensitivity, Specificity, F1, Confusion Matrix
- Gini feature importances
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold

from ml_engine.preprocessing import ClinicalDataPreprocessor
from ml_engine.model_evaluation import compute_clinical_metrics


class RandomForestTrainer:
    """
    Trains Random Forest classifier following Paper 2 (2022) methodology.
    """

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: Optional[int] = 6,
        min_samples_split: int = 4,
        random_seed: int = 42
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_seed = random_seed

    def train_and_evaluate(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        groups: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        y_train_arr = np.asarray(y_train).astype(int)
        y_test_arr = np.asarray(y_test).astype(int)

        # ---------------------------------------------------------------------
        # 1. 3-Fold Stratified Cross-Validation (Group-aware if groups passed)
        # ---------------------------------------------------------------------
        if groups is not None:
            from sklearn.model_selection import StratifiedGroupKFold
            skf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=self.random_seed)
            split_iter = skf.split(X_train, y_train_arr, groups=groups)
        else:
            skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=self.random_seed)
            split_iter = skf.split(X_train, y_train_arr)

        cv_metrics: List[Dict[str, Any]] = []

        for fold, (train_idx, val_idx) in enumerate(split_iter):
            X_tr, y_tr = X_train.iloc[train_idx], y_train_arr[train_idx]
            X_val, y_val = X_train.iloc[val_idx], y_train_arr[val_idx]

            fold_preprocessor = ClinicalDataPreprocessor(scale_numerical=False)
            X_tr_trans = fold_preprocessor.fit_transform(X_tr)
            X_val_trans = fold_preprocessor.transform(X_val)

            fold_model = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=self.random_seed + fold,
                n_jobs=-1
            )
            fold_model.fit(X_tr_trans, y_tr)

            val_probs = fold_model.predict_proba(X_val_trans)[:, 1]
            fold_metric = compute_clinical_metrics(y_val, val_probs, threshold=0.5)
            cv_metrics.append(fold_metric)

        cv_summary = {
            "folds": 3,
            "mean_roc_auc": round(float(np.mean([m["roc_auc"] for m in cv_metrics])), 4),
            "std_roc_auc": round(float(np.std([m["roc_auc"] for m in cv_metrics])), 4),
            "mean_auprc": round(float(np.mean([m["auprc"] for m in cv_metrics])), 4),
            "mean_sensitivity": round(float(np.mean([m["sensitivity"] for m in cv_metrics])), 4),
            "mean_specificity": round(float(np.mean([m["specificity"] for m in cv_metrics])), 4),
            "mean_f1": round(float(np.mean([m["f1_score"] for m in cv_metrics])), 4)
        }

        # ---------------------------------------------------------------------
        # 2. Final Model Fit on Full Training Set
        # ---------------------------------------------------------------------
        full_preprocessor = ClinicalDataPreprocessor(scale_numerical=False)
        X_train_trans = full_preprocessor.fit_transform(X_train)
        X_test_trans = full_preprocessor.transform(X_test)
        feature_names = full_preprocessor.get_feature_names_out()

        final_model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_seed,
            n_jobs=-1
        )
        final_model.fit(X_train_trans, y_train_arr)

        # Independent Holdout Test Evaluation
        test_probs = final_model.predict_proba(X_test_trans)[:, 1]
        test_metrics = compute_clinical_metrics(y_test_arr, test_probs, threshold=0.5, compute_ci=True)

        # Gini feature importances
        gini_importances = final_model.feature_importances_
        feature_importance_list = [
            {"feature": name, "importance": round(float(gini_importances[i]), 5)}
            for i, name in enumerate(feature_names)
        ]
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)

        training_duration = round(time.time() - start_time, 2)

        return {
            "model_name": "Random Forest (Paper 2, 2022)",
            "model_family": "Ensemble (RandomForestClassifier)",
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "min_samples_split": self.min_samples_split
            },
            "training_duration_seconds": training_duration,
            "cv_evaluation": cv_summary,
            "test_evaluation": test_metrics,
            "feature_names": feature_names,
            "feature_importance": feature_importance_list[:15],
            "final_model": final_model,
            "preprocessor": full_preprocessor
        }

