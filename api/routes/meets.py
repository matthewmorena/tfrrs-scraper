from fastapi import APIRouter, HTTPException, Query
from scrapers.getMeetDetails import get_meet_results
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__, "api_meets.log")

@router.get("/{meet_id}")
def fetch_meet(
    meet_id: int,
    sport: str = Query("tf", description="Sport type: 'tf' or 'xc'"),
    gender: str = Query(None, description="Gender: 'm' or 'f' (only for track meets)"),
):
    """
    Fetch all events and results for a meet.
    - Track meets use `/results/{meet_id}/{gender}`
    - XC meets use `/results/xc/{meet_id}/m`
    """
    base_url = "https://www.tfrrs.org/results"

    # Build URL
    if sport == "xc":
        url = f"{base_url}/xc/{meet_id}/m"  # XC always uses /m
    else:
        if gender not in ("m", "f"):
            raise HTTPException(status_code=400, detail="Gender must be 'm' or 'f' for track meets.")
        url = f"{base_url}/{meet_id}/{gender}/"

    try:
        data = get_meet_results(url)
        if not data:
            raise HTTPException(status_code=404, detail="Meet not found")
        return data
    except Exception as e:
        logger.exception(f"Error fetching {sport.upper()} {gender.upper() if gender else ''} meet {meet_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
