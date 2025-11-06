from fastapi import APIRouter, HTTPException
from scrapers.getTeamRoster import get_team_roster
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__, "api_teams.log")

@router.get("/{sport}/{slug}")
def fetch_team(sport: str, slug: str):
    """Fetch team roster and metadata."""
    url = f"https://www.tfrrs.org/teams/{sport}/{slug}.html"
    try:
        data = get_team_roster(url)
        if not data:
            raise HTTPException(status_code=404, detail="Team not found")
        return data
    except Exception as e:
        logger.exception(f"Error fetching team {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
