import os
import joblib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedGroupKFold, GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)
from catboost import CatBoostClassifier

from ml_engine.config import FEATURE_NAMES, WEIGHTS_DIR, TOTAL_FEATURE_DIM

class DatasetValidationResult:
    def __init__(
        self,
        is_eligible: bool,
        total_samples: int,
        num_participants: int,
        class_counts: Dict[int, int],
        missing_rate_overall: float,
        reasons: List[str],
        warnings: List[str]
    ):
        self.is_eligible = is_eligible
        self.total_samples = total_samples
        self.num_participants = num_participants
        self.class_counts = class_counts
        self.missing_rate_overall = missing_rate_overall
        self.reasons = reasons
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_eligible": self.is_eligible,
            "total_samples": self.total_samples,
            "num_participants": self.num_participants,
            "class_counts": self.class_counts,
            "missing_rate_overall": round(self.missing_rate_overall, 3),
            "reasons": self.reasons,
            "warnings": self.warnings
        }


class DatasetValidator:
    """
    Validates clinical research datasets prior to ML training.
    Enforces minimum participant count, class balance, label completeness, and missingness bounds.
    Prevents premature or scientifically invalid training on small cohorts.
    """
    MIN_SAMPLES = 50
    MIN_PARTICIPANTS = 40
    MIN_PER_CLASS = 15
    MAX_MISSING_RATE = 0.40

    @classmethod
    def validate(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        participant_ids: List[str]
    ) -> DatasetValidationResult:
        reasons = []
        warnings = []

        total_samples = len(y)
        unique_participants = len(set(participant_ids))
        classes, counts = np.unique(y, return_counts=True)
        class_counts = dict(zip([int(c) for c in classes], [int(c) for c in counts]))

        # 1. Sample Size Check
        if total_samples < cls.MIN_SAMPLES:
            reasons.append(
                f"Total sample count (N={total_samples}) is below clinical training threshold (required >= {cls.MIN_SAMPLES})."
            )

        if unique_participants < cls.MIN_PARTICIPANTS:
            reasons.append(
                f"Unique participant cohort size (N={unique_participants}) is below minimum generalization requirement (required >= {cls.MIN_PARTICIPANTS})."
            )

        # 2. Class Balance & Representation
        for c in [0, 1]:
            c_count = class_counts.get(c, 0)
            if c_count < cls.MIN_PER_CLASS:
                reasons.append(
                    f"Class {c} representation ({c_count}) is below minimum statistical threshold ({cls.MIN_PER_CLASS} per class)."
                )

        # 3. Missingness Check
        if X.size > 0:
            missing_rate = float(np.isnan(X).sum() / X.size)
            if missing_rate > cls.MAX_MISSING_RATE:
                reasons.append(
                    f"Overall feature missingness ({round(missing_rate * 100, 1)}%) exceeds maximum acceptable threshold ({int(cls.MAX_MISSING_RATE * 100)}%)."
                )
            elif missing_rate > 0.15:
                warnings.append(
                    f"Feature missingness is {round(missing_rate * 100, 1)}%. Imputation will be required."
                )
        else:
            missing_rate = 1.0
            reasons.append("Feature matrix X contains 0 elements.")

        # 4. Length Consistency
        if len(X) != total_samples or len(participant_ids) != total_samples:
            reasons.append(
                f"Dimension mismatch between X ({len(X)}), y ({total_samples}), and participant_ids ({len(participant_ids)})."
            )

        is_eligible = len(reasons) == 0

        return DatasetValidationResult(
            is_eligible=is_eligible,
            total_samples=total_samples,
            num_participants=unique_participants,
            class_counts=class_counts,
            missing_rate_overall=missing_rate,
            reasons=reasons,
            warnings=warnings
        )


class FeaturePreprocessor:
    """
    Fits imputation and scaling strictly on training folds to prevent data leakage.
    Applies fitted transformers to validation and test folds.
    """
    def __init__(self, select_k: Optional[int] = None):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.selector = SelectKBest(f_classif, k=select_k) if select_k and select_k < TOTAL_FEATURE_DIM else None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        X_imp = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imp)
        if self.selector and y is not None:
            self.selector.fit(X_scaled, y)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_imp = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imp)
        if self.selector:
            return self.selector.transform(X_scaled)
        return X_scaled

    def fit_transform(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        self.fit(X, y)
        return self.transform(X)


class ParticipantLevelSplitter:
    """
    Partitions datasets grouped strictly by participant identifier.
    Guarantees 0% participant leakage between train and validation/test folds.
    """
    def __init__(self, n_splits: int = 5, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state

    def split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        participant_ids: List[str]
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        groups = np.array(participant_ids)
        
        # Verify if stratified group split is feasible with current class counts
        try:
            sgkf = StratifiedGroupKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
            splits = list(sgkf.split(X, y, groups=groups))
        except Exception:
            gkf = GroupKFold(n_splits=self.n_splits)
            splits = list(gkf.split(X, y, groups=groups))

        # Scientific Integrity Assertion: Verify zero participant leakage
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            train_participants = set(groups[train_idx])
            test_participants = set(groups[test_idx])
            overlap = train_participants.intersection(test_participants)
            if overlap:
                raise ValueError(
                    f"Data Leakage Detected in Fold {fold_idx}: "
                    f"{len(overlap)} participants leaked across train and test partitions: {list(overlap)[:3]}"
                )

        return splits


class TrainingPipeline:
    """
    End-to-end multimodal model training, cross-validation, calibration, and benchmarking pipeline.
    Compares CatBoost, Random Forest, and Logistic Regression with rigorous clinical evaluation metrics.
    """
    def __init__(
        self,
        n_splits: int = 5,
        random_seed: int = 42,
        weights_dir: Optional[Path] = None
    ):
        self.n_splits = n_splits
        self.random_seed = random_seed
        self.weights_dir = weights_dir or WEIGHTS_DIR
        self.weights_dir.mkdir(parents=True, exist_ok=True)

    def _init_models(self) -> Dict[str, Any]:
        return {
            "CatBoost": CatBoostClassifier(
                iterations=100,
                depth=4,
                learning_rate=0.08,
                random_seed=self.random_seed,
                verbose=0
            ),
            "Random_Forest": RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_leaf=2,
                random_state=self.random_seed
            ),
            "Logistic_Regression": LogisticRegression(
                C=1.0,
                max_iter=1000,
                solver="liblinear",
                random_state=self.random_seed
            )
        }

    def run(
        self,
        X: np.ndarray,
        y: np.ndarray,
        participant_ids: List[str],
        export_checkpoints: bool = False
    ) -> Dict[str, Any]:
        """
        Executes ML training workflow.
        If dataset is too small or invalid, gracefully halts and returns eligibility diagnostic report.
        """
        # Step 1: Dataset Validation Gate
        validation_report = DatasetValidator.validate(X, y, participant_ids)
        if not validation_report.is_eligible:
            return {
                "status": "TRAINING_SUSPENDED_INSUFFICIENT_DATA",
                "eligible": False,
                "validation_report": validation_report.to_dict(),
                "message": (
                    "Model training is strictly suspended in accordance with research governance rules. "
                    "Clinical cohort sample size or label balance does not meet the minimum statistical validity criteria."
                ),
                "model_comparison": {},
                "calibrated_checkpoints": []
            }

        # Step 2: Participant-Level Splitting
        splitter = ParticipantLevelSplitter(n_splits=self.n_splits, random_state=self.random_seed)
        splits = splitter.split(X, y, participant_ids)

        model_comparison = {}
        models = self._init_models()

        # Step 3: Stratified Participant Cross-Validation
        for name, model_cls in models.items():
            oof_preds = np.zeros(len(y))
            oof_probs = np.zeros(len(y))

            for train_idx, val_idx in splits:
                X_tr, y_tr = X[train_idx], y[train_idx]
                X_val = X[val_idx]

                # Leakage-free preprocessing
                preprocessor = FeaturePreprocessor()
                X_tr_proc = preprocessor.fit_transform(X_tr, y_tr)
                X_val_proc = preprocessor.transform(X_val)

                # Fit model on train fold
                model = self._init_models()[name]
                model.fit(X_tr_proc, y_tr)

                val_probs = model.predict_proba(X_val_proc)[:, 1]
                val_preds = (val_probs >= 0.5).astype(int)

                oof_probs[val_idx] = val_probs
                oof_preds[val_idx] = val_preds

            # Compute clinical evaluation metrics across OOF predictions
            tn, fp, fn, tp = confusion_matrix(y, oof_preds).ravel()
            sensitivity = float(recall_score(y, oof_preds, pos_label=1, zero_division=0)) # Recall / Sensitivity
            specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            precision = float(precision_score(y, oof_preds, pos_label=1, zero_division=0))
            f1 = float(f1_score(y, oof_preds, pos_label=1, zero_division=0))
            roc_auc = float(roc_auc_score(y, oof_probs))
            pr_auc = float(average_precision_score(y, oof_probs))
            brier = float(brier_score_loss(y, oof_probs))

            model_comparison[name] = {
                "sensitivity": round(sensitivity, 3),
                "specificity": round(specificity, 3),
                "precision": round(precision, 3),
                "recall": round(sensitivity, 3),
                "f1_score": round(f1, 3),
                "roc_auc": round(roc_auc, 3),
                "pr_auc": round(pr_auc, 3),
                "brier_score": round(brier, 3),
                "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}
            }

        # Step 4: Model Selection & Final Training
        best_model_name = max(model_comparison.keys(), key=lambda k: model_comparison[k]["roc_auc"])
        best_metrics = model_comparison[best_model_name]

        # Train full model with Platt calibration
        full_preprocessor = FeaturePreprocessor().fit(X, y)
        X_proc = full_preprocessor.transform(X)

        best_base_model = self._init_models()[best_model_name]
        best_base_model.fit(X_proc, y)

        calibrated_model = CalibratedClassifierCV(
            estimator=best_base_model,
            method="sigmoid",
            cv=3
        )
        calibrated_model.fit(X_proc, y)

        exported_files = []
        if export_checkpoints:
            # Save Random Forest checkpoint
            rf_full = self._init_models()["Random_Forest"].fit(X_proc, y)
            rf_calibrated = CalibratedClassifierCV(estimator=rf_full, method="sigmoid", cv=3).fit(X_proc, y)
            rf_path = self.weights_dir / "rf_multimodal.joblib"
            joblib.dump(rf_calibrated, str(rf_path))
            exported_files.append(str(rf_path))

            # Save CatBoost checkpoint
            cb_full = self._init_models()["CatBoost"].fit(X_proc, y)
            cb_path = self.weights_dir / "catboost_multimodal.joblib"
            joblib.dump(cb_full, str(cb_path))
            exported_files.append(str(cb_path))

        return {
            "status": "TRAINING_COMPLETED_SUCCESSFULLY",
            "eligible": True,
            "validation_report": validation_report.to_dict(),
            "best_model": best_model_name,
            "best_model_metrics": best_metrics,
            "model_comparison": model_comparison,
            "calibrated": True,
            "calibration_method": "Platt Scaling (Sigmoid)",
            "calibrated_checkpoints": exported_files
        }

