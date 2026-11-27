# NeuroScreen AI 🧠
### Explainable, Multimodal Autism Spectrum Disorder (ASD) Screening-Support System

NeuroScreen AI is a full-stack clinical decision-support and screening-triaging platform developed according to the methodologies of **two research papers** and **two patent references**:
- **Research Paper 1**: Behavioral & psychometric feature modeling (digitized AQ-10, M-CHAT-R/F sub-item vectors, and response latencies).
- **Research Paper 2**: Vocal prosody profiling & acoustic biomarkers ($F_0$ pitch variability, jitter, shimmer, hesitation pause dynamics).
- **Patent Reference 1**: Dynamic visual gaze & oculomotor tracking (social region-of-interest dwell %, joint attention saccade latency, scanpath entropy).
- **Patent Reference 2**: Explainable multimodal fusion decision-support architecture (Scikit-Learn Random Forest, XGBoost, CatBoost, and PyTorch deep cross-modal fusion with **SHAP** and **LIME** local/global explanations).

> ⚠️ **Clinical & Ethical Safeguard**:
> NeuroScreen AI is strictly a **screening-support and triaging aid** and **not a diagnostic system**. It provides transparent, explainable feature-attribution vectors to assist specialists. Models are configured with modular interfaces and uncalibrated fallback states; **no fake clinical results or mock weights are fabricated**.

---

## 🏛️ System Architecture

```
neuroscreen-ai/
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── main.py               # FastAPI application & CORS configuration
│   │   ├── core/                 # App settings, SQLite SQLAlchemy engine, security
│   │   ├── models/               # SQLAlchemy ORM models (Patient, ScreeningSession, Features, Explanations, Audit)
│   │   ├── schemas/              # Pydantic v2 schemas for strict data contracts
│   │   ├── services/             # Screening, patient, and ML Bridge services
│   │   └── api/v1/endpoints/     # REST endpoints (health, patients, screenings, multimodal, explainability)
│   ├── tests/                    # Pytest test suite for API & ML verification
│   ├── requirements.txt          # Backend dependencies
│   ├── run.py                    # Local development runner
│   └── seed.py                   # Baseline research data seed script
│
├── ml_engine/                    # Machine Learning & Explainability subsystem
│   ├── config.py                 # 24 standardized multimodal biomarker definitions & normative baselines
│   ├── interfaces/               # BaseMultimodalModel, BaseFeaturePipeline, BaseExplainer
│   ├── pipelines/                # Behavioral, Visual Gaze, and Audio Prosody extraction pipelines
│   ├── models/                   # Random Forest, XGBoost, CatBoost, PyTorch Deep Fusion Network
│   ├── explainability/           # SHAP and LIME explanation engines
│   ├── registry/                 # Central ModelRegistry for dynamic discovery
│   ├── weights/                  # Directory for clinical model checkpoints (.joblib, .json, .bin, .pt)
│   ├── datasets/                 # Reference evaluation datasets
│   └── requirements.txt          # ML engine dependencies
│
└── frontend/                     # React + Vite + TypeScript application
    ├── src/
    │   ├── components/
    │   │   ├── ui/               # shadcn-styled buttons, cards, badges, progress bars, alerts
    │   │   ├── layout/           # Navbar, footer, status indicators
    │   │   ├── screening/        # Multimodal wizard, preset loader, behavioral/gaze/acoustic forms
    │   │   └── explainability/   # Interactive SHAP waterfall chart, LIME feature bar, modality breakdown
    │   ├── pages/                # Dashboard, ScreeningWizard, ResultsDetail, PatientsView, ResearchBasis
    │   ├── services/             # API client connecting to FastAPI backend
    │   ├── types/                # TypeScript interfaces
    │   └── lib/                  # Utility formatting functions
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.ts
```

---

## 💻 macOS Local Execution Guide

Open two separate Terminal windows on your Mac.

### Terminal 1: Backend Service (FastAPI)

```bash
cd "/Users/yashwanthnaikbr/Desktop/neuroscreen ai/backend"

# 1. Activate the Python virtual environment
source venv/bin/activate

# 2. (Optional) Run tests to verify backend & ML engine integrity
pytest tests/test_api.py -v

# 3. Start the FastAPI backend server
python run.py
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

### Terminal 2: Frontend Service (React + Vite + TypeScript)

```bash
cd "/Users/yashwanthnaikbr/Desktop/neuroscreen ai/frontend"

# Start the Vite development server with proxy to backend
npm run dev
```
- **Web Application**: `http://localhost:5173`

---

## 🔬 Integrating Trained ML Checkpoints in the Future

The ML engine is built with clean abstract interfaces (`BaseMultimodalModel`). To mount real trained checkpoints from future clinical trial datasets:

| Model Architecture | Expected Checkpoint File | Checkpoint Directory | Interface Class |
| :--- | :--- | :--- | :--- |
| **Random Forest** | `rf_multimodal.joblib` | `ml_engine/weights/` | `RandomForestScreeningModel` |
| **XGBoost** | `xgb_multimodal.json` | `ml_engine/weights/` | `XGBoostScreeningModel` |
| **CatBoost** | `catboost_multimodal.bin` | `ml_engine/weights/` | `CatBoostScreeningModel` |
| **PyTorch Fusion Net** | `pytorch_fusion.pt` | `ml_engine/weights/` | `PyTorchFusionScreeningModel` |

When a file is placed in `ml_engine/weights/`, the `ModelRegistry` automatically detects the weights, transitions `is_calibrated` to `True`, and switches from uncalibrated normative deviation mode to live inference probability prediction with SHAP/LIME calculation.

---

## 🧪 Verification & Testing

To run the complete automated test suite:
```bash
cd backend
source venv/bin/activate
pytest tests/test_api.py -v
```

To run the frontend production build verification:
```bash
cd frontend
npm run build
```
Both test suites pass cleanly with 100% compliance.

