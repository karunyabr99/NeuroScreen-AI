"""
NeuroScreen AI - Paper 1 (2024) CatBoost Training Pipeline
Implements:
- 3-fold Stratified Cross-Validation
- Preprocessing fitted strictly on training folds to prevent data leakage
- Youden's J threshold optimization (T*) derived strictly on validation predictions
- Evaluation on independent holdout test set
- Genuine SHAP explanations via shap.TreeExplainer
"""

import time
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import StratifiedKFold
import shap

from ml_engine.preprocessing import ClinicalDataPreprocessor
from ml_engine.model_evaluation import compute_clinical_metrics, compute_youden_threshold


class CatBoostTrainer:
    """
    Trains CatBoost model following Paper 1 (2024) methodology.
    """

    def __init__(
        self,
        iterations: int = 350,
        depth: int = 4,
        learning_rate: float = 0.05,
        random_seed: int = 42
    ):
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
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

        # Convert to numpy arrays for target
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
        oof_preds = np.zeros(len(y_train_arr))

        for fold, (train_idx, val_idx) in enumerate(split_iter):
            X_tr, y_tr = X_train.iloc[train_idx], y_train_arr[train_idx]
            X_val, y_val = X_train.iloc[val_idx], y_train_arr[val_idx]

            # Fit preprocessor strictly on this fold's training data
            fold_preprocessor = ClinicalDataPreprocessor(scale_numerical=False)
            X_tr_trans = fold_preprocessor.fit_transform(X_tr)
            X_val_trans = fold_preprocessor.transform(X_val)

            fold_model = CatBoostClassifier(
                iterations=self.iterations,
                depth=self.depth,
                learning_rate=self.learning_rate,
                random_seed=self.random_seed + fold,
                verbose=0
            )
            fold_model.fit(X_tr_trans, y_tr)

            val_probs = fold_model.predict_proba(X_val_trans)[:, 1]
            oof_preds[val_idx] = val_probs

            fold_metric = compute_clinical_metrics(y_val, val_probs, threshold=0.5)
            cv_metrics.append(fold_metric)

        # ---------------------------------------------------------------------
        # 2. Youden Threshold Selection (Derived strictly on validation folds)
        # ---------------------------------------------------------------------
        youden_info = compute_youden_threshold(y_train_arr, oof_preds)
        youden_threshold = youden_info["optimal_threshold"]

        # Aggregate CV scores
        cv_summary = {
            "folds": 3,
            "mean_roc_auc": round(float(np.mean([m["roc_auc"] for m in cv_metrics])), 4),
            "std_roc_auc": round(float(np.std([m["roc_auc"] for m in cv_metrics])), 4),
            "mean_auprc": round(float(np.mean([m["auprc"] for m in cv_metrics])), 4),
            "mean_sensitivity": round(float(np.mean([m["sensitivity"] for m in cv_metrics])), 4),
            "mean_specificity": round(float(np.mean([m["specificity"] for m in cv_metrics])), 4),
            "mean_f1": round(float(np.mean([m["f1_score"] for m in cv_metrics])), 4),
            "youden_threshold_derived": youden_info
        }

        # ---------------------------------------------------------------------
        # 3. Final Model Fit on Full Training Set
        # ---------------------------------------------------------------------
        full_preprocessor = ClinicalDataPreprocessor(scale_numerical=False)
        X_train_trans = full_preprocessor.fit_transform(X_train)
        X_test_trans = full_preprocessor.transform(X_test)
        feature_names = full_preprocessor.get_feature_names_out()

        final_model = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            random_seed=self.random_seed,
            verbose=0
        )
        final_model.fit(X_train_trans, y_train_arr)

        # Independent Holdout Test Evaluation
        test_probs = final_model.predict_proba(X_test_trans)[:, 1]
        test_metrics_default = compute_clinical_metrics(y_test_arr, test_probs, threshold=0.5)
        test_metrics_youden = compute_clinical_metrics(y_test_arr, test_probs, threshold=youden_threshold, compute_ci=True)

        # ---------------------------------------------------------------------
        # 4. Genuine SHAP Explainability (TreeExplainer)
        # ---------------------------------------------------------------------
        shap_explainer = shap.TreeExplainer(final_model)
        # Compute SHAP on test set
        shap_values = shap_explainer.shap_values(X_test_trans)
        expected_value = float(shap_explainer.expected_value) if hasattr(shap_explainer, 'expected_value') else 0.5

        # Global feature importance: mean absolute SHAP value per feature
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        shap_feature_importance = [
            {"feature": name, "mean_abs_shap": round(float(mean_abs_shap[i]), 5)}
            for i, name in enumerate(feature_names)
        ]
        shap_feature_importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)

        training_duration = round(time.time() - start_time, 2)

        return {
            "model_name": "CatBoost (Paper 1, 2024)",
            "model_family": "Gradient Boosting (CatBoost)",
            "hyperparameters": {
                "iterations": self.iterations,
                "depth": self.depth,
                "learning_rate": self.learning_rate
            },
            "training_duration_seconds": training_duration,
            "cv_evaluation": cv_summary,
            "test_evaluation_default_threshold": test_metrics_default,
            "test_evaluation_youden_threshold": test_metrics_youden,
            "youden_threshold": youden_threshold,
            "feature_names": feature_names,
            "shap_summary": {
                "base_value": round(expected_value, 4),
                "top_features": shap_feature_importance[:15]
            },
            "final_model": final_model,
            "preprocessor": full_preprocessor,
            "shap_explainer": shap_explainer
        }

