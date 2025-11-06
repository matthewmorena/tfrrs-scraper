import requests
from bs4 import BeautifulSoup
import re
import time
from utils.common import safe_decode, default_headers
from utils.logging_config import get_logger

logger = get_logger(__name__, "search_scrape.log")

BASE_URL = "https://www.tfrrs.org"

# ---------- Core Logic ---------- #

def get_authenticity_token(session):
    """Fetch homepage and extract CSRF authenticity token."""
    start = time.time()
    logger.info("Fetching authenticity token from TFRRS...")

    headers = default_headers()

    try:
        r = session.get(BASE_URL + "/", headers=headers, timeout=20)
        html = safe_decode(r.content, r.headers.get("Content-Encoding"))
        soup = BeautifulSoup(html, "lxml")

        token_input = soup.find("input", {"name": "authenticity_token"})
        if not token_input or not token_input.get("value"):
            raise ValueError("Could not find authenticity_token on homepage.")

        token = token_input["value"]
        logger.debug(f"Token fetched in {time.time() - start:.2f}s")
        return token

    except Exception as e:
        logger.error(f"Failed to fetch authenticity token: {e}")
        raise


def search_tfrrs(query_type, query_value):
    """
    Perform a TFRRS search for athletes, teams, or meets.
    Returns clean objects with IDs/slugs instead of full URLs.
    """
    if query_type not in {"athlete", "team", "meet"}:
        raise ValueError("Invalid query_type. Must be 'athlete', 'team', or 'meet'.")

    logger.info(f"Searching TFRRS for {query_type}: '{query_value}'")
    session = requests.Session()

    try:
        token = get_authenticity_token(session)
    except Exception as e:
        logger.error(f"Aborting search: unable to fetch token ({e})")
        return []

    payload = {
        "authenticity_token": token,
        "athlete": query_value if query_type == "athlete" else "",
        "team": query_value if query_type == "team" else "",
        "meet": query_value if query_type == "meet" else "",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    try:
        start = time.time()
        r = session.post(BASE_URL + "/search.html", data=payload, headers=headers, timeout=30)
        html = safe_decode(r.content, r.headers.get("Content-Encoding"))
        soup = BeautifulSoup(html, "lxml")
        logger.info(f"Search request completed in {time.time() - start:.2f}s")
    except Exception as e:
        logger.error(f"Search request failed: {e}")
        return []

    # Route to correct parser
    if query_type == "athlete":
        results = parse_athlete_results(soup)
    elif query_type == "team":
        results = parse_team_results(soup)
    else:
        results = parse_meet_results(soup)

    logger.info(f"Found {len(results)} {query_type} results for '{query_value}'")
    return results


# ---------- Parsers ---------- #

def parse_athlete_results(soup):
    results = []
    for row in soup.select("#myTable tbody tr"):
        athlete_cell = row.select_one("td#col0 a")
        team_cell = row.select_one("td#col1 a")

        if not athlete_cell or not athlete_cell.get("href"):
            continue

        # Extract athlete ID from /athletes/<id>/
        match = re.search(r"/athletes/(\d+)/", athlete_cell["href"])
        athlete_id = match.group(1) if match else None

        # Extract team slug if present
        team_slug = None
        if team_cell and team_cell.get("href"):
            m2 = re.search(r"/teams/(?:tf|xc)/([^/]+)\.html", team_cell["href"])
            team_slug = m2.group(1) if m2 else None

        results.append({
            "athlete_name": athlete_cell.text.strip(),
            "athlete_id": athlete_id,
            "team_name": team_cell.text.strip() if team_cell else None,
            "team_slug": team_slug,
        })

    logger.debug(f"Parsed {len(results)} athlete results")
    return results


def parse_team_results(soup):
    results = []
    for row in soup.select("#myTable tbody tr"):
        team_cell = row.select_one("td#col0 a")
        if not team_cell or not team_cell.get("href"):
            continue

        # Extract slug from team URL
        match = re.search(r"/teams/(?:tf|xc)/([^/]+)\.html", team_cell["href"])
        team_slug = match.group(1) if match else None

        sport_cell = row.select_one("td:nth-of-type(2)")
        gender_cell = row.select_one("td:nth-of-type(3)")

        results.append({
            "team_name": team_cell.text.strip(),
            "team_slug": team_slug,
            "sport": sport_cell.text.strip() if sport_cell else None,
            "gender": gender_cell.text.strip() if gender_cell else None,
        })

    logger.debug(f"Parsed {len(results)} team results")
    return results


def parse_meet_results(soup):
    results = []
    for row in soup.select("#myTable tbody tr"):
        meet_cell = row.select_one("td#col0 a")
        if not meet_cell or not meet_cell.get("href"):
            continue

        # Extract numeric meet ID from URL
        match = re.search(r"/results/(xc/)?(\d+)/", meet_cell["href"])
        meet_id = match.group(2) if match else None

        date_cell = row.select_one("td:nth-of-type(2)")
        sport_cell = row.select_one("td:nth-of-type(3)")

        results.append({
            "meet_name": meet_cell.text.strip(),
            "meet_id": meet_id,
            "date": date_cell.text.strip() if date_cell else None,
            "sport": sport_cell.text.strip() if sport_cell else None,
        })

    logger.debug(f"Parsed {len(results)} meet results")
    return results


# ---------- Manual Testing ---------- #

#if __name__ == "__main__":
#    try:
#        print("\nAthlete search: Nico Young")
#        athletes = search_tfrrs("athlete", "Nico Young")
#        print(f"Found {len(athletes)} athletes")
#        if athletes:
#            print(athletes[:3])

#        print("\nTeam search: Northern Arizona")
#        teams = search_tfrrs("team", "Northern Arizona")
#        print(f"Found {len(teams)} teams")
#        if teams:
#            print(teams[:3])

#        print("\nMeet search: IC4A")
#        meets = search_tfrrs("meet", "IC4A")
#        print(f"Found {len(meets)} meets")
#        if meets:
#            print(meets[:3])

#    except Exception as e:
#        logger.exception(f"Search test failed: {e}")
