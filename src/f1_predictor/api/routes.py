"""F1 Predictor 2026 — API Routes."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/circuits")
async def get_circuits():
    """Get all circuits."""
    from f1_predictor.data.circuit_data import get_all_circuits
    return {"circuits": get_all_circuits()}

@router.get("/drivers")
async def get_drivers():
    """Get all drivers."""
    from f1_predictor.data.driver_data import get_all_drivers
    return {"drivers": get_all_drivers()}
