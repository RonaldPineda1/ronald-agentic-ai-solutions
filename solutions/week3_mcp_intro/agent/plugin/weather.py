# agent/plugin/weather.py
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


# ---- Config (hardcoded per requirements) -------------------------------------
REGISTRY_URL = "http://localhost:8765/descriptor"
TOOL_URL = "http://localhost:8765/weather"

# English-only NL: lightweight keyword+regex matcher
WEATHER_PATTERN = re.compile(
    r"(?:\bweather\b).*?\b(?:in|at|for)\s+(?P<city>[A-Za-z][A-Za-z\-\s]+)\??",
    re.IGNORECASE,
)


# ---- Error types --------------------------------------------------------------
class WeatherClientError(ValueError):
    """4xx error raised by the weather tool with a parsed, user-safe message."""

    def __init__(self, status: int, message: str, raw_body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.raw_body = raw_body or ""


class WeatherServerError(RuntimeError):
    """5xx or unknown transport error when calling the weather tool."""

    def __init__(self, status: int, message: str, raw_body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.raw_body = raw_body or ""


def _parse_error_body(body: str) -> str:
    """
    Try to extract a useful error message from the tool's error body.
    Falls back to the raw body (trimmed) if JSON parse fails or 'error' field missing.
    """
    try:
        data = json.loads(body)
        # Prefer explicit 'error', otherwise join any string-like values for context
        if isinstance(data, dict):
            if (
                "error" in data
                and isinstance(data["error"], str)
                and data["error"].strip()
            ):
                return data["error"].strip()
            # Collect short string fields as a compact fallback
            fields = [
                str(v).strip()
                for v in data.values()
                if isinstance(v, str) and v.strip()
            ]
            if fields:
                return "; ".join(fields)
        # If body is a bare string/array, just stringify it.
        return body.strip()[:400] or "Unknown client error"
    except Exception:
        return body.strip()[:400] or "Unknown client error"


# ---- Tool registry ------------------------------------------------------------
def get_tool_descriptor() -> Dict[str, Any]:
    """Fetch the weather tool descriptor from the local registry endpoint."""
    with urllib.request.urlopen(REGISTRY_URL, timeout=3) as resp:  # nosec B310
        if resp.status != 200:
            raise RuntimeError(f"descriptor HTTP {resp.status}")
        data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict) or data.get("name") != "get_weather":
            raise ValueError("unexpected tool descriptor payload")
        return data


# ---- Intent + params ----------------------------------------------------------
def parse_intent(query: str) -> Optional[str]:
    """Return 'get_weather' when English NL suggests a weather query."""
    if "weather" in query.lower() and WEATHER_PATTERN.search(query):
        return "get_weather"
    return None


def extract_params(query: str) -> Dict[str, Any]:
    """Extract parameters for the weather tool (currently just city)."""
    m = WEATHER_PATTERN.search(query)
    city = m.group("city").strip() if m else None
    return {"city": city}  # keep dict for future multi-param tools


# ---- Tool call (HTTP) ---------------------------------------------------------
def call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the weather tool over HTTP: /weather?city={city} and handle errors cleanly."""
    city = (params.get("city") or "").strip()
    if not city:
        raise WeatherClientError(400, "City not detected. Try: weather in <city>.")

    q = urllib.parse.urlencode({"city": city})
    url = f"{TOOL_URL}?{q}"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
            payload = json.loads(resp.read().decode("utf-8"))
            if resp.status != 200:
                # Defensive: urlopen usually raises HTTPError for non-200, but keep this anyway.
                msg = _parse_error_body(json.dumps(payload))
                raise WeatherClientError(resp.status, msg, raw_body=json.dumps(payload))
            return payload

    except urllib.error.HTTPError as e:
        # Read server body and try to parse a helpful message
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        if 400 <= e.code < 500:
            msg = _parse_error_body(body) or f"HTTP {e.code}"
            raise WeatherClientError(e.code, msg, raw_body=body)
        else:
            msg = (body.strip() or e.reason or "Unknown server error")[:400]
            raise WeatherServerError(e.code, f"HTTP {e.code}: {msg}", raw_body=body)

    except urllib.error.URLError as e:
        raise WeatherServerError(503, f"Weather tool unreachable: {e.reason}") from e

    except json.JSONDecodeError as e:
        raise WeatherServerError(502, f"Invalid JSON from weather tool: {e}") from e

    except Exception as e:
        # Last-resort unknown failure
        raise WeatherServerError(500, f"Unexpected weather tool error: {e}") from e


# ---- Answer builder -----------------------------------------------------------
def build_answer(tool_json: Dict[str, Any]) -> str:
    """Compose a short grounded answer from the tool result JSON."""
    city = tool_json.get("city")
    temp = tool_json.get("temp_c")
    cond = tool_json.get("conditions")
    src = tool_json.get("source", "weather-tool")
    return f"According to Weather tool the temperature and weather for {city} is {temp}\u00b0C, {cond}. (Source: {src})."
