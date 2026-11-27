"""
NeuroScreen AI - Toddler ASD Questionnaire Model Training Pipeline
Target population: Toddlers aged 12-36 months.
Primary Dataset: Autism Screening Data for Toddlers (Fadi Thabtah, July 2018)
External Validation: Polish Q-CHAT Toddler Dataset (Niedźwiecka et al., Mendeley Data tmpkt2mfkg/2)
Cross-Population Subgroup: Middle Eastern Toddler Cohort

Strict Data Integrity:
- Drops 'Case_No' (anonymized participant ID)
- Drops 'Qchat-10-Score' (deterministic threshold target leakage)
- Stratified 80/20 train/test split
- 5-fold Stratified Cross-Validation
- Platt Sigmoid Calibration via CalibratedClassifierCV
- Evaluates 5 models: Random Forest, SVM (RBF), Gradient Boosting, Logistic Regression, Stacking Ensemble
- Saves artifacts to ml_engine/weights/
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import pyreadstat

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
    confusion_matrix
)


def compute_metrics(y_true, y_pred, y_prob):
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    sens = float(recall_score(y_true, y_pred))
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    brier = float(brier_score_loss(y_true, y_prob))
    
    return {
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "sensitivity_recall": round(sens, 4),
        "specificity": round(spec, 4),
        "precision": round(prec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }
    }


def train_and_evaluate():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "datasets"
    weights_dir = base_dir / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    
    primary_file = data_dir / "toddler_autism_dataset_july_2018.csv"
    polish_file = data_dir / "polish_toddler_qchat.sav"
    
    if not primary_file.exists():
        raise FileNotFoundError(f"Primary dataset not found at {primary_file}")
    
    print("[1/6] Loading and auditing primary toddler dataset...")
    df = pd.read_csv(primary_file)
    print(f"      Loaded {len(df)} records. Columns: {df.columns.tolist()}")
    
    # Target definition & strict leakage removal
    target_col = 'Class/ASD Traits '
    drop_cols = ['Case_No', 'Qchat-10-Score', target_col]
    
    X = df.drop(columns=drop_cols)
    y = (df[target_col].str.strip() == 'Yes').astype(int)
    
    num_cols = ['Age_Mons']
    cat_cols = ['Sex', 'Ethnicity', 'Jaundice', 'Family_mem_with_ASD', 'Who completed the test']
    bin_cols = [f'A{i}' for i in range(1, 11)]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
            ('bin', 'passthrough', bin_cols)
        ]
    )
    
    print("[2/6] Splitting dataset (Stratified 80/20 train/test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    print(f"      Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"      Preprocessed features: {X_train_trans.shape[1]}")
    
    # 5 Algorithms
    base_rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    base_svm = CalibratedClassifierCV(SVC(kernel='rbf', C=1.0, random_state=42), ensemble=False)
    base_gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
    base_lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    
    models = {
        "RandomForest": base_rf,
        "SVM_RBF": base_svm,
        "GradientBoosting": base_gb,
        "LogisticRegression": base_lr
    }
    
    metrics_summary = {"cv_5fold": {}, "test_evaluation": {}}
    
    print("[3/6] Running 5-fold cross-validation across base models...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for name, model in models.items():
        cv_res = cross_validate(
            model, X_train_trans, y_train, cv=cv,
            scoring=['accuracy', 'balanced_accuracy', 'recall', 'precision', 'f1', 'roc_auc']
        )
        metrics_summary["cv_5fold"][name] = {
            "mean_accuracy": round(float(np.mean(cv_res['test_accuracy'])), 4),
            "mean_balanced_accuracy": round(float(np.mean(cv_res['test_balanced_accuracy'])), 4),
            "mean_recall": round(float(np.mean(cv_res['test_recall'])), 4),
            "mean_precision": round(float(np.mean(cv_res['test_precision'])), 4),
            "mean_f1": round(float(np.mean(cv_res['test_f1'])), 4),
            "mean_roc_auc": round(float(np.mean(cv_res['test_roc_auc'])), 4)
        }
        print(f"      {name:18s} -> CV ROC-AUC: {metrics_summary['cv_5fold'][name]['mean_roc_auc']:.4f}, Recall: {metrics_summary['cv_5fold'][name]['mean_recall']:.4f}")
        
        # Fit on train and evaluate on test
        model.fit(X_train_trans, y_train)
        pred = model.predict(X_test_trans)
        prob = model.predict_proba(X_test_trans)[:, 1]
        metrics_summary["test_evaluation"][name] = compute_metrics(y_test, pred, prob)
    
    print("[4/6] Training and calibrating Stacking Ensemble Classifier...")
    estimators = [
        ('rf', RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)),
        ('svm', CalibratedClassifierCV(SVC(kernel='rbf', C=1.0, random_state=42), ensemble=False)),
        ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)),
        ('lr', LogisticRegression(C=1.0, max_iter=1000, random_state=42))
    ]
    meta_clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    stacking_clf = StackingClassifier(estimators=estimators, final_estimator=meta_clf, cv=5)
    
    calibrated_stacking = CalibratedClassifierCV(estimator=stacking_clf, method='sigmoid', cv=3)
    calibrated_stacking.fit(X_train_trans, y_train)
    
    stack_test_pred = calibrated_stacking.predict(X_test_trans)
    stack_test_prob = calibrated_stacking.predict_proba(X_test_trans)[:, 1]
    metrics_summary["test_evaluation"]["StackingEnsemble_Calibrated"] = compute_metrics(
        y_test, stack_test_pred, stack_test_prob
    )
    print(f"      Stacking Ensemble -> Test ROC-AUC: {metrics_summary['test_evaluation']['StackingEnsemble_Calibrated']['roc_auc']:.4f}, Sensitivity: {metrics_summary['test_evaluation']['StackingEnsemble_Calibrated']['sensitivity_recall']:.4f}, Specificity: {metrics_summary['test_evaluation']['StackingEnsemble_Calibrated']['specificity']:.4f}")
    
    print("[5/6] Performing external validation on Polish Clinical Toddler Dataset...")
    if polish_file.exists():
        df_pol, meta = pyreadstat.read_sav(polish_file, apply_value_formats=False)
        
        X_pol = pd.DataFrame()
        # Item mapping from Q-CHAT-25 to Q-CHAT-10:
        # Items 1-9: atypical scoring threshold (recode >= 2.0 indicates atypicality)
        X_pol['A1'] = (df_pol['qchat1recode'] >= 2.0).astype(int)
        X_pol['A2'] = (df_pol['qchat2recode'] >= 2.0).astype(int)
        X_pol['A3'] = (df_pol['qchat5recode'] >= 2.0).astype(int)
        X_pol['A4'] = (df_pol['qchat6recode'] >= 2.0).astype(int)
        X_pol['A5'] = (df_pol['qchat9recode'] >= 2.0).astype(int)
        X_pol['A6'] = (df_pol['qchat10recode'] >= 2.0).astype(int)
        X_pol['A7'] = (df_pol['qchat15recode'] >= 2.0).astype(int)
        X_pol['A8'] = (df_pol['qchat17recode'] >= 2.0).astype(int)
        X_pol['A9'] = (df_pol['qchat19recode'] >= 2.0).astype(int)
        X_pol['A10'] = (df_pol['qchat25recode'] >= 2.0).astype(int)
        
        X_pol['Age_Mons'] = df_pol['age'].fillna(21.0).astype(int)
        X_pol['Sex'] = df_pol['sex'].map({1.0: 'm', 2.0: 'f'}).fillna('m')
        X_pol['Ethnicity'] = 'White European'
        X_pol['Jaundice'] = 'no'
        X_pol['Family_mem_with_ASD'] = df_pol['sibling_withASD'].map({1.0: 'yes', 0.0: 'no'}).fillna('no')
        X_pol['Who completed the test'] = 'family member'
        
        y_pol = (df_pol['group'] == 1.0).astype(int)
        
        X_pol_trans = preprocessor.transform(X_pol)
        pol_probs = calibrated_stacking.predict_proba(X_pol_trans)[:, 1]
        pol_preds = (pol_probs >= 0.5).astype(int)
        
        metrics_summary["external_polish_validation"] = compute_metrics(y_pol, pol_preds, pol_probs)
        metrics_summary["external_polish_validation"]["total_participants"] = len(df_pol)
        metrics_summary["external_polish_validation"]["asd_cases"] = int((y_pol == 1).sum())
        metrics_summary["external_polish_validation"]["control_cases"] = int((y_pol == 0).sum())
        
        print(f"      Polish Validation -> ROC-AUC: {metrics_summary['external_polish_validation']['roc_auc']:.4f}, Accuracy: {metrics_summary['external_polish_validation']['accuracy']:.4f}, Sensitivity: {metrics_summary['external_polish_validation']['sensitivity_recall']:.4f}, Specificity: {metrics_summary['external_polish_validation']['specificity']:.4f}")
    
    # Subgroup evaluation: Middle Eastern / Saudi cohort within primary dataset
    me_indices = X_test['Ethnicity'].str.lower() == 'middle eastern'
    if me_indices.sum() > 0:
        me_y_test = y_test[me_indices]
        me_pred = stack_test_pred[me_indices]
        me_prob = stack_test_prob[me_indices]
        metrics_summary["middle_eastern_subgroup_test"] = compute_metrics(me_y_test, me_pred, me_prob)
        print(f"      Middle Eastern Subgroup -> Test ROC-AUC: {metrics_summary['middle_eastern_subgroup_test']['roc_auc']:.4f}, Accuracy: {metrics_summary['middle_eastern_subgroup_test']['accuracy']:.4f}")
    
    # Sex subgroup evaluation
    male_indices = X_test['Sex'].str.lower() == 'm'
    female_indices = X_test['Sex'].str.lower() == 'f'
    metrics_summary["sex_subgroups"] = {
        "male": compute_metrics(y_test[male_indices], stack_test_pred[male_indices], stack_test_prob[male_indices]),
        "female": compute_metrics(y_test[female_indices], stack_test_pred[female_indices], stack_test_prob[female_indices])
    }
    
    print("[6/6] Saving trained artifacts...")
    model_path = weights_dir / "toddler_questionnaire_model.joblib"
    preprocessor_path = weights_dir / "toddler_preprocessor.joblib"
    metrics_path = weights_dir / "toddler_training_metrics.json"
    metadata_path = weights_dir / "toddler_model_metadata.json"
    
    joblib.dump(calibrated_stacking, model_path)
    joblib.dump(preprocessor, preprocessor_path)
    
    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    metadata = {
        "model_name": "NeuroScreen AI Toddler Q-CHAT Stacking Ensemble",
        "model_version": "1.0.0",
        "target_population": "Toddlers aged 12 to 36 months (1.0 - 3.0 years)",
        "age_restrictions": {
            "minimum_age_months": 12,
            "maximum_age_months": 36,
            "under_12_months_policy": "OBSERVATION_ONLY_UNDER_12M (Standard Q-CHAT-10 is not clinically validated under 12 months; questionnaire predictions are withheld, observation checklist only)",
            "over_36_months_policy": "STANDARD_CHILD_ASSESSMENT (Directs to childhood screening protocols)"
        },
        "algorithm": {
            "ensemble_type": "StackingClassifier",
            "base_learners": ["RandomForestClassifier", "SVC (RBF Kernel)", "GradientBoostingClassifier", "LogisticRegression"],
            "meta_classifier": "LogisticRegression",
            "calibration_method": "Platt Scaling (CalibratedClassifierCV, sigmoid, 3-fold)"
        },
        "features": {
            "numerical": num_cols,
            "categorical": cat_cols,
            "binary_questionnaire_items": bin_cols,
            "total_raw_features": len(num_cols) + len(cat_cols) + len(bin_cols)
        },
        "target": {
            "name": "Class/ASD Traits",
            "positive_label": 1,
            "negative_label": 0
        },
        "data_integrity": {
            "leakage_features_dropped": ["Case_No", "Qchat-10-Score"],
            "leakage_rationale": "Qchat-10-Score is a direct sum of items with deterministic cutoff in original dataset; dropping it forces genuine pattern learning across individual developmental traits."
        },
        "validation": {
            "internal_cv": "5-fold Stratified K-Fold",
            "test_split": "20% Stratified Holdout",
            "external_cohort": "Polish Toddler Q-CHAT (Niedźwiecka et al., 252 participants, Mendeley Data tmpkt2mfkg/2)",
            "cross_population": "Middle Eastern Toddler Subgroup (ASDTests mobile application cohort)"
        },
        "artifacts": {
            "model_file": str(model_path.name),
            "preprocessor_file": str(preprocessor_path.name),
            "metrics_file": str(metrics_path.name)
        }
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"[+] All artifacts successfully saved:")
    print(f"    - Model: {model_path}")
    print(f"    - Preprocessor: {preprocessor_path}")
    print(f"    - Metrics: {metrics_path}")
    print(f"    - Metadata: {metadata_path}")


if __name__ == "__main__":
    train_and_evaluate()

