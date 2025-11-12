import requests
from bs4 import BeautifulSoup
import re
import time
from utils.common import safe_decode, extract_meet_id, extract_team_slug, default_headers
from utils.logging_config import get_logger

logger = get_logger(__name__, "athlete_scrape.log")

# ---------- Core Parsing Functions ---------- #

def parse_name_and_year(raw_name: str):
    """Split athlete name into (clean_name, class_year)."""
    if not raw_name:
        return None, None

    match = re.search(r"\(([^)]*)\)", raw_name)
    year_info = match.group(1).strip() if match else None
    name_only = re.sub(r"\([^)]*\)", "", raw_name).strip()

    if name_only.isupper():
        name_only = name_only.title()
    name_only = " ".join(name_only.split())
    return name_only, year_info

def extract_name_and_teams(soup):
    """Extract athlete name, year, and current/previous team info."""
    name_el = soup.select_one("h3.panel-title.large-title")
    raw_name = name_el.get_text(" ", strip=True) if name_el else None
    athlete_name, class_year = parse_name_and_year(raw_name)

    if not athlete_name:
        logger.warning("Athlete name not found on page.")
    else:
        logger.debug(f"Parsed athlete: {athlete_name} ({class_year})")

    # --- Current Team (Name + Slug + Gender) ---
    current_team_slug = None
    current_team_name = None
    gender = None

    # Find anchor containing the current team slug and team name <h3>
    team_anchor = soup.select_one("a[href*='/teams/'] h3.panel-title")
    if team_anchor:
        parent_a = team_anchor.find_parent("a", href=True)
        if parent_a:
            href = parent_a["href"]
            current_team_slug = extract_team_slug(href)
            current_team_name = team_anchor.get_text(strip=True)

            # Infer gender from slug
            if "_m_" in current_team_slug.lower():
                gender = "Male"
            elif "_f_" in current_team_slug.lower():
                gender = "Female"
            else:
                gender = "Unknown"

            logger.debug(
                f"Current team: {current_team_name} (slug={current_team_slug}, gender={gender})"
            )

    # --- Previous Teams ---
    previous_team_slugs = []
    prev_container = soup.select_one(".panel-second-title div.float-right")
    if prev_container:
        for a in prev_container.select("a[href]"):
            slug = extract_team_slug(a["href"])
            if slug:
                previous_team_slugs.append(slug)
        if previous_team_slugs:
            logger.debug(f"Previous team slugs: {previous_team_slugs}")

    return athlete_name, class_year, current_team_slug, current_team_name, gender, previous_team_slugs


def extract_athlete_results(soup):
    """Extract all non-relay meet results for an athlete."""
    results = []
    for table in soup.select("div#meet-results table.table-hover"):
        header = table.find("thead")
        if not header:
            continue

        meet_link = header.find("a", href=True)
        meet_name = meet_link.get_text(strip=True) if meet_link else None
        meet_url = meet_link["href"] if meet_link else None
        meet_id = extract_meet_id(meet_url)

        if "/xc/" in meet_url:
            meet_type = "xc"
        else:
            meet_type = "tf"

        date_span = header.find("span")
        meet_date = date_span.get_text(strip=True) if date_span else None

        for row in table.select("tr"):
            if row.find_parent("thead"):
                continue

            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            # Skip relays, para, and field events
            exclude_keywords = [
                "relay", "x", "para", "jump", "vault", "shot", "discus",
                "hammer", "javelin", "weight", "athlon"
            ]
            event_name = cols[0].get_text(strip=True)
            if event_name and any(k in event_name.lower() for k in exclude_keywords):
                logger.debug(f"Skipping relay event: {event_name}")
                continue

            mark = cols[1].get_text(strip=True)
            place = cols[2].get_text(strip=True)

            round_info = None
            if "(" in place and ")" in place:
                match = re.search(r"\((.*?)\)", place)
                if match:
                    round_info = match.group(1)
                    place = re.sub(r"\(.*?\)", "", place).strip()

            results.append({
                "meet_type": meet_type,
                "meet_id": meet_id,
                "meet_name": meet_name,
                "date": meet_date,
                "event": event_name,
                "mark": mark,
                "place": place,
                "round": round_info,
            })

        logger.debug(f"Parsed results for meet: {meet_name} ({meet_date})")

    logger.info(f"Total non-relay performances parsed: {len(results)}")
    return results


# ---------- Main Scraper ---------- #

def get_athlete_details(athlete_url: str):
    """Scrape a TFRRS athlete page and return structured data."""
    if not athlete_url.startswith("http"):
        athlete_url = f"https://www.tfrrs.org{athlete_url}"

    start_time = time.time()
    logger.info(f"Fetching athlete page: {athlete_url}")

    headers = default_headers()

    try:
        r = requests.get(athlete_url, headers=headers, timeout=30)
        html = safe_decode(r.content, r.headers.get("Content-Encoding"))
    except Exception as e:
        logger.error(f"Failed to fetch athlete page: {e}")
        return None

    fetch_time = time.time() - start_time
    soup = BeautifulSoup(html, "lxml")

    parse_start = time.time()
    (
        athlete_name,
        class_year,
        current_team_slug,
        current_team_name,
        gender,
        previous_team_slugs,
    ) = extract_name_and_teams(soup)

    results = extract_athlete_results(soup)
    parse_time = time.time() - parse_start

    total_time = time.time() - start_time
    logger.info(
        f"Scrape complete for {athlete_name} "
        f"({len(results)} results, fetch: {fetch_time:.2f}s, parse: {parse_time:.2f}s, total: {total_time:.2f}s)"
    )

    return {
        "athlete_name": athlete_name,
        "class_year": class_year,
        "current_team_slug": current_team_slug,
        "current_team_name": current_team_name,
        "gender": gender,
        "previous_team_slugs": previous_team_slugs,
        "results": results,
    }


# ---------- Manual Testing ---------- #

#if __name__ == "__main__":
#    data = get_athlete_details("https://www.tfrrs.org/athletes/7929458")
#    if data:
#        print(f"{data['athlete_name']} ({data['class_year']})")
#        print("Current team slug:", data["current_team_slug"])
#        print("Previous team slugs:", data["previous_team_slugs"])
#        print(f"Results found: {len(data['results'])}")
#        print(data["results"][:10])
