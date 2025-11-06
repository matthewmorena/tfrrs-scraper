import requests
from bs4 import BeautifulSoup
import re
import time
from utils.common import safe_decode, default_headers
from utils.logging_config import get_logger

logger = get_logger(__name__, "team_scrape.log")

# ---------- Core Logic ---------- #

def get_team_roster(team_url: str):
    """
    Scrape a TFRRS team page.
    Extracts:
        - team_name
        - sport_type (tf or xc)
        - conference
        - region
        - roster: list of athletes (athlete_id, name, year)
    """
    if not team_url.startswith("http"):
        team_url = "https://www.tfrrs.org" + team_url

    logger.info(f"Fetching team roster: {team_url}")

    # Derive sport type from URL (e.g., /teams/tf/... or /teams/xc/...)
    sport_match = re.search(r"/teams/(tf|xc)/", team_url)
    sport_type = sport_match.group(1) if sport_match else None

    session = requests.Session()
    headers = default_headers()

    start = time.time()
    try:
        r = session.get(team_url, headers=headers, timeout=30)
        html = safe_decode(r.content, r.headers.get("Content-Encoding"))
    except Exception as e:
        logger.error(f"Failed to fetch team page: {e}")
        return None

    soup = BeautifulSoup(html, "lxml")

    # ---------- Team name ----------
    team_name_el = soup.select_one("h3.panel-title.large-title, h3.panel-title")
    team_name = team_name_el.get_text(strip=True) if team_name_el else None

    # ---------- Conference / Region ----------
    conference = None
    region = None

    league_links = soup.select(".panel-second-title a[href*='/leagues/']")
    if league_links:
        # Sometimes one or both appear
        if len(league_links) >= 1:
            conference = league_links[0].get_text(strip=True)
        if len(league_links) >= 2:
            region = league_links[1].get_text(strip=True)

    # ---------- Roster Table ----------
    roster_table = soup.select_one("table.tablesaw")
    if not roster_table:
        logger.warning(f"No roster table found for {team_url}")
        return {
            "team_name": team_name,
            "sport_type": sport_type,
            "conference": conference,
            "region": region,
            "roster": []
        }

    roster = []
    for tr in roster_table.select("tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue

        name_cell = cells[0]
        year_cell = cells[1]
        athlete_link = name_cell.select_one("a")

        athlete_name = athlete_link.get_text(strip=True) if athlete_link else name_cell.get_text(strip=True)
        athlete_url = athlete_link["href"] if athlete_link else None

        athlete_id = None
        if athlete_url:
            match = re.search(r"/athletes/(\d+)/", athlete_url)
            if match:
                athlete_id = match.group(1)

        year = year_cell.get_text(strip=True)

        roster.append({
            "athlete_name": athlete_name,
            "athlete_id": athlete_id,
            "year": year
        })

    logger.info(f"Parsed roster for {team_name} ({len(roster)} athletes, {sport_type.upper()}) in {time.time() - start:.2f}s")

    return {
        "team_name": team_name,
        "sport_type": sport_type,
        "conference": conference,
        "region": region,
        "roster": roster
    }


# ---------- Manual Testing ---------- #

#if __name__ == "__main__":
#    data = get_team_roster("https://www.tfrrs.org/teams/xc/OR_college_m_Oregon.html")
#    print("Team:", data["team_name"])
#    print("Sport Type:", data["sport_type"])
#    print("Conference:", data["conference"])
#    print("Region:", data["region"])
#    print("Roster size:", len(data["roster"]))
#    print("Sample athletes:", data["roster"][:5])
