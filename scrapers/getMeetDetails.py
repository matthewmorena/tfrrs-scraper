import requests
from bs4 import BeautifulSoup
import re
import time
from utils.common import safe_decode, extract_athlete_id, extract_team_slug, default_headers
from utils.logging_config import get_logger

logger = get_logger(__name__, "meet_scrape.log")

def parse_event_id(event_id_str: str):
    """Parse TFRRS event_id class strings like 'round_4_3200350_89' or 'heat_3_1_3200350_71'."""
    if not event_id_str:
        return None, None, None, False

    m_heat = re.match(r"heat_(\d+)_(\d+)_([0-9]+)_[0-9]+", event_id_str)
    m_round = re.match(r"round_(\d+)_([0-9]+)_[0-9]+", event_id_str)

    round_label, heat_number, event_uid, valid_round = None, None, None, True

    if m_heat:
        round_num, heat_number, event_uid = int(m_heat.group(1)), int(m_heat.group(2)), m_heat.group(3)
        round_label = {4: "finals", 3: "semifinals", 2: "quarterfinals", 1: "preliminaries"}.get(round_num)
    elif m_round:
        round_num, event_uid = int(m_round.group(1)), m_round.group(2)
        valid_round = round_num >= 4
        if valid_round:
            round_label, heat_number = "finals", 1

    return round_label, heat_number, event_uid, valid_round


# ---------- Track & Field Parsing ---------- #

def parse_tf_event_results(event_div, hidden_classes_set):
    title_elem = event_div.select_one(".custom-table-title h3, .custom-table-title h5")
    event_name = str(title_elem.get_text(strip=True)).split('\n', 1)[0] if title_elem else None

    # Skip relays, para, and field events
    exclude_keywords = [
        "relay", "x", "dmr", "smr", "para", "jump", "vault", "shot", "discus",
        "hammer", "javelin", "weight", "athlon"
    ]
    if event_name and any(k in event_name.lower() for k in exclude_keywords):
        logger.debug(f"Skipping excluded event: {event_name}")
        return None

    wind_elem = event_div.select_one(".custom-table-title .wind-text")
    wind = wind_elem.get_text(strip=True) if wind_elem else None

    table = event_div.select_one("table.table-hover, table.table-striped")
    if not table:
        logger.warning(f"No results table found for event: {event_name}")
        return None

    results = []
    for row in table.select("tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        place = cells[0].get_text(strip=True)

        athlete_link = cells[1].select_one("a")
        athlete_name = athlete_link.get_text(strip=True) if athlete_link else None
        athlete_id = extract_athlete_id(athlete_link["href"]) if athlete_link else None

        year = cells[2].get_text(strip=True) if len(cells) > 2 else None

        team_link = cells[3].select_one("a")
        team_name = team_link.get_text(strip=True) if team_link else None
        team_slug = extract_team_slug(team_link["href"]) if team_link else None

        # Find first visible time column
        time, event_id = "", None
        for td in cells[4:]:
            td_classes = td.get("class", [])
            if td_classes and not hidden_classes_set.intersection(td_classes):
                val = td.get_text(strip=True)
                if val:
                    time = val
                    event_id = td_classes[0]
                    break

        round_label, heat_number, event_uid, valid_round = parse_event_id(event_id)
        if not valid_round:
            logger.debug(f"Skipping combined heat round event: {event_name} ({event_id})")
            return None

        results.append({
            "place": place,
            "athlete_name": athlete_name,
            "athlete_id": athlete_id,
            "year": year,
            "team_name": team_name,
            "team_slug": team_slug,
            "time": time,
            "event_id": event_id,
        })

    logger.info(f"Parsed TF event: {event_name} ({len(results)} results)")
    return {
        "event_id": event_uid,
        "event_name": event_name,
        "round": round_label,
        "heat": heat_number,
        "wind": wind,
        "results": results,
    }


def get_tf_results(soup, gender):
    meet_name_el = soup.select_one("h3.panel-title")
    meet_name = meet_name_el.get_text(strip=True) if meet_name_el else None

    css_text = "\n".join(style.get_text() for style in soup.select("div.panel-body style"))
    hidden_classes = set(re.findall(r"\.([a-zA-Z0-9_-]+)\s*\{[^}]*display\s*:\s*none", css_text))

    meta_divs = soup.select("div.panel-heading-normal-text.inline-block")
    meet_date = meta_divs[0].get_text(" ", strip=True) if len(meta_divs) >= 1 else None
    meet_location = meta_divs[1].get_text(" ", strip=True) if len(meta_divs) >= 2 else None

    events = []
    for event_div in soup.select("div[class*='col-lg-']:has(.custom-table-title)"):
        parsed = parse_tf_event_results(event_div, hidden_classes)
        if parsed:
            parsed["gender"] = gender
            events.append(parsed)

    logger.info(f"Total TF events parsed: {len(events)}")
    return {
        "meet_type": "tf",
        "meet_name": meet_name,
        "meet_date": meet_date,
        "meet_location": meet_location,
        "events": events,
    }


# ---------- Cross Country Parsing ---------- #

def parse_xc_event(anchor):
    event_id = anchor.get("name", "").removeprefix("event").strip()
    if not event_id:
        return None

    title_elem = anchor.find_next("div", class_="custom-table-title-xc")
    if not title_elem:
        return None
    event_name_el = title_elem.select_one("h3")
    event_name = event_name_el.get_text(strip=True) if event_name_el else None

    # Truncate after 'CC'
    if event_name and "CC" in event_name:
        event_name = event_name.split("CC")[0].strip() + " CC"

    team_div = anchor.find_next("div", class_="row")
    indiv_div = team_div.find_next("div", class_="row") if team_div else None
    if not indiv_div:
        logger.warning(f"No individual results div found for XC event {event_id}")
        return None

    table = indiv_div.select_one("table")
    if not table:
        logger.warning(f"No results table found for XC event {event_id}")
        return None

    results = []
    for tr in table.select("tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue

        athlete_link = cells[1].select_one("a")
        athlete_name = athlete_link.get_text(strip=True) if athlete_link else None
        athlete_id = extract_athlete_id(athlete_link["href"]) if athlete_link else None

        team_link = cells[3].select_one("a")
        team_name = team_link.get_text(strip=True) if team_link else None
        team_slug = extract_team_slug(team_link["href"]) if team_link else None

        results.append({
            "place": cells[0].get_text(strip=True),
            "athlete_name": athlete_name,
            "athlete_id": athlete_id,
            "team_name": team_name,
            "team_slug": team_slug,
            "time": cells[5].get_text(strip=True),
        })

    logger.info(f"Parsed XC event: {event_name} ({len(results)} results)")
    return {"event_id": event_id, "event_name": event_name, "results": results}


def get_xc_results(soup):
    meet_name_el = soup.select_one("h3.panel-title")
    meet_name = meet_name_el.get_text(strip=True) if meet_name_el else None

    meta_divs = soup.select("div.panel-heading-normal-text.inline-block")
    meet_date = meta_divs[0].get_text(" ", strip=True) if len(meta_divs) >= 1 else None
    meet_location = (
        re.sub(r"\s+", " ", meta_divs[1].get_text(" ", strip=True)) if len(meta_divs) >= 2 else None
    )

    events = []
    for anchor in soup.select("a.anchor[name^='event']"):
        parsed = parse_xc_event(anchor)
        if parsed:
            events.append(parsed)

    logger.info(f"Total XC events parsed: {len(events)}")
    return {
        "meet_type": "xc",
        "meet_name": meet_name,
        "meet_date": meet_date,
        "meet_location": meet_location,
        "events": events,
    }


# ---------- Main entrypoint ---------- #

def get_meet_results(meet_url: str):
    """Scrape all event results from a TFRRS meet page."""
    if not meet_url.startswith("http"):
        meet_url = f"https://www.tfrrs.org{meet_url}"

    headers = default_headers()

    logger.info(f"Fetching meet page: {meet_url}")
    r = requests.get(meet_url, headers=headers, timeout=30)
    html = safe_decode(r.content, r.headers.get("Content-Encoding"))
    soup = BeautifulSoup(html, "lxml")

    if "/xc/" in meet_url:
        logger.info("Detected XC meet page.")
        return get_xc_results(soup)
    elif "/m/" in meet_url:
        logger.info("Detected Men's Track & Field meet page.")
        return get_tf_results(soup, "m")
    elif "/f/" in meet_url:
        logger.info("Detected Women's Track & Field meet page.")
        return get_tf_results(soup, "f")
    else:
        logger.error("Detected Invalid Meet URL.")
        return None

# ---------- Manual Testing ---------- #

#if __name__ == "__main__":
#    data = get_meet_results("https://www.tfrrs.org/results/92668/m")
#    logger.info(f"Meet: {data['meet_name']} | {data['meet_date']} | {data['meet_location']} | {data['meet_type']}")
#    logger.info(f"Total events found: {len(data['events'])}")
