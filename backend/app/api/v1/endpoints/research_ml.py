import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query, status

from ml_engine.data_loader import DatasetLoader
from ml_engine.leakage_audit import LeakageAuditor
from ml_engine.train_research_models import execute_full_training
from ml_engine.prediction_service import ResearchPredictionService
from ml_engine.model_registry import ResearchModelRegistry
from app.schemas.research_ml import (
    DatasetPreviewResponse,
    TrainModelsRequest,
    ChildPredictionRequest,
    ChildPredictionResponse
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[5]
DATASETS_DIR = BASE_DIR / "ml_engine" / "datasets"
WEIGHTS_DIR = BASE_DIR / "ml_engine" / "weights" / "research_ml"
DEFAULT_DATASET = DATASETS_DIR / "toddler_autism_dataset_july_2018.csv"

# In-memory training status tracker
_training_state: Dict[str, Any] = {
    "status": "idle",  # "idle" | "running" | "completed" | "failed"
    "progress_percent": 0,
    "current_stage": "",
    "logs": [],
    "last_completed_at": None,
    "error": None
}


@router.post("/upload-dataset", summary="Upload research autism screening CSV dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset (e.g. Kaggle Autism Screening Data for Toddlers)
    for model training and evaluation.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported."
        )

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATASETS_DIR / f"uploaded_{file.filename}"

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Immediately inspect to verify validity
    try:
        df = DatasetLoader.load_csv(destination)
        inspection = DatasetLoader.inspect_dataset(df)
        _, audit_summary = LeakageAuditor.audit_and_clean(df, target_col=inspection["identified_target"] or "Class/ASD Traits")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse uploaded CSV: {str(e)}"
        )

    return {
        "message": "Dataset uploaded and validated successfully.",
        "filename": destination.name,
        "row_count": inspection["row_count"],
        "column_count": inspection["column_count"],
        "identified_target": inspection["identified_target"],
        "leakage_columns_detected": audit_summary["dropped_columns"]
    }


@router.get("/datasets", summary="List all available screening research datasets")
def list_datasets():
    """
    Returns the list of available screening datasets in the ml_engine/datasets directory.
    """
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    datasets = []

    catalog = {
        "toddler_autism_dataset_july_2018.csv": {
            "title": "Primary Toddler ASD Screening Dataset",
            "source": "Kaggle / Fadi Thabtah (July 2018)",
            "cohort": "Toddlers (12–36 months)",
            "description": "Primary benchmark dataset containing 1,054 records with 10 Q-CHAT items and demographic features.",
            "is_default": True
        },
        "Autism_Screening_Data_Combined.csv": {
            "title": "Combined Multi-Group Autism Screening Dataset",
            "source": "Multi-Age Cohorts Screening Benchmark",
            "cohort": "Multi-Age (Toddlers, Children, Adolescents, Adults)",
            "description": "Large cross-age cohort screening dataset with 6,075 records across developmental stages.",
            "is_default": False
        },
        "Autism-Adult-Data.csv": {
            "title": "Adult ASD Screening Dataset (CSV)",
            "source": "UCI ML Repository / Fadi Thabtah (2017)",
            "cohort": "Adults (18+ years)",
            "description": "Standardized adult autism screening dataset with 704 records and 20 clinical/demographic features.",
            "is_default": False
        },
        "Autism-Adult-Data.arff": {
            "title": "Adult ASD Screening Dataset (WEKA ARFF)",
            "source": "UCI ML Repository / WEKA Benchmark",
            "cohort": "Adults (18+ years)",
            "description": "Original WEKA attribute-relation format benchmark for adult autism spectrum screening.",
            "is_default": False
        },
        "QCHAT_dataset2_mendeley.sav": {
            "title": "Polish Toddler Q-CHAT Cohort (SPSS .sav)",
            "source": "Mendeley Data DOI: 10.17632/tmpkt2mfkg.2 (SYNAPSIS Foundation)",
            "cohort": "Toddlers (14–35 months)",
            "description": "External clinical validation dataset with 252 records (135 ASD, 117 controls) with genuine clinical diagnoses.",
            "is_default": False
        },
        "polish_toddler_qchat.sav": {
            "title": "Polish Toddler External Validation Dataset (.sav)",
            "source": "Mendeley Data DOI: 10.17632/tmpkt2mfkg.2",
            "cohort": "Toddlers (14–35 months)",
            "description": "External validation cohort used for independent out-of-distribution evaluation of research models.",
            "is_default": False
        }
    }

    seen = set()
    for p in sorted(DATASETS_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in ['.csv', '.arff', '.sav']:
            fn = p.name
            # If an un-prefixed version exists, ignore the uploaded_ duplicate
            if fn.startswith('uploaded_') and (DATASETS_DIR / fn.replace('uploaded_', '')).exists():
                continue
            if fn in seen:
                continue
            seen.add(fn)
            meta = catalog.get(fn, {
                "title": fn,
                "source": "Local Upload / User Provided",
                "cohort": "Clinical Screening Cohort",
                "description": f"Dataset file {fn} with size {p.stat().st_size:,} bytes.",
                "is_default": fn == "toddler_autism_dataset_july_2018.csv"
            })
            datasets.append({
                "filename": fn,
                "title": meta["title"],
                "source": meta["source"],
                "cohort": meta["cohort"],
                "description": meta["description"],
                "file_size_bytes": p.stat().st_size,
                "format": p.suffix.lower().replace('.', '').upper(),
                "is_default": meta.get("is_default", False)
            })

    return {"datasets": datasets, "default_dataset": "toddler_autism_dataset_july_2018.csv"}


@router.get("/preview-dataset", response_model=DatasetPreviewResponse, summary="Preview and audit screening dataset")
@router.post("/preview-dataset", response_model=DatasetPreviewResponse, summary="Preview and audit screening dataset")
def preview_dataset(dataset_name: Optional[str] = Query(None)):
    """
    Preview dataset schema, analyze missing values, detect duplicates, evaluate
    class balance, and audit for target leakage (e.g. Case_No and Qchat-10-Score).
    """
    target_path = DEFAULT_DATASET
    if dataset_name:
        candidate = DATASETS_DIR / dataset_name
        if candidate.exists():
            target_path = candidate

    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found at {target_path}"
        )

    df = DatasetLoader.load_csv(target_path)
    inspection = DatasetLoader.inspect_dataset(df)

    target_col = inspection["identified_target"] or "Class/ASD Traits"
    if target_col in df.columns:
        _, audit_summary = LeakageAuditor.audit_and_clean(df, target_col=target_col)
        inspection["target_leakage_audit"] = audit_summary
    else:
        inspection["target_leakage_audit"] = None

    return inspection


def _run_background_training(dataset_path: Path):
    global _training_state
    _training_state["status"] = "running"
    _training_state["progress_percent"] = 10
    _training_state["logs"] = ["Initiating full research training pipeline..."]
    _training_state["error"] = None

    def log_cb(msg: str):
        _training_state["logs"].append(msg)
        if len(_training_state["logs"]) > 200:
            _training_state["logs"] = _training_state["logs"][-200:]

    try:
        execute_full_training(dataset_path=dataset_path, log_callback=log_cb)
        _training_state["status"] = "completed"
        _training_state["progress_percent"] = 100
        _training_state["last_completed_at"] = json.loads(
            (WEIGHTS_DIR / "research_ml_metadata.json").read_text()
        ).get("timestamp")
    except Exception as e:
        _training_state["status"] = "failed"
        _training_state["error"] = str(e)
        log_cb(f"Error during training: {str(e)}")


@router.post("/train", summary="Train CatBoost, Random Forest, and LASSO Logistic Regression")
def trigger_training(
    background_tasks: BackgroundTasks,
    payload: Optional[TrainModelsRequest] = None
):
    """
    Triggers end-to-end model training following Paper 1 (2024) and Paper 2 (2022) methodologies.
    Trains CatBoost with Youden threshold & SHAP, Random Forest, and LASSO Logistic Regression.
    """
    global _training_state
    if _training_state["status"] == "running":
        return {
            "message": "Training is already in progress.",
            "status": "running",
            "progress_percent": _training_state["progress_percent"]
        }

    dataset_path = DEFAULT_DATASET
    if payload and payload.dataset_name:
        candidate = DATASETS_DIR / payload.dataset_name
        if candidate.exists():
            dataset_path = candidate

    # Execute directly or via background task
    if background_tasks:
        background_tasks.add_task(_run_background_training, dataset_path)
        return {
            "message": "Training job initiated in background.",
            "status": "running",
            "dataset_used": dataset_path.name
        }
    else:
        # Synchronous execution
        _training_state["status"] = "running"
        _training_state["logs"] = []
        try:
            summary = execute_full_training(
                dataset_path=dataset_path,
                log_callback=lambda msg: _training_state["logs"].append(msg)
            )
            _training_state["status"] = "completed"
            _training_state["progress_percent"] = 100
            _training_state["last_completed_at"] = summary.get("timestamp")
            return {
                "message": "Training completed successfully.",
                "status": "completed",
                "summary": summary
            }
        except Exception as e:
            _training_state["status"] = "failed"
            _training_state["error"] = str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {str(e)}"
            )


@router.get("/training-status", summary="Check model training status and live logs")
def get_training_status():
    """
    Returns current training status, progress, and logs.
    """
    meta_file = WEIGHTS_DIR / "research_ml_metadata.json"
    is_trained = meta_file.exists()
    return {
        **_training_state,
        "is_model_artifact_available": is_trained,
        "models_available": ResearchModelRegistry.list_available_models()
    }


@router.get("/models/comparison", summary="Side-by-side evaluation comparison across all 3 models")
def get_model_comparison():
    """
    Returns side-by-side performance metrics, ROC curves, PR curves,
    confusion matrices, and feature selections for CatBoost, Random Forest, and LASSO.
    """
    meta_file = WEIGHTS_DIR / "research_ml_metadata.json"
    if not meta_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model comparison artifacts not found. Please train models first."
        )

    with open(meta_file, "r") as f:
        data = json.load(f)

    return data


@router.get("/models/{model_name}/explainability", summary="Model feature importance / SHAP explainer data")
def get_model_explainability(model_name: str):
    """
    Returns global explainability data (SHAP for CatBoost, Gini for RF, coefficients for LASSO).
    """
    meta_file = WEIGHTS_DIR / "research_ml_metadata.json"
    if not meta_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata not found."
        )

    with open(meta_file, "r") as f:
        meta = json.load(f)

    clean_key = model_name.lower().strip()
    if clean_key == "catboost":
        return {
            "model": "CatBoost (Paper 1, 2024)",
            "method": "SHAP (TreeExplainer)",
            "youden_threshold": meta.get("catboost", {}).get("youden_threshold"),
            "shap_summary": meta.get("catboost", {}).get("shap_summary", {})
        }
    elif clean_key == "random_forest":
        return {
            "model": "Random Forest (Paper 2, 2022)",
            "method": "Gini Impurity Feature Importance",
            "feature_importance": meta.get("random_forest", {}).get("feature_importance", [])
        }
    elif clean_key in ["lasso_logistic", "logistic_regression", "lasso"]:
        return {
            "model": "LASSO Logistic Regression (Paper 2, 2022)",
            "method": "L1 Non-Zero Standardized Coefficients",
            "lasso_selected_features_count": meta.get("lasso_logistic", {}).get("lasso_selected_features_count"),
            "total_initial_features": meta.get("lasso_logistic", {}).get("total_initial_features"),
            "selected_features": meta.get("lasso_logistic", {}).get("lasso_selected_features", []),
            "top_coefficients": meta.get("lasso_logistic", {}).get("top_coefficients", [])
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model '{model_name}'. Choose from: catboost, random_forest, lasso_logistic."
        )


@router.post("/predict", response_model=ChildPredictionResponse, summary="Run screening prediction on child profile")
def predict_child(payload: ChildPredictionRequest):
    """
    Execute child screening prediction with strict age gating:
    - Under 12 months: Suspends ML probability (OBSERVATION_ONLY_UNDER_12M).
    - 12-36 months: Runs selected research model (CatBoost by default with Youden threshold).
    - Computes genuine explainability (SHAP waterfall / LASSO coefficients).
    """
    pred_service = ResearchPredictionService.get_instance()
    assessment_dict = payload.model_dump()

    result = pred_service.predict_child(
        assessment_data=assessment_dict,
        model_name=payload.model_name or "catboost"
    )

    return result
