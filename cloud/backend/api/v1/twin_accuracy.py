"""
Twin Accuracy Monitor API Router

Endpoints:
  GET  /twin-accuracy/stats       — accuracy metrics over time window
  GET  /twin-accuracy/history     — time-series of prediction vs. actual
  GET  /twin-accuracy/brain       — full DT Brain summary (6 physics models)
"""

from fastapi import APIRouter, Query
from core.twin_accuracy import get_accuracy_stats, get_accuracy_history, get_physics_model_summary

router = APIRouter(tags=["Twin Accuracy Monitor"])


@router.get("/twin-accuracy/stats")
async def twin_accuracy_stats(
    farm_id: str = Query("farm_001"),
    hours: int = Query(24, ge=1, le=168),
):
    """Twin accuracy statistics: overall accuracy %, MAE, RMSE, sample count."""
    return get_accuracy_stats(farm_id, hours)


@router.get("/twin-accuracy/history")
async def twin_accuracy_history(
    farm_id: str = Query("farm_001"),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(500, ge=1, le=5000),
):
    """Time-series of prediction vs actual for charting."""
    records = get_accuracy_history(farm_id, hours, limit)
    return {"farm_id": farm_id, "count": len(records), "records": records}


@router.get("/twin-accuracy/brain")
async def twin_brain(
    farm_id: str = Query("farm_001"),
    hours: int = Query(24, ge=1, le=168),
):
    """
    DT Brain: complete physics model summary with all 6 models,
    accuracy metrics, and time evolution predictions.
    """
    return get_physics_model_summary(farm_id, hours)
