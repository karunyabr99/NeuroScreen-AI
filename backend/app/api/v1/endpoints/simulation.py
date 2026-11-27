from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.schemas.simulation import (
    SimulationInput,
    SimulationResultResponse,
    ScenarioDefinition
)
from app.services.simulation_service import SimulationService

router = APIRouter()

@router.get(
    "/scenarios",
    response_model=List[ScenarioDefinition],
    summary="Get Preconfigured Simulation Scenarios (All Roles)"
)
def get_scenarios(
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Returns the 5 dynamic clinical research demonstration scenarios:
    Scenario A (Typical), Scenario B (Communication), Scenario C (Social),
    Scenario D (Repetitive Behaviors), Scenario E (Mixed).
    """
    return SimulationService.get_preconfigured_scenarios()


@router.post(
    "/run",
    response_model=SimulationResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Stacking Ensemble Simulation (All Roles)"
)
def run_simulation(
    payload: SimulationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """
    Executes end-to-end child screening simulation using the calibrated Stacking Ensemble:
    1. Preprocesses assessment observation parameters
    2. Runs Random Forest + SVM + Gradient Tree Boosting -> Logistic Regression Meta-Learner
    3. Calculates genuine SHAP feature attributions
    4. Persists the simulation run in SQLite database under synthetic research partition.
    """
    return SimulationService.run_simulation(
        db=db,
        inputs=payload,
        current_user=current_user
    )


@router.get(
    "/history",
    summary="Get Recent Simulation Runs (All Roles)"
)
def get_simulation_history(
    limit: int = 25,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(["Administrator", "Assessor", "Researcher"]))
):
    """Retrieves chronological history of saved simulation runs."""
    return SimulationService.get_simulation_history(db=db, limit=limit)

