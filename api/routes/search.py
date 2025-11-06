from fastapi import APIRouter, HTTPException, Query
from scrapers.getSearchResults import search_tfrrs
from utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__, "api_search.log")

@router.get("/")
def search(query_type: str = Query(..., regex="^(athlete|team|meet)$"), query: str = Query(...)):
    """Search TFRRS for athletes, teams, or meets."""
    try:
        results = search_tfrrs(query_type, query)
        return {"count": len(results), "results": results}
    except Exception as e:
        logger.exception(f"Search failed for {query_type}='{query}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
