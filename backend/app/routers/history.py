from fastapi import APIRouter, HTTPException
from app.services.mortgage_service import MortgageService
router = APIRouter()
@router.get("/history")
def history(limit: int = 50):
    with MortgageService() as s: return {"items": s.history(limit)}
@router.get("/history/{run_id}")
def history_detail(run_id: int):
    with MortgageService() as s:
        run = s.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run
