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
