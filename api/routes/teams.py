from fastapi import APIRouter, HTTPException
from scrapers.getTeamRoster import get_team_roster
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__, "api_teams.log")

@router.get("/{team_slug}")
def fetch_team(team_slug: str, sport: str = "tf"):
    """Fetch team roster for either TF or XC."""
    try:
        # Build the correct TFRRS URL
        if sport not in ("tf", "xc"):
            raise HTTPException(status_code=400, detail="Invalid sport type. Must be 'tf' or 'xc'.")

        team_url = f"https://www.tfrrs.org/teams/{sport}/{team_slug}.html"
        logger.info(f"Fetching team roster: {team_url}")

        data = get_team_roster(team_url)
        if not data:
            raise HTTPException(status_code=404, detail="Team not found")

        return data

    except Exception as e:
        logger.exception(f"Error fetching team {team_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
