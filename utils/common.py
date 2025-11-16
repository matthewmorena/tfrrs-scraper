import re
import brotli
import gzip

def safe_decode(content, encoding):
    """Decode HTTP response content based on encoding."""
    try:
        if encoding == "br":
            return brotli.decompress(content).decode("utf-8", errors="replace")
        elif encoding == "gzip":
            return gzip.decompress(content).decode("utf-8", errors="replace")
        else:
            return content.decode("utf-8", errors="replace")
    except Exception:
        return content.decode("utf-8", errors="replace")


def extract_athlete_id(url: str) -> str | None:
    match = re.search(r"/athletes/(\d+)/", url or "")
    return match.group(1) if match else None


def extract_team_slug(url: str) -> str | None:
    match = re.search(r"/teams/(?:tf|xc)/([^/]+)\.html", url or "")
    return match.group(1) if match else None


def extract_meet_id(url: str) -> str | None:
    match = re.search(r"/results/(?:xc/)?(\d+)", url or "")
    return match.group(1) if match else None


def default_headers() -> dict:
    """Shared headers for all requests."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

def time_to_seconds(time_str, keep_flags=False):
    """
    Convert a race time string into total seconds (float).

    Handles formats like:
        SS.mm
        MM:SS.mm
        MM:SS.m
        HH:MM:SS.mm
        SS
    Also handles text flags like:
        NT, DNS, DNF, DQ

    Args:
        time_str (str): the race time
        keep_flags (bool): if True, returns the flag text instead of None for NT/DNS/DNF/DQ

    Returns:
        float or None or str: total seconds, None, or flag string
    """
    if not isinstance(time_str, str) or not time_str.strip():
        return None

    time_str = time_str.strip().upper()

    # Handle textual results
    invalid_flags = {"NT", "DNS", "DNF", "DQ"}
    if time_str in invalid_flags:
        return time_str if keep_flags else None

    # Split by colon
    parts = time_str.split(':')

    try:
        if len(parts) == 1:
            # Format: SS.mm or SS
            return float(parts[0])

        elif len(parts) == 2:
            # Format: MM:SS.mm
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds

        elif len(parts) == 3:
            # Format: HH:MM:SS.mm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds

        else:
            raise ValueError

    except ValueError:
        # If parsing fails, return None or keep flag
        return None
