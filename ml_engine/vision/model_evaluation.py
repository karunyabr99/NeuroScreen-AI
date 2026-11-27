import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.model_selection import StratifiedGroupKFold, GroupKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss
)
from sklearn.calibration import calibration_curve

class ParticipantLevelVisionDatasetSplitter:
    """
    Enforces participant-level disjoint partitioning for multimodal and vision-derived ML pipelines.
    
    CRITICAL METHODOLOGICAL SAFEGUARD:
    Video frames, feature clips, and multiple sessions from the same child must NEVER appear in
    both training and evaluation sets simultaneously. Leakage across folds produces artificially
    inflated, clinically misleading metrics.
    """

    @classmethod
    def split_by_participant(
        cls,
        features: np.ndarray,
        labels: np.ndarray,
        participant_ids: np.ndarray,
        n_splits: int = 5,
        random_state: int = 42
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Generates cross-validation fold indices grouped strictly by participant identifier.
        Guarantees that each participant's observations reside entirely within train OR test fold.
        """
        assert len(features) == len(labels) == len(participant_ids), "Features, labels, and participant_ids must have identical lengths."

        # Unique participant count validation
        unique_participants = np.unique(participant_ids)
        if len(unique_participants) < n_splits:
            raise ValueError(
                f"Cannot split into {n_splits} participant folds with only {len(unique_participants)} unique participants. "
                "Minimum participants must equal or exceed n_splits to avoid empty validation sets."
            )

        # Check label distribution per participant if stratified split is desired
        try:
            sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
            splits = list(sgkf.split(features, labels, groups=participant_ids))
        except Exception:
            # Fall back to standard GroupKFold if label stratification cannot be satisfied
            gkf = GroupKFold(n_splits=n_splits)
            splits = list(gkf.split(features, labels, groups=participant_ids))

        # Verification: Assert zero participant overlap between train and test
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            train_participants = set(participant_ids[train_idx])
            test_participants = set(participant_ids[test_idx])
            overlap = train_participants.intersection(test_participants)
            if overlap:
                raise AssertionError(
                    f"CRITICAL LEAKAGE DETECTED in Fold {fold_idx}: Participants {overlap} "
                    "appear in both training and test sets!"
                )

        return splits

    @classmethod
    def evaluate_clinical_metrics(
        cls,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray,
        bootstrap_ci: bool = True,
        n_bootstraps: int = 200,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Evaluates comprehensive clinical and statistical performance metrics:
          - Sensitivity (Recall)
          - Specificity (True Negative Rate)
          - Precision (Positive Predictive Value)
          - F1-Score (Harmonic mean of Precision and Recall)
          - ROC-AUC (Area under ROC Curve)
          - PR-AUC (Precision-Recall Area under Curve / Average Precision)
          - Calibration Brier Score (Mean squared prediction error on probabilities)
          - 95% Confidence Intervals via non-parametric bootstrapping
        """
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = precision_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # ROC-AUC and PR-AUC require probability array
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = 0.5
        try:
            pr_auc = float(average_precision_score(y_true, y_prob))
        except Exception:
            pr_auc = float(np.mean(y_true))

        brier = float(brier_score_loss(y_true, y_prob))

        # Calibration curve (10 bins)
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="uniform")

        metrics = {
            "sample_size": len(y_true),
            "confusion_matrix": {"true_positive": int(tp), "false_positive": int(fp), "true_negative": int(tn), "false_negative": int(fn)},
            "sensitivity": round(float(sensitivity), 4),
            "specificity": round(float(specificity), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(sensitivity), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "brier_score": round(float(brier), 4),
            "calibration_curve": {
                "mean_predicted_probabilities": [round(float(p), 3) for p in prob_pred],
                "fraction_of_positives": [round(float(p), 3) for p in prob_true]
            }
        }

        # 95% Bootstrap Confidence Intervals
        if bootstrap_ci and len(y_true) >= 20:
            rng = np.random.RandomState(random_state)
            boot_sens, boot_spec, boot_f1, boot_auc = [], [], [], []
            n_samples = len(y_true)

            for _ in range(n_bootstraps):
                indices = rng.choice(n_samples, size=n_samples, replace=True)
                b_true, b_pred, b_prob = y_true[indices], y_pred[indices], y_prob[indices]
                if len(np.unique(b_true)) < 2:
                    continue
                b_tn, b_fp, b_fn, b_tp = confusion_matrix(b_true, b_pred, labels=[0, 1]).ravel()
                b_se = b_tp / (b_tp + b_fn) if (b_tp + b_fn) > 0 else 0.0
                b_sp = b_tn / (b_tn + b_fp) if (b_tn + b_fp) > 0 else 0.0
                boot_sens.append(b_se)
                boot_spec.append(b_sp)
                boot_f1.append(f1_score(b_true, b_pred, zero_division=0))
                try:
                    boot_auc.append(roc_auc_score(b_true, b_prob))
                except Exception:
                    pass

            if boot_sens:
                metrics["confidence_intervals_95"] = {
                    "sensitivity": [round(float(np.percentile(boot_sens, 2.5)), 3), round(float(np.percentile(boot_sens, 97.5)), 3)],
                    "specificity": [round(float(np.percentile(boot_spec, 2.5)), 3), round(float(np.percentile(boot_spec, 97.5)), 3)],
                    "f1_score": [round(float(np.percentile(boot_f1, 2.5)), 3), round(float(np.percentile(boot_f1, 97.5)), 3)],
                    "roc_auc": [round(float(np.percentile(boot_auc, 2.5)), 3), round(float(np.percentile(boot_auc, 97.5)), 3)] if boot_auc else [0.5, 0.5]
                }

        return metrics

