# NeuroScreen AI – Real Video and Image Analysis Module Report

**Module Version:** `v1.5.0-vision-cv-2026-11`  
**Date:** November 5, 2026  
**Status:** Implemented, Audited & Fully Verified  
**Audit Scope:** Media Intake, Computer-Vision Behavioral Extraction, Technical Image Quality, Multimodal Triage Synthesis, Participant-Level Disjoint ML Splitting, and Mandatory Ethical Negative Constraints.

---

## 1. Executive Summary

NeuroScreen AI has been upgraded with a specialized **Real Video and Image Analysis Module** designed specifically to support clinical research and developmental triage for Autism Spectrum Disorder (ASD). The module enables authorized clinicians and researchers to securely upload, inspect, and analyze real observational child video recordings and photographs while strictly preserving research governance, participant privacy, and neurodevelopmental ethics.

### Primary Architectural Commitments
1. **Observable Behaviors Only:** All computer-vision pipelines extract task-specific, dynamic behavioral features (postural stability, gesture frequency, visual cue latency, and periodic motor stereotypies) rather than biometric identity or static appearance.
2. **Strict Negative Safeguards:** The system explicitly **refuses** to classify autism from facial photographs, facial expressions, attractiveness, or emotion recognition. It **never** generates an "autism percentage" or definitive diagnostic label.
3. **Scientific Accuracy in Gaze Tracking:** Monocular RGB webcam tracking carries an explicit disclaimer that it is **not equivalent to clinical infrared corneal-reflection eye tracking**.
4. **Research Governance & Consent Gating:** Media intake and streaming are gated by verified guardian informed consent. Ingestion is blocked if consent is pending, and access is immediately quarantined if consent is withdrawn.
5. **Separation of Machine Learning Training:** Media files are never automatically used for machine learning. A separate explicit authorization flag (`media_training_authorized`) is legally and architecturally required.
6. **Disjoint Participant-Level Splitting:** ML cross-validation folds strictly group data by participant identifier (`participant_id`), guaranteeing zero leakage of frames or sessions across train and evaluation partitions.

---

## 2. Media Upload & Privacy Architecture

### Supported Media Formats & Physical Validation
| Modality | Permitted File Formats | Maximum Permissible Size | Duration / Resolution Bounds | Storage Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Video** | `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv` | 100 MB | 3.0 to 600.0 seconds (10 min) | Private disk storage (`backend/storage/media/`) |
| **Image** | `.jpg`, `.jpeg`, `.png`, `.webp` | 15 MB | Minimum 128x128 px | Private disk storage (`backend/storage/media/`) |

### Privacy & Access Controls
* **Non-Public Storage:** Media files are stored using cryptographically random UUID filenames inside `backend/storage/media/`. No public static route is ever exposed.
* **Authenticated Streaming Gateway (`GET /api/v1/media/{media_id}/stream`):**
  * Caller must present a valid JWT bearer token with authorized role (`Administrator`, `Assessor`, or `Researcher`).
  * Participant record is verified in the database: if `consent_status == "withdrawn"`, stream access returns `403 Forbidden` and is quarantined.
  * Security headers enforce privacy: `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store, max-age=0`.
* **Immutable Audit Trail:** All uploads, streams, behavioral analyses, and deletions are recorded in `AuditLog` with timestamps, actor credentials, and participant IDs.

---

## 3. Observable Computer-Vision Behavioral Pipeline (`VideoBehavioralAnalyzer`)

Implemented in `ml_engine/vision/video_analyzer.py`, this module analyzes temporal frame sequences from task-based observational sessions:

### 1. Body Pose & Movement Patterns
* **Gross Motor Activity Level:** Calculated from normalized frame-differencing motion energy across temporal windows (`low`, `moderate`, `elevated`, or `intense_motor_activity`).
* **Postural Stability Index:** Computes upper-body center-of-mass dispersion and spatial variance ($0.0$ to $1.0$).
* **Motion Energy Entropy:** Quantifies the predictability and entropy of spatial displacement patterns over time.

### 2. Gesture and Action Dynamics
* **Pointing & Reaching Frequency:** Tracks proto-declarative reaching events per minute during structured stimulus presentation.
* **Manual Interaction Classification:** Distinguishes active object manipulation from ambient postures.
* **Visual Motor Latency:** Measures the interval between stimulus presentation and physical manual orientation.

### 3. Coarse Gaze Direction & Webcam Non-Equivalence
* **Head Pose & Fixation Proxy:** Approximates coarse head yaw and pitch orientation toward activity zones (tabletop, examiner, stimulus target).
* **Fixation Stability Ratio:** Quantifies sustained visual orientation toward designated targets.
* **Mandatory Caveat:** Explicitly flags `webcam_infrared_equivalence_claimed = False` and outputs:
  > *"Non-invasive monocular webcam tracking cannot replicate high-speed (300–1200 Hz) infrared eye-tracking pupillometry, micro-saccadic kinematics, or corneal reflection accuracy."*

### 4. Joint Attention Task Observations
* **Examiner Visual Cue Shift Latency:** Quantifies orientation shift latency in milliseconds when the examiner delivers a structured social cue.
* **Classification Categories:** `prompt_response` (< 1500 ms), `delayed_shift` (1500–3500 ms), or `minimal_response` (> 3500 ms).
* **Shared Engagement Duration:** Measures cumulative seconds of mutual focus on structured activity materials.

### 5. Repetitive Movement Rhythmicity (Motor Stereotypies)
* **Autocorrelation & Fourier Spectral Analysis:** Isolates motor oscillations in the clinical stereotypy frequency band ($1.5 \text{ to } 4.0\text{ Hz}$).
* **Rhythmicity Index ($0.0 \text{ to } 1.0$):** Measures the peak periodicity of repetitive upper-limb or body oscillations.
* **Periodic Stereotypy Burst Detection:** Identifies continuous periodic movement sequences exceeding 3 consecutive cycles.

### 6. Social Interaction Opportunities
* **Structured Opportunity Windows:** Quantifies naturalistic social response opportunities provided by the examiner or educator.
* **Mutual Interaction Events:** Counts reciprocal engagement events during structured turn-taking activities.

---

## 4. Photographic Quality & Scene Context Pipeline (`ImageQualityAndContextAnalyzer`)

Implemented in `ml_engine/vision/image_analyzer.py`, this pipeline processes still photographs exclusively for environmental and technical quality verification:

### Technical Quality Metrics
1. **Sharpness via Discrete Laplacian Variance:** Computes $\nabla^2 I$ variance over grayscale luminance arrays. Categorizes image as `sharp` ($\ge 200$), `adequate` ($80 - 200$), or `blurred` ($< 80$).
2. **Mean Luminance & RMS Contrast:** Evaluates lighting balance, clipping ratios, and detects underexposure or overexposure.
3. **Composite Data Quality Score ($0.10 \text{ to } 1.00$):** Informs clinicians whether an observational photograph possesses adequate technical fidelity.

### Observable Environmental Setting
* Evaluates spatial clutter and quadrant color variance to classify the assessment setting:
  * `structured_tabletop_assessment`
  * `free_play_mat_area`
  * `inclusive_classroom_station`
  * `structured_clinical_or_assessment_room`

---

## 5. Absolute Scientific & Ethical Negative Constraints

Every execution of `analyze_video()` and `analyze_image()` embeds verified audit flags:

```json
{
  "facial_autism_inference_attempted": false,
  "facial_appearance_or_attractiveness_evaluated": false,
  "facial_emotion_recognition_used": false,
  "photograph_autism_classification_attempted": false,
  "autism_severity_percentage_generated": false,
  "webcam_infrared_equivalence_claimed": false,
  "diagnostic_claim_made": false
}
```

### Prohibited Practices & Enforced Countermeasures
| Prohibited AI Practice | System Countermeasure | Rationale |
| :--- | :--- | :--- |
| **Facial Autism Diagnosis** | Pipeline explicitly refuses facial feature extraction or classification; returns `photographic_autism_classification_performed: False`. | Autism is a complex neurodevelopmental profile of behavior and social communication; static facial morphology has no valid diagnostic basis. |
| **Emotion Recognition Diagnosis** | Pipeline omits emotion recognition from diagnostic triage. | Autistic facial affect expression is heterogeneous and neurodivergent; automated emotion classification introduces severe clinical bias. |
| **Autism Severity Percentages** | System generates descriptive triage categories instead of percentages. | Clinical autism is heterogeneous and non-linear; expressing diagnosis as a percentage is scientifically invalid and clinically misleading. |
| **Webcam = Eye-Tracker Claims** | Explicit warning badge and audit flag attached to all gaze metrics. | Ordinary monocular RGB cameras lack corneal reflection LEDs, high sample rates, and calibration necessary for clinical pupillometry. |

---

## 6. Multimodal Screening Triage Synthesis

The synthesis engine (`MediaService.synthesize_multimodal_screening`) combines video-derived parameters with multi-informant assessment data while keeping each information source strictly identifiable:

1. **Source A (Computer Vision):** Objective behavioral metrics (pose stability, joint attention latency, motor rhythmicity).
2. **Source B (Developmental Milestones):** Language onset, motor milestones, response to name.
3. **Source C (Caregiver Observations):** Structured questionnaire responses, prominently flagged:
   > *"Descriptive parent report; does NOT constitute a confirmed clinical diagnosis."*
4. **Source D (Teacher / Therapist Observations):** Classroom peer interaction and transition observations.
5. **Source E (Qualified Professional Clinical Findings):** Formal evaluator observation notes or pending status.

### Screening Support Categories (Non-Diagnostic)
* **Category 1:** `Elevated Behavioral Indicators Observed - Priority Clinical Referral Recommended`
* **Category 2:** `Moderate Variation Observed - In-Person Assessment Recommended`
* **Category 3:** `Behavioral Parameters Age-Expected - Routine Developmental Monitoring`

### Mandatory Clinical Referral
Every report mandates in-person evaluation:
> *"Direct in-person multidisciplinary clinical evaluation (e.g., ADOS-2, ADI-R) by qualified licensed specialists (pediatric neurologist, child clinical psychologist, speech-language pathologist) is required."*

---

## 7. Machine Learning Methodology: Participant-Level Disjoint Splitting

Implemented in `ml_engine/vision/model_evaluation.py` (`ParticipantLevelVisionDatasetSplitter`):

### 1. Frame and Participant Leakage Prevention
* Standard frame-level or session-level random splitting allows frames from the same child to appear in both training and testing folds, artificially inflating accuracy scores to $>95\%$.
* NeuroScreen AI enforces `StratifiedGroupKFold` / `GroupKFold` grouped strictly by `participant_id`.
* The splitter runs a mandatory assertion checking that $\text{TrainParticipants} \cap \text{TestParticipants} = \emptyset$.

### 2. Comprehensive Clinical Metrics
* **Sensitivity (Recall):** $\frac{\text{TP}}{\text{TP} + \text{FN}}$
* **Specificity (True Negative Rate):** $\frac{\text{TN}}{\text{TN} + \text{FP}}$
* **Precision (PPV):** $\frac{\text{TP}}{\text{TP} + \text{FP}}$
* **F1-Score:** $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$
* **ROC-AUC & PR-AUC:** Discrimination ability across probability thresholds.
* **Brier Score Loss & Calibration Curve:** Evaluates probability calibration error.
* **95% Bootstrap Confidence Intervals:** Non-parametric resampling ($N=200$) reporting empirical 2.5th and 97.5th percentiles.

---

## 8. Frontend Implementation: Video & Media CV Studio

The React interface (`frontend/src/pages/VideoAnalysisDashboard.tsx`) provides:
1. **Participant Governance Bar:** Displays anonymized ID, age, and verified guardian consent badge (`Granted`, `Pending`, or `Withdrawn`).
2. **Upload Studio:** File dropzone supporting video/photo, protocol context selector, and an explicit ML training authorization checkbox.
3. **Encrypted Media Gallery:** Lists recordings with technical quality tags (`Validated High`, `Validated Adequate`, `Low Resolution`).
4. **Authenticated Player:** Securely renders HTML5 video or image via authenticated binary blob streaming.
5. **Behavioral Feature Cards:** Interactive breakdowns of movement stability, stereotypy frequency bands, joint-attention latency, and coarse gaze orientation.
6. **Ethical Safeguard Banner:** Prominently alerts assessors of prohibited automated facial diagnostic claims.
7. **Multimodal Synthesis View:** Displays cross-modality triage categories, confidence intervals, and recommended clinical referral steps.

---

## 9. Test Verification & Suite Results

### 1. Backend Pytest Execution (`test_media_analysis.py` + Full Suite)
Command: `cd backend && MPLCONFIGDIR=/tmp/matplotlib venv/bin/pytest -v`

| Test Name | Module Tested | Verification Criteria | Status |
| :--- | :--- | :--- | :--- |
| `test_media_upload_requires_granted_consent` | Consent Gating | Blocks upload when consent is pending (403 Forbidden) | **PASSED** |
| `test_media_upload_succeeds_with_granted_consent` | Media Upload | Saves file, creates DB record, verifies file size | **PASSED** |
| `test_media_upload_rejects_invalid_file_format` | Format Validation | Rejects `.exe` or unsupported containers (400 Bad Request) | **PASSED** |
| `test_media_upload_requires_authentication` | RBAC Security | Rejects unauthenticated upload attempts (401 Unauthorized) | **PASSED** |
| `test_video_behavioral_analyzer_negative_constraints` | Vision Engine | Verifies all 7 ethical negative constraints are strictly enforced | **PASSED** |
| `test_image_analyzer_quality_and_ethical_refusal` | Image Analysis | Computes Laplacian sharpness, refuses facial classification | **PASSED** |
| `test_authenticated_streaming_and_quarantine_on_withdrawal` | Privacy Gateway | Streams with security headers; quarantines on consent withdrawal | **PASSED** |
| `test_media_analysis_and_multimodal_synthesis` | Triage Synthesis | Combines video features, milestones, caregiver notes | **PASSED** |
| `test_secure_media_deletion_and_audit` | Data Governance | Deletes disk file, cascades DB records, logs `MEDIA_DELETED` | **PASSED** |
| `test_participant_level_vision_dataset_splitter` | ML Splitting | Proves zero participant leakage across cross-validation folds | **PASSED** |
| **All Previous Tests (Phases 1-4)** | Core Full-Stack | 21 existing tests across auth, RBAC, cascade, explainability | **PASSED** |
| **Total Backend Test Suite** | Full Project | **31 passed, 0 failed** in 31.50s | **PASSED** |

### 2. Frontend TypeScript & Production Build
Commands:
* `cd frontend && npx tsc --noEmit` $\rightarrow$ **0 errors** (Code 0)
* `cd frontend && npm run build` $\rightarrow$ **Built in 1.27s** (dist/index.html, dist/assets/index.css, dist/assets/index.js)

---

## 10. Summary of Deliverables

1. `ml_engine/vision/video_analyzer.py` – Complete video behavioral computer vision analyzer with negative constraints.
2. `ml_engine/vision/image_analyzer.py` – Technical image quality and scene context analyzer with photographic refusal safeguards.
3. `ml_engine/vision/model_evaluation.py` – Participant-level disjoint cross-validation splitter and bootstrap clinical metrics evaluator.
4. `backend/app/models/media.py` – Database ORM models for `MediaUpload` and `MediaAnalysis`.
5. `backend/app/schemas/media.py` – Pydantic schemas for upload, trigger request, analysis response, and multimodal screening response.
6. `backend/app/services/media_service.py` – Secure disk storage, consent gating, streaming gateway, deletion, and multimodal synthesis.
7. `backend/app/api/v1/endpoints/media.py` – FastAPI REST endpoints mounted at `/api/v1/media`.
8. `frontend/src/types/index.ts` & `frontend/src/services/api.ts` – Frontend TypeScript types and authenticated API methods.
9. `frontend/src/pages/VideoAnalysisDashboard.tsx` – Full-featured React analysis dashboard with video/photo player, feature cards, and synthesis.
10. `frontend/src/components/layout/Navbar.tsx` & `frontend/src/App.tsx` – Navigation and routing updates.
11. `backend/tests/test_media_analysis.py` – Complete automated test suite covering all modules.
12. `VIDEO_IMAGE_ANALYSIS_REPORT.md` – Scientific and technical implementation documentation.

