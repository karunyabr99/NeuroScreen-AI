"""
NeuroScreen AI - Comprehensive Clinical Model Evaluation Engine
Computes ROC-AUC, AUPRC, Sensitivity, Specificity, Precision, Recall, F1, Brier Score,
Youden's J statistic, ROC curve coordinates, and PR curve coordinates for side-by-side comparison.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
    precision_recall_curve
)


def compute_youden_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """
    Compute Youden's J statistic: J = Sensitivity + Specificity - 1
    Selects optimal cut-off threshold T* maximizing J strictly on validation predictions.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    # Specificity = 1 - FPR
    j_scores = tpr + (1.0 - fpr) - 1.0
    best_idx = int(np.argmax(j_scores))

    best_threshold = float(thresholds[best_idx])
    # Handle infinite threshold boundary case in sklearn roc_curve
    if np.isinf(best_threshold) or best_threshold > 1.0:
        best_threshold = 0.5

    return {
        "optimal_threshold": round(best_threshold, 4),
        "youden_j": round(float(j_scores[best_idx]), 4),
        "sensitivity_at_threshold": round(float(tpr[best_idx]), 4),
        "specificity_at_threshold": round(float(1.0 - fpr[best_idx]), 4)
    }


def compute_clinical_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
    compute_ci: bool = False
) -> Dict[str, Any]:
    """
    Calculate comprehensive clinical classification metrics for a model.
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    y_pred = (y_prob >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    sens = float(recall_score(y_true, y_pred, zero_division=0))
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    npv = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))

    # Area metrics
    auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    auprc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    brier = float(brier_score_loss(y_true, y_prob))

    # Curve coordinates (sampled to at most 50 points for efficient JSON serialization)
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    prec_pts, rec_pts, _ = precision_recall_curve(y_true, y_prob)

    step_roc = max(1, len(fpr) // 40)
    roc_points = [
        {"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)}
        for i in range(0, len(fpr), step_roc)
    ]
    if {"fpr": round(float(fpr[-1]), 4), "tpr": round(float(tpr[-1]), 4)} not in roc_points:
        roc_points.append({"fpr": round(float(fpr[-1]), 4), "tpr": round(float(tpr[-1]), 4)})

    step_pr = max(1, len(rec_pts) // 40)
    pr_points = [
        {"recall": round(float(rec_pts[i]), 4), "precision": round(float(prec_pts[i]), 4)}
        for i in range(0, len(rec_pts), step_pr)
    ]

    output = {
        "threshold_used": round(threshold, 4),
        "roc_auc": round(auc, 4),
        "auprc": round(auprc, 4),
        "sensitivity": round(sens, 4),
        "specificity": round(spec, 4),
        "precision_ppv": round(prec, 4),
        "negative_predictive_value": round(npv, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "total": tn + fp + fn + tp
        },
        "roc_curve": roc_points,
        "pr_curve": pr_points
    }
    if compute_ci:
        output["confidence_intervals_95"] = compute_bootstrap_confidence_intervals(
            y_true, y_prob, threshold=threshold
        )
    return output


def compute_bootstrap_confidence_intervals(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
    n_bootstraps: int = 1000,
    random_seed: int = 42
) -> Dict[str, List[float]]:
    """
    Computes 95% bootstrap confidence intervals for clinical metrics.
    """
    rng = np.random.RandomState(random_seed)
    n = len(y_true)
    metrics = {"auc": [], "auprc": [], "sensitivity": [], "specificity": [], "precision": [], "f1": []}

    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, n)
        yt = y_true[idx]
        if len(np.unique(yt)) < 2:
            continue
        yp = y_prob[idx]
        pred = (yp >= threshold).astype(int)

        metrics["auc"].append(roc_auc_score(yt, yp))
        metrics["auprc"].append(average_precision_score(yt, yp))
        metrics["sensitivity"].append(recall_score(yt, pred, zero_division=0))
        tn = np.sum((yt == 0) & (pred == 0))
        fp = np.sum((yt == 0) & (pred == 1))
        metrics["specificity"].append(tn / (tn + fp) if (tn + fp) > 0 else 0.0)
        metrics["precision"].append(precision_score(yt, pred, zero_division=0))
        metrics["f1"].append(f1_score(yt, pred, zero_division=0))

    ci_result = {}
    for k, vals in metrics.items():
        if len(vals) > 0:
            ci_result[k] = [
                round(float(np.percentile(vals, 2.5)), 4),
                round(float(np.percentile(vals, 97.5)), 4)
            ]
        else:
            ci_result[k] = [0.0, 0.0]

    return ci_result


