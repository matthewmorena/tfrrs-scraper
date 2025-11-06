from fastapi import APIRouter, HTTPException
from scrapers.getAthleteDetails import get_athlete_details
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__, "api_athletes.log")

@router.get("/{athlete_id}")
def fetch_athlete(athlete_id: int):
    """Fetch detailed athlete data by ID."""
    url = f"https://www.tfrrs.org/athletes/{athlete_id}"
    try:
        data = get_athlete_details(url)
        if not data:
            raise HTTPException(status_code=404, detail="Athlete not found")
        return data
    except Exception as e:
        logger.exception(f"Error fetching athlete {athlete_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
