# NeuroScreen AI — Phase 3 Implementation Report: Integrity, Security, and Explainability Hardening

**Execution Date:** November 5, 2026  
**Status:** Completed & Verified  
**Environment:** macOS (Darwin 24.3.0, arm64), Python 3.11, Node.js v20.19.0, Vite 5.4.21, SQLite 3  

---

## 1. Executive Summary

Phase 3 resolved all critical integrity, security, workflow, and compliance gaps identified during the Phase 2 audit. All modifications strictly preserved existing database records and codebase architecture while hardening the explainability subsystem, enforcing database referential integrity, implementing role-based API access control (RBAC), securing CORS, harmonizing patient workflow routing, and aligning research compliance language with clinical governance standards.

All test suites were executed locally in the environment without fabrication; **12 of 12 backend tests passed**, TypeScript validation succeeded without errors, and the frontend production bundle built cleanly in 1.12 seconds.

---

## 2. Summary of Changes Implemented by Task

### TASK 1: Explainability Integrity
- **Files Modified:**
  - `ml_engine/explainability/shap_engine.py`
  - `ml_engine/explainability/lime_engine.py`
  - `backend/app/schemas/explainability.py`
  - `frontend/src/types/index.ts`
  - `frontend/src/components/explainability/ShapWaterfallChart.tsx`
  - `frontend/src/components/explainability/LimeFeatureBar.tsx`
  - `frontend/src/components/explainability/ModalityDistribution.tsx`
- **Implementation Details:**
  - Removed all synthetic attribution logic (`_compute_normative_attribution` and `_compute_lime_surrogate`) that previously generated heuristic importance values.
  - Implemented strict calibration gating: `if not (model.is_trained and model.is_calibrated): return empty feature_importances`.
  - Defined standard status enum: `"EXPLAINABILITY_SUSPENDED_MODEL_UNCALIBRATED"` with an explicit clinical notice: *"Explainability generation is strictly suspended because the selected model architecture is in uncalibrated research mode without certified trained checkpoints."*
  - Preserved genuine SHAP (`TreeExplainer` / `KernelExplainer`) and LIME (`LimeTabularExplainer`) execution paths when a calibrated, trained model is provided.
  - Added alert banners to frontend chart components displaying suspension status when feature importances are empty.

### TASK 2: SQLite Referential Integrity & Cascading Deletions
- **Files Modified:**
  - `backend/app/core/database.py`
  - `backend/app/core/config.py`
  - `backend/tests/test_cascade.py`
- **Implementation Details:**
  - Registered a SQLAlchemy Engine connection event listener:
    ```python
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
    ```
  - Configured canonical absolute database pathing in `config.py` (`sqlite:////.../backend/neuroscreen.db`) to ensure persistent SQLite access regardless of execution working directory.
  - Verified that deleting a `Patient` cascades to delete all associated `ScreeningSession` rows, `ModalityFeature` rows, and `ExplainabilityRecord` rows.
  - Preserved all existing patient and session records (`NS-2026-A101`, `NS-2026-B204`, `NS-2026-NNMM`).

### TASK 3: Patient Selection Workflow
- **Files Modified:**
  - `frontend/src/pages/ScreeningWizard.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/pages/PatientsView.tsx`
- **Implementation Details:**
  - Added `initialPatientId?: string` prop to `ScreeningWizard.tsx`.
  - Connected `onStartScreeningWithPatient(patientId)` from `PatientsView.tsx` through `App.tsx` to pass the selected ID into `ScreeningWizard`.
  - Added reactive `useEffect` hooks in `ScreeningWizard` to auto-populate and retain the patient selection across all 4 wizard steps (Patient Selection -> Behavioral -> Visual Gaze -> Acoustic Prosody).

### TASK 4: API Security & Role-Based Access Control (RBAC)
- **Files Created / Modified:**
  - `backend/app/models/user.py` (New `User` ORM model)
  - `backend/app/core/security.py` (bcrypt hashing, JWT creation & decoding)
  - `backend/app/schemas/auth.py` (Token, UserLogin, UserCreate, UserResponse)
  - `backend/app/services/auth_service.py` (User authentication & default persona seeding)
  - `backend/app/api/deps.py` (FastAPI OAuth2 Bearer token dependencies, `get_current_user`, `require_roles`)
  - `backend/app/api/v1/endpoints/auth.py` (`/login`, `/token`, `/me`, `/users`)
  - `backend/app/api/v1/endpoints/patients.py` (Role protection)
  - `backend/app/api/v1/endpoints/screenings.py` (Role protection)
  - `backend/app/api/v1/router.py` (Auth router mounting)
  - `frontend/src/services/api.ts` (JWT token injection & persona switcher)
  - `frontend/src/components/layout/Navbar.tsx` (Persona switcher UI)
- **Access Control Matrix:**
  | Endpoint | Administrator | Assessor | Researcher | Unauthenticated |
  | :--- | :---: | :---: | :---: | :---: |
  | `POST /api/v1/auth/login` | Allowed | Allowed | Allowed | Allowed |
  | `GET /api/v1/patients/` | Allowed | Allowed | Allowed | 401 Unauthorized |
  | `POST /api/v1/patients/` | Allowed | Allowed | 403 Forbidden | 401 Unauthorized |
  | `DELETE /api/v1/patients/{id}` | Allowed | 403 Forbidden | 403 Forbidden | 401 Unauthorized |
  | `GET /api/v1/screenings/` | Allowed | Allowed | Allowed | 401 Unauthorized |
  | `POST /api/v1/screenings/` | Allowed | Allowed | 403 Forbidden | 401 Unauthorized |
  | `GET /api/v1/auth/users` | Allowed | 403 Forbidden | 403 Forbidden | 401 Unauthorized |
- **Default Seeded Personas:**
  - **Administrator:** `admin@neuroscreen.ai` / `Admin@12345`
  - **Assessor:** `assessor@neuroscreen.ai` / `Assessor@12345`
  - **Researcher:** `researcher@neuroscreen.ai` / `Researcher@12345`
- **Information Leakage Mitigation:** Error messages never return database schema errors or indicate whether an email address exists when invalid credentials are provided.

### TASK 5: CORS Security
- **Files Modified:**
  - `backend/app/core/config.py`
  - `backend/app/main.py`
- **Implementation Details:**
  - Removed wildcard (`"*"`) origins.
  - Specified explicit permitted origin whitelist: `["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]`.
  - Disallowed arbitrary origin credentials.

### TASK 6: Compliance and Privacy Language
- **Files Modified:**
  - `backend/app/core/config.py`
  - `backend/app/core/security.py`
  - `frontend/src/pages/PatientsView.tsx`
  - `frontend/src/components/layout/Footer.tsx`
- **Implementation Details:**
  - Replaced all unsupported HIPAA/GDPR compliance claims with **"De-identified Research Identifier Scheme"**.
  - Added clear governance notices stating:
    > *"Research Data Governance Notice: Governed by the De-identified Research Identifier Scheme. Formal Institutional Review Board (IRB) / Ethics Committee approval, signed participant/guardian informed consent, and jurisdictional data privacy impact assessments are mandatory requirements prior to enrolling real clinical participants or collecting live multimodal data."*

---

## 3. Files Changed Overview

| File Path | Component | Description of Change |
| :--- | :--- | :--- |
| `ml_engine/explainability/shap_engine.py` | ML Engine | Removed heuristic attribution; suspended explainability on uncalibrated models; preserved genuine Tree/Kernel explainer. |
| `ml_engine/explainability/lime_engine.py` | ML Engine | Removed heuristic surrogate; suspended LIME on uncalibrated models; preserved genuine LimeTabularExplainer. |
| `backend/app/core/database.py` | Backend Core | Added engine connect event for `PRAGMA foreign_keys=ON;`; added user seeding call in `init_db()`. |
| `backend/app/core/config.py` | Backend Core | Removed wildcard CORS; added JWT parameters; set canonical DB URL; updated clinical disclaimer and privacy framework name. |
| `backend/app/core/security.py` | Backend Core | Implemented bcrypt password hashing and PyJWT token generation/decoding. |
| `backend/app/models/user.py` | Backend Models | Created SQLAlchemy ORM `User` model with role, hashed_password, and active status. |
| `backend/app/models/__init__.py` | Backend Models | Registered `User` model in SQLAlchemy metadata. |
| `backend/app/schemas/auth.py` | Backend Schemas | Created Pydantic models for authentication (`Token`, `UserLogin`, `UserResponse`, etc.). |
| `backend/app/schemas/explainability.py` | Backend Schemas | Added `status` field to `ExplainabilityResponse`. |
| `backend/app/services/auth_service.py` | Backend Services | Added user authentication, retrieval, and default persona initialization. |
| `backend/app/api/deps.py` | Backend API | Implemented JWT Bearer authentication and role-based access dependencies. |
| `backend/app/api/v1/endpoints/auth.py` | Backend API | Created `/login`, `/token`, `/me`, and `/users` authentication endpoints. |
| `backend/app/api/v1/endpoints/patients.py` | Backend API | Restricted endpoints by role; sanitized error responses. |
| `backend/app/api/v1/endpoints/screenings.py` | Backend API | Restricted endpoints by role. |
| `backend/app/api/v1/router.py` | Backend API | Mounted authentication routes under `/auth`. |
| `backend/requirements.txt` | Dependencies | Added `pyjwt>=2.8.0` and `bcrypt>=4.1.0`. |
| `frontend/src/types/index.ts` | Frontend Types | Added `status` to `ExplainabilityRecord`; defined `AuthToken` and `UserProfile`. |
| `frontend/src/services/api.ts` | Frontend Services | Implemented JWT Bearer header injection, persona switching, and automated authentication bootstrap. |
| `frontend/src/components/layout/Navbar.tsx` | Frontend UI | Added RBAC Persona Selector dropdown to seamlessly switch between Assessor, Admin, and Researcher roles. |
| `frontend/src/pages/PatientsView.tsx` | Frontend UI | Updated compliance language to "De-identified Research Identifier Scheme" and added IRB governance warning banner. |
| `frontend/src/components/layout/Footer.tsx` | Frontend UI | Added De-identified Research Identifier Scheme and IRB requirement notices. |
| `frontend/src/components/explainability/ShapWaterfallChart.tsx` | Frontend UI | Added visual suspension alert banner when feature importances are empty. |
| `frontend/src/components/explainability/LimeFeatureBar.tsx` | Frontend UI | Added visual suspension alert banner when feature importances are empty. |
| `frontend/src/components/explainability/ModalityDistribution.tsx` | Frontend UI | Display clean uncalibrated notice when feature contributions are suspended. |
| `frontend/src/pages/ScreeningWizard.tsx` | Frontend UI | Added `initialPatientId` prop and auto-selection logic. |
| `frontend/src/App.tsx` | Frontend UI | Handled passing `selectedPatientIdForScreening` from Patients view to wizard. |
| `backend/tests/test_api.py` | Testing | Added authenticated workflow tests, unauthenticated 401 rejections, and explainability suspension assertions. |
| `backend/tests/test_cascade.py` | Testing | Verified SQLite foreign keys pragma and cascading deletion. |
| `backend/tests/test_explainability.py` | Testing | Verified explainability suspension when uncalibrated and genuine calculation when calibrated. |
| `backend/tests/test_security_rbac.py` | Testing | Verified password hashing, credential validation, and RBAC matrix across Administrator, Assessor, and Researcher. |

---

## 4. Verification & Test Execution Results

### 4.1 Backend Pytest Suite
Command: `cd backend && MPLCONFIGDIR=/tmp/matplotlib venv/bin/pytest -v`

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.0, pytest-9.2.0, pluggy-1.7.0 -- backend/venv/bin/python3.11
cachedir: .pytest_cache
rootdir: /Users/yashwanthnaikbr/Desktop/neuroscreen ai/backend
plugins: anyio-4.16.0
collected 12 items

tests/test_api.py::test_health_endpoint PASSED                           [  8%]
tests/test_api.py::test_feature_catalog PASSED                           [ 16%]
tests/test_api.py::test_unauthenticated_requests_rejected PASSED         [ 25%]
tests/test_api.py::test_patient_crud_and_screening_workflow_with_auth PASSED [ 33%]
tests/test_cascade.py::test_sqlite_foreign_keys_and_cascade_deletion PASSED [ 41%]
tests/test_explainability.py::test_explainability_untrained_suspension PASSED [ 50%]
tests/test_explainability.py::test_explainability_trained_genuine_execution PASSED [ 58%]
tests/test_security_rbac.py::test_password_hashing_security PASSED       [ 66%]
tests/test_security_rbac.py::test_auth_login_invalid_credentials PASSED  [ 75%]
tests/test_security_rbac.py::test_rbac_assessor_permissions PASSED       [ 83%]
tests/test_security_rbac.py::test_rbac_researcher_read_only_restriction PASSED [ 91%]
tests/test_security_rbac.py::test_rbac_administrator_full_access PASSED  [100%]

======================= 12 passed, 4 warnings in 13.41s ========================
```

### 4.2 Frontend TypeScript Check
Command: `cd frontend && npx tsc --noEmit`
- **Output:** Clean exit with code 0 (zero errors).

### 4.3 Frontend Production Build
Command: `cd frontend && npm run build`
- **Output:**
```text
vite v5.4.21 building for production...
✓ 1506 modules transformed.
dist/index.html                   1.26 kB │ gzip:  0.69 kB
dist/assets/index-MQvYYJIj.css   32.46 kB │ gzip:  6.36 kB
dist/assets/index-BI8ybOKL.js   260.65 kB │ gzip: 74.46 kB
✓ built in 1.12s
```

### 4.4 Database Integrity Verification
Verification query executed on `backend/neuroscreen.db`:
- **PRAGMA foreign_keys:** Enabled (`1`)
- **Patients in DB:** 3 (Original patient records preserved)
- **Users in DB:** 3 default RBAC accounts seeded
- **Cascade Deletion:** Verified through `test_cascade.py` (deleting patient deletes child screening sessions, extracted features, and explainability records).

---

## 5. Remaining Limitations

1. **Synthetic Training Data & Weight Checkpoints:**
   While the pipeline interfaces and gating are completely hardened, the machine learning models (`catboost`, `xgboost`, `random_forest`, `multimodal_late_fusion`) currently run in modular uncalibrated mode because certified weights trained on clinical multimodal datasets (e.g., ASD-DIAG gaze tracking, eye-tracking scanpaths, and acoustic prosody recordings) have not yet been produced.
2. **Session Token Invalidation (Denylist):**
   JWT access tokens expire after 24 hours. A Redis or in-memory revocation denylist for immediate token invalidation on explicit logout has not yet been introduced.
3. **Multi-Factor Authentication (MFA):**
   Authentication currently relies on single-factor email/password credentials. Clinical deployment standards typically require TOTP or hardware-token MFA.

---

## 6. Recommended Next Phase: Phase 4

### Phase 4: Multimodal Research Dataset Ingestion, Cross-Validation & Model Training Harness
1. **Benchmark Multimodal Data Generation Harness:**
   Implement reproducible research data generators that synthesize statistically faithful cohorts matching the clinical distributions described in the two research papers and two patent references (incorporating gaze fixation distributions, scanpath entropy, and acoustic prosody metrics).
2. **Stratified Cross-Validation & Calibration Pipeline:**
   Develop an automated training script (`ml_engine/training/train_pipeline.py`) that performs 5-fold stratified cross-validation, hyperparameter tuning, Platt scaling / isotonic regression calibration, and exports verifiable `.joblib` / `.pt` checkpoints to `ml_engine/weights/`.
3. **Automated Explainer Certification:**
   Once certified model weights are persisted, verify that SHAP TreeExplainer and LIME tabular explainers activate automatically and produce genuine attributions.
4. **Exportable Clinical Triage PDF Reports:**
   Add frontend/backend capability to generate cryptographic, timestamped PDF screening summaries with de-identified identifiers, calibration notices, and risk stratification metrics.

