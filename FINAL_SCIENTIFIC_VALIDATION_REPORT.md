# NeuroScreen AI: Final Independent Scientific Validation & Verification Report

**Date of Audit:** November 2026  
**Audited Primary Dataset:** `toddler_autism_dataset_july_2018.csv` ($N = 1,054$)  
**Audited External Cohort:** `polish_toddler_qchat.sav` ($N = 252$)  
**Verification Status:** Verified, Hardened, Strict Group-Isolation Implemented  

---

## 1. Executive Summary

This report delivers the final forensic verification of the machine learning system within **NeuroScreen AI**. 

Three fundamental conclusions have been established with mathematical certainty:
1. **Target Construction & Circular Leakage:** In the primary Kaggle toddler dataset, the target column `Class/ASD Traits` is **100.0% deterministically generated** from an arithmetic cut-off on the questionnaire items ($\sum_{i=1}^{10} A_i \ge 4$). There are **zero exceptions** across all $1,054$ observations. Any model trained on items $A_1 \dots A_{10}$ reproduces this arithmetic rule rather than learning an independent clinical autism diagnosis.
2. **Duplicate Record Leakage Audit:** Forensic inspection identified **59 duplicate groups** covering **138 records** ($79$ excess redundant copies). In naive unstratified splitting, $23$ duplicate groups crossed the train/test boundary, contaminating the holdout test set with **$24$ identical twin records ($11.37\%$)**. A strict group-based isolation strategy (`StratifiedGroupKFold`) has been implemented, eliminating cross-split contamination ($0$ duplicate groups cross boundaries). Removing duplicate leakage adjusted the demographic-only test ROC-AUC from $0.6886$ to **$0.6170$**.
3. **External Clinical Validation & Provenance Verification:** Provenance audit of the Polish Toddler cohort (Niedźwiecka, Pisula, Domasiewicz, 2020; Mendeley Data DOI: [10.17632/tmpkt2mfkg.2](https://doi.org/10.17632/tmpkt2mfkg.2)) verifies that ground-truth labels reflect a **community-based clinical diagnosis of ASD** granted by regional developmental centres (such as SYNAPSIS Foundation). Standardized research administration of ADOS-2 or ADI-R is **not** explicitly documented in the dataset record. Evaluated under a frozen decision threshold ($0.6915$) derived strictly from training folds without external exposure, CatBoost achieved **$0.9355$ ROC-AUC** ($95\%$ CI: $[0.9046, 0.9623]$) and **$91.45\%$ Specificity** ($95\%$ CI: $[0.8583, 0.9633]$). This validates questionnaire-based behavioral discrimination ($10$ mapped items from Q-CHAT-25); it does **not** validate demographic-only prediction (which drops to $0.5842$ ROC-AUC) or live-video vision models.

---

## 2. Duplicate Record Leakage Audit

### 2.1 Forensic Inventory of Exact Duplicates
Excluding arbitrary identifier `Case_No`, aggregate score `Qchat-10-Score`, and target `Class/ASD Traits`, the primary dataset was audited across all 16 clinical and demographic variables:

* **Total Dataset Records:** $1,054$
* **Distinct Feature Profiles:** $975$
* **Total Duplicate Groups ($>1$ identical record):** $59$
* **Total Records in Duplicate Groups:** $138$
* **Excess Redundant Copies:** $79$
* **Duplicate Group Size Distribution:**
  - $44$ groups of size $2$ ($88$ records)
  - $11$ groups of size $3$ ($33$ records)
  - $3$ groups of size $4$ ($12$ records)
  - $1$ group of size $5$ ($5$ records)
* **Conflicting Target Labels within Duplicate Groups:** **0** (All identical twins share identical targets because $\sum A_i \ge 4$ is deterministic).

### 2.2 Leakage in Naive Splitting
When an un-grouped $80/20$ train/test split is applied:
* **Duplicate groups crossing train/test boundary:** $23$ groups
* **Holdout test records with identical twins in training set:** **$24$ out of $211$ ($11.37\%$)**
* **Training records with identical twins in test set:** **$32$ out of $843$ ($3.80\%$)**
* **Cross-Validation fold twin overlap:** **$7.12\%$ to $10.68\%$** of validation records had exact duplicates in training folds.

### 2.3 Scientific Mitigation Strategy
To eliminate duplicate leakage without discarding clinically plausible identical presentations:
* Unique feature profiles were hashed into distinct group identifiers (`group_id`).
* An outer **5-fold `StratifiedGroupKFold`** split ($80\%$ train, $20\%$ holdout test) was implemented.
* An inner **3-fold `StratifiedGroupKFold`** cross-validation split was implemented within training folds.
* **Result:** Exactly **$0$ duplicate groups** cross between train and test, and **$0$ duplicate groups** cross between cross-validation folds.

---

## 3. External Polish Cohort Verification & Provenance Correction

### 3.1 Provenance, Primary Citation & Participant Count Resolution
* **Study Title:** *Q-CHAT scores of Polish toddlers with autism spectrum disorders and typically developing controls*
* **Authors:** Alicja Niedźwiecka, Ewa Pisula, and Zuzanna Domasiewicz (2020)
* **Affiliation:** University of Warsaw, Faculty of Psychology & SYNAPSIS Foundation (Warsaw, Poland)
* **Repository & Citation:** Mendeley Data, DOI: [10.17632/tmpkt2mfkg.2](https://doi.org/10.17632/tmpkt2mfkg.2) (Version 2, published October 2020)
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Dataset File:** `ml_engine/datasets/polish_toddler_qchat.sav` (SPSS format)
* **Cryptographic Checksum:** `SHA256: 7fed516fc4e615f4750d0e44c1eea538bbdcdee989e8c2ff8de719976fa08a41`
* **Participant Count Resolution ($N = 252$):**
  - **Mendeley Abstract Description:** States *"135 toddlers with a community-based diagnosis of Autism Spectrum Disorders (ASD), 118 typically developing toddlers (control group)"*. This text implies $135 + 118 = 253$ participants.
  - **SPSS Dataset File Count:** The published SPSS data file (`polish_toddler_qchat.sav`) contains exactly **$252$ participant records**:
    - `group == 1.0` (ASD): $135$ toddlers ($53.57\%$)
    - `group == 7.0` (Typically Developing Control): $117$ toddlers ($46.43\%$)
  - **Resolution:** $135 + 117 = 252$. All $252$ records present in the primary SPSS file are evaluated with zero exclusions. The 1-participant difference is an author-level discrepancy between their abstract text and the uploaded `.sav` dataset file (an off-by-one textual error or pre-upload exclusion of 1 control record). The original dataset checksum is strictly preserved.

### 3.2 Diagnostic Ground-Truth Methodology Correction
* **Verified Diagnostic Methodology:** The primary dataset record documents a **community-based clinical diagnosis of ASD** established at diagnostic centres in Poland (including the SYNAPSIS Foundation).
* **Correction of Prior Claims:** Standardized research administration of the **Autism Diagnostic Observation Schedule (ADOS)** or **Autism Diagnostic Interview-Revised (ADI-R)** across the entire cohort is **not** explicitly documented in the Mendeley record. Prior references in platform documentation claiming "ADOS/ADI-R Ground Truth" have been corrected to **"Community-Based Clinical ASD Diagnosis"**.

### 3.3 Evaluation Scope & Protocol Independence
* **Zero Contamination Verification:**
  - $0$ external cohort records were included in model training, feature selection, or imputation fitting.
  - The classification decision threshold ($T^* = 0.6915$) was computed strictly from training folds via Youden's $J$ optimization and frozen before external evaluation.
* **Feature Harmonization (Q-CHAT-25 to Q-CHAT-10):**
  - CatBoost Experiment A was trained on questionnaire items ($A_1 \dots A_{10}$) along with demographics.
  - $10$ corresponding items were extracted from the Polish Q-CHAT-25 responses (`qchat1recode`, `qchat2recode`, `qchat5recode`, `qchat6recode`, `qchat9recode`, `qchat10recode`, `qchat15recode`, `qchat17recode`, `qchat19recode`, `qchat25recode`) and dichotomized ($\ge 2$ indicative of atypical behavior).
  - Age in months ($18 \dots 24$, mean $21.06$), Sex ($157$ Male, $95$ Female), Family ASD history (`sibling_withASD`). Jaundice was not recorded in the Polish study (assigned baseline 'no').
* **Clear Scope Boundaries:**
  - External validation demonstrates **questionnaire-based behavioral discrimination** against real-world clinical labels.
  - It does **not** establish demographic-only prediction (Experiment B drops to $0.5842$ ROC-AUC, near chance, on this cohort).
  - It does **not** validate the live-video or computer-vision behavioral screening models.

---

## 4. Empirical Evaluation Across the Three Paradigms

All metrics below are computed on held-out test data with $95\%$ bootstrap confidence intervals ($1,000$ resamples):

### 4.1 Summary Table

| Evaluation Cohort | Model | ROC-AUC (95% CI) | AUPRC (95% CI) | Sensitivity (95% CI) | Specificity (95% CI) | Precision PPV (95% CI) | F1-Score (95% CI) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Exp A: Questionnaire Items**<br>*(A1-A10 + Demographics)*<br>*Group-Isolated Holdout ($N=211$)* | **CatBoost**<br>*(Paper 1, 2024)* | **1.0000**<br>[1.000, 1.000] | **1.0000**<br>[1.000, 1.000] | **100.0%**<br>[100.0, 100.0] | **100.0%**<br>[100.0, 100.0] | **100.0%**<br>[100.0, 100.0] | **1.0000**<br>[1.000, 1.000] |
| | **Random Forest**<br>*(Paper 2, 2022)* | **0.9936**<br>[0.9861, 0.9990] | **0.9973**<br>[0.9935, 0.9996] | **97.95%**<br>[95.17, 100.0] | **80.00%**<br>[69.23, 89.23] | **91.67%**<br>[87.34, 95.83] | **0.9470**<br>[0.9205, 0.9722] |
| | **LASSO L1**<br>*(Paper 2, 2022)* | **1.0000**<br>[1.000, 1.000] | **1.0000**<br>[1.000, 1.000] | **100.0%**<br>[100.0, 100.0] | **98.46%**<br>[94.44, 100.0] | **99.32%**<br>[97.58, 100.0] | **0.9966**<br>[0.9877, 1.000] |
| **Exp B: Pre-Test Demographics**<br>*(Demographics/History Only)*<br>*Group-Isolated Holdout ($N=211$)* | **CatBoost**<br>*(Paper 1, 2024)* | **0.6170**<br>[0.5331, 0.6950] | **0.8037**<br>[0.7348, 0.8656] | **53.42%**<br>[45.25, 0.6208] | **64.62%**<br>[52.83, 75.93] | **77.23%**<br>[68.80, 84.81] | **0.6316**<br>[0.5517, 0.7059] |
| | **Random Forest**<br>*(Paper 2, 2022)* | **0.6168**<br>[0.5336, 0.6999] | **0.7974**<br>[0.7268, 0.8617] | **93.15%**<br>[88.67, 97.16] | **7.69%**<br>[1.72, 14.93] | **69.39%**<br>[62.77, 75.81] | **0.7953**<br>[0.7397, 0.8464] |
| | **LASSO L1**<br>*(Paper 2, 2022)* | **0.5543**<br>[0.4697, 0.6358] | **0.7461**<br>[0.6698, 0.8170] | **93.15%**<br>[88.65, 97.20] | **6.15%**<br>[1.49, 12.33] | **69.04%**<br>[62.56, 75.40] | **0.7930**<br>[0.7371, 0.8443] |
| **External Clinical Validation**<br>*(Community Clinical Ground Truth)*<br>*Polish Clinical Cohort ($N=252$)* | **CatBoost**<br>*(Trained on Exp A)* | **0.9355**<br>[0.9046, 0.9623] | **0.9254**<br>[0.8711, 0.9685] | **77.04%**<br>[69.85, 83.82] | **91.45%**<br>[85.83, 96.33] | **91.23%**<br>[85.71, 96.15] | **0.8353**<br>[0.7838, 0.8807] |
| | **CatBoost**<br>*(Trained on Exp B)* | **0.5842**<br>[0.5132, 0.6558] | **0.6374**<br>[0.5582, 0.7164] | **100.0%**<br>[100.0, 100.0] | **0.00%**<br>[0.00, 0.00] | **53.57%**<br>[47.35, 59.80] | **0.6977**<br>[0.6427, 0.7485] |

---

## 5. Confusion Matrices

### 5.1 Experiment A: CatBoost on Group-Isolated Holdout ($N = 211$)
*Decision Threshold:* $T^* = 0.6915$
```
                    Predicted Negative    Predicted Positive      Total
Actual Negative             65 (TN)                0 (FP)            65
Actual Positive              0 (FN)              146 (TP)           146
Total                       65                   146                211
```
*Balanced Accuracy:* $100.0\%$ | *Brier Score:* $0.0076$

### 5.2 Experiment B: CatBoost on Group-Isolated Holdout ($N = 211$)
*Decision Threshold:* $T^* = 0.6775$
```
                    Predicted Negative    Predicted Positive      Total
Actual Negative             42 (TN)               23 (FP)            65
Actual Positive             68 (FN)               78 (TP)           146
Total                      110                   101                211
```
*Balanced Accuracy:* $59.02\%$ | *Brier Score:* $0.2179$

### 5.3 External Clinical Cohort: CatBoost on Polish Toddlers ($N = 252$)
*Decision Threshold:* $T^* = 0.6915$ (Frozen from training folds)
```
                    Predicted Negative    Predicted Positive      Total
Actual Negative            107 (TN)               10 (FP)           117
Actual Positive             31 (FN)              104 (TP)           135
Total                      138                   114                252
```
*Balanced Accuracy:* $84.25\%$ | *False Positive Rate:* $8.55\%$

---

## 6. Reproducibility & Cryptographic Provenance

To guarantee exact audit reproducibility:

### 6.1 Cryptographic File Hashes
* **Primary Toddler Dataset (`toddler_autism_dataset_july_2018.csv`):**  
  `SHA256: 818d604290cdae767f40a1bfcc2ca5634f1ba9ed1c31bfd41aa4b450943d973f`
* **External Polish Clinical Dataset (`polish_toddler_qchat.sav`):**  
  `SHA256: 7fed516fc4e615f4750d0e44c1eea538bbdcdee989e8c2ff8de719976fa08a41`
* **CatBoost Primary Model Weights (`catboost_research.joblib`):**  
  `SHA256: 62bc74b486938a16db2c219602fdb8cb45d475cbe6f7c9e54a01e389e17b8f9e`
* **Metadata & Audit Registry (`research_ml_metadata.json`):**  
  `SHA256: 25055b80ee91aa9b9fe556f89dd0e4ef3d8a98fa4c3f5ea7c44df656641bce74`

### 6.2 Deterministic Split Protocol
* **Random Seed:** $42$ fixed across all dataset loaders, group splitters, and model trainers.
* **Stratification:** Stratified by binary class outcome and grouped by unique 16-feature combination.
* **Transformer Hygiene:** Preprocessing scaling and one-hot encoders are fitted exclusively within each fold's training slice (`X_tr`) and applied out-of-sample to validation and test slices.
* **Test Isolation:** The test set was accessed strictly once after hyperparameter and threshold derivation was finalized.

---

## 7. Model Limitations

1. **Questionnaire Boundary Confounding:** The primary Kaggle dataset does not contain clinically diagnosed ASD outcomes. High metrics in Experiment A represent the mathematical recovery of the addition rule $\sum_{i=1}^{10} A_i \ge 4$.
2. **Weak Pre-Test Demographic Signal:** Non-questionnaire demographics alone (`Age`, `Sex`, `Ethnicity`, `Jaundice`, `Family ASD`) achieve an ROC-AUC of only $0.6170$. On an external cohort, demographics drop to near-chance ($0.5842$). Demographic features cannot replace behavioral milestone assessments.
3. **Absence of Longitudinal EHR Markers:** Unlike the clinical cohorts in the referenced literature (e.g., Paper 1 Well-Baby data or Paper 2 Claims data), the Kaggle screening dataset lacks physical growth curves (head circumference trajectory, birth weight percentiles), gestational age in weeks, APGAR scores, and ICD-10 encounter codes.
4. **Caregiver Assessment Subjectivity:** Binary checklist responses ($A_1 \dots A_{10}$) reflect caregiver report and are vulnerable to subjectivity and recall bias compared to structured clinical observations.

---

## 8. Final Scientific Conclusions

1. **Questionnaire Threshold Reproduction is NOT Independent Diagnosis:**  
   Models trained on $A_1 \dots A_{10}$ must never be presented as discovering predictive clinical biomarkers for autism. They are automated screening cutoff scoring tools.
2. **Duplicate Leakage Eliminated:**  
   Group-based splitting successfully resolved the $11.37\%$ duplicate contamination present in naive splitting, adjusting demographic test ROC-AUC to an honest $0.6170$.
3. **External Clinical Validity Verified for Behavioral Items:**  
   When evaluated against community-based clinical diagnoses in the verified Polish toddler cohort (Niedźwiecka et al., 2020, Mendeley Data DOI: 10.17632/tmpkt2mfkg.2), questionnaire-based screening items achieve strong discriminative performance ($0.9355$ ROC-AUC, $91.45\%$ Specificity). This establishes external validity for structured behavioral questions while confirming that demographic features alone do not generalize across distinct healthcare environments without behavioral observations. Live-video and computer-vision pipelines remain separate validation targets.
4. **Platform Status:**  
   NeuroScreen AI is rigorously audited, scientifically hardened, and transparently structured to serve as an academic screening support tool in compliance with healthcare software engineering best practices.

