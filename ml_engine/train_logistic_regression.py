"""
NeuroScreen AI - Paper 2 (2022) LASSO Logistic Regression Training Pipeline
Implements:
- LogisticRegression with L1 regularization (LASSO)
- Training-only numerical standardization pipeline
- Automatic LASSO feature selection via non-zero L1 coefficients
- 3-fold Stratified Cross-Validation
- Independent holdout test evaluation: ROC-AUC, AUPRC, Sensitivity, Specificity, F1, Confusion Matrix
- Selected feature reporting (risk drivers vs protective factors)
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

from ml_engine.preprocessing import ClinicalDataPreprocessor
from ml_engine.model_evaluation import compute_clinical_metrics


class LassoLogisticRegressionTrainer:
    """
    Trains LASSO Logistic Regression following Paper 2 (2022) methodology.
    """

    def __init__(
        self,
        C: float = 0.5,
        penalty: str = 'l1',
        solver: str = 'liblinear',
        max_iter: int = 2000,
        random_seed: int = 42
    ):
        self.C = C
        self.penalty = penalty
        self.solver = solver
        self.max_iter = max_iter
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

            # Scale numerical features for LASSO convergence
            fold_preprocessor = ClinicalDataPreprocessor(scale_numerical=True)
            X_tr_trans = fold_preprocessor.fit_transform(X_tr)
            X_val_trans = fold_preprocessor.transform(X_val)

            fold_model = LogisticRegression(
                penalty=self.penalty,
                C=self.C,
                solver=self.solver,
                max_iter=self.max_iter,
                random_state=self.random_seed + fold,
                l1_ratio=1.0 if self.solver in ['saga', 'elasticnet'] else None
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
        full_preprocessor = ClinicalDataPreprocessor(scale_numerical=True)
        X_train_trans = full_preprocessor.fit_transform(X_train)
        X_test_trans = full_preprocessor.transform(X_test)
        feature_names = full_preprocessor.get_feature_names_out()

        final_model = LogisticRegression(
            penalty=self.penalty,
            C=self.C,
            solver=self.solver,
            max_iter=self.max_iter,
            random_state=self.random_seed,
            l1_ratio=1.0 if self.solver in ['saga', 'elasticnet'] else None
        )
        final_model.fit(X_train_trans, y_train_arr)

        # Independent Holdout Test Evaluation
        test_probs = final_model.predict_proba(X_test_trans)[:, 1]
        test_metrics = compute_clinical_metrics(y_test_arr, test_probs, threshold=0.5, compute_ci=True)

        # ---------------------------------------------------------------------
        # 3. LASSO Feature Selection (Non-zero coefficients analysis)
        # ---------------------------------------------------------------------
        coefs = final_model.coef_[0]
        intercept = float(final_model.intercept_[0])

        selected_features = []
        all_feature_weights = []

        for i, name in enumerate(feature_names):
            weight = float(coefs[i])
            weight_entry = {
                "feature": name,
                "coefficient": round(weight, 5),
                "abs_weight": round(abs(weight), 5),
                "direction": "Risk-Increasing (+)" if weight > 0 else "Protective / Risk-Reducing (-)" if weight < 0 else "Neutral / Shrunk to Zero"
            }
            all_feature_weights.append(weight_entry)
            if abs(weight) > 1e-4:
                selected_features.append(weight_entry)

        selected_features.sort(key=lambda x: x["abs_weight"], reverse=True)
        all_feature_weights.sort(key=lambda x: x["abs_weight"], reverse=True)

        training_duration = round(time.time() - start_time, 2)

        return {
            "model_name": "LASSO Logistic Regression (Paper 2, 2022)",
            "model_family": "L1 Regularized Generalized Linear Model",
            "hyperparameters": {
                "penalty": self.penalty,
                "C": self.C,
                "solver": self.solver,
                "max_iter": self.max_iter
            },
            "training_duration_seconds": training_duration,
            "cv_evaluation": cv_summary,
            "test_evaluation": test_metrics,
            "feature_names": feature_names,
            "intercept": round(intercept, 5),
            "total_initial_features": len(feature_names),
            "lasso_selected_features_count": len(selected_features),
            "lasso_selected_features": selected_features,
            "top_coefficients": all_feature_weights[:15],
            "final_model": final_model,
            "preprocessor": full_preprocessor
        }
