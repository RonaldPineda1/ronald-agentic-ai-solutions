# agent/plugin/time.py
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Dict, Optional

# Free, no-key public API
# Docs: http://worldtimeapi.org/
WORLD_TIME_API = "https://worldtimeapi.org/api/timezone"

# Match: “time in Europe/Madrid” or “what time in Madrid?”
TIME_PATTERN = re.compile(
    r"(?:\btime\b|\bcurrent\s+time\b|\bwhat\s+time\b).*?\b(?:in|at|for)\s+(?P<place>[A-Za-z/_][A-Za-z\-_/\s]+)\??",
    re.IGNORECASE,
)

# A tiny helper map for common cities → IANA time zones (extend as needed)
CITY_TO_TZ = {
    "paris": "Europe/Paris",
    "madrid": "Europe/Madrid",
    "london": "Europe/London",
    "new york": "America/New_York",
    "tokyo": "Asia/Tokyo",
    "berlin": "Europe/Berlin",
    "rome": "Europe/Rome",
    "sydney": "Australia/Sydney",
    "toronto": "America/Toronto",
    "singapore": "Asia/Singapore",
}


# ---- Intent + params ----------------------------------------------------------
def parse_intent(query: str) -> Optional[str]:
    """Return 'get_time' when English NL suggests a time query."""
    if TIME_PATTERN.search(query):
        return "get_time"
    return None


def extract_params(query: str) -> Dict[str, Any]:
    """
    Extract a timezone from the NL. Accepts either:
      - explicit IANA tz like 'Europe/Madrid'
      - a city name we map via CITY_TO_TZ
    """
    m = TIME_PATTERN.search(query)
    place_raw = (m.group("place").strip() if m else "") if m else ""
    place = re.sub(r"\s+", " ", place_raw)

    if "/" in place:  # Assume explicit IANA timezone
        tz = place
    else:
        tz = CITY_TO_TZ.get(place.lower())

    return {"timezone": tz, "raw": place}


# ---- Tool call (HTTP) ---------------------------------------------------------
def call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke worldtimeapi.org for the given timezone.
    Raises a friendly error if timezone is missing/unknown.
    """
    tz = (params.get("timezone") or "").strip()
    if not tz:
        raw = params.get("raw") or "the requested place"
        raise ValueError(
            f"Could not determine a timezone for '{raw}'. "
            "Try e.g. 'time in Europe/Madrid' or a mapped city like 'time in Madrid'."
        )

    url = f"{WORLD_TIME_API}/{tz}"
    with urllib.request.urlopen(url, timeout=6) as resp:  # nosec B310
        if resp.status != 200:
            raise RuntimeError(f"time API HTTP {resp.status}")
        payload = json.loads(resp.read().decode("utf-8"))
        # Minimal shape check
        if "datetime" not in payload:
            raise ValueError("Unexpected time API payload")
        return payload


# ---- Answer builder -----------------------------------------------------------
def build_answer(tool_json: Dict[str, Any]) -> str:
    tz = tool_json.get("timezone") or tool_json.get("timezone_name") or "Unknown TZ"
    dt = tool_json.get("datetime")  # e.g. 2025-11-01T19:06:54.371061-06:00
    abbr = tool_json.get("abbreviation", "")
    offset = tool_json.get("utc_offset", "")
    nice = dt.replace("T", " ") if isinstance(dt, str) else dt
    suffix = f" {abbr}" if abbr else ""
    return f"According to {WORLD_TIME_API} tool the Local time in {tz}: {nice}{suffix} (UTC{offset})."
