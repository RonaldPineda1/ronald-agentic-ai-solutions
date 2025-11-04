# mcp_agent_runner.py
from __future__ import annotations
import argparse
import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Weather plugin
from agent.plugin import weather as weather_plugin

# Time plugin
from agent.plugin import time as time_plugin


# ---- Agent (runner) descriptor ------------------------------------------------
AGENT_DESCRIPTOR: Dict[str, Any] = {
    "name": "mcp_agent_runner",
    "description": "Minimal MCP-style agent runner that routes English NL to tools.",
    "inputs": [{"name": "query", "type": "string", "required": True}],
    "capabilities": [
        {
            "intent": "get_weather",
            "tool_name": "get_weather",
            "params": [{"name": "city", "type": "string", "required": True}],
        },
        {
            "intent": "get_time",
            "tool_name": "get_time",
            "params": [{"name": "timezone", "type": "string", "required": True}],
        },
    ],
    "notes": [
        "Weather tool registry at http://localhost:8765/descriptor and /weather?city=<city>",
        "Time tool uses https://worldtimeapi.org/api/timezone/<IANA>",
        "Parallel multi-tool execution supported.",
        "Client errors (HTTP 400s) from weather tool are parsed and shown cleanly.",
    ],
}


# ---- Logging model ------------------------------------------------------------
@dataclass
class InvocationLog:
    query: str
    intents: List[str]
    tool_used: bool
    params: Dict[str, Any]
    success: bool
    latency_ms: float
    error: Optional[str]
    answer: str


# ---- Internal helpers ---------------------------------------------------------
def _detect_intents(query: str) -> List[Tuple[str, Dict[str, Any], Any]]:
    results: List[Tuple[str, Dict[str, Any], Any]] = []

    if weather_plugin.parse_intent(query) == "get_weather":
        results.append(
            ("get_weather", weather_plugin.extract_params(query), weather_plugin)
        )

    if time_plugin.parse_intent(query) == "get_time":
        results.append(("get_time", time_plugin.extract_params(query), time_plugin))

    return results


def _run_one(plugin, params) -> str:
    """Call tool then build answer (blocking; safe to run in a thread)."""
    result = plugin.call_tool(params)
    return plugin.build_answer(result)


def _stringify_error(intent: str, err: Exception) -> str:
    """
    Normalize exceptions coming from plugins into concise, user-friendly lines.
    Handles weather plugin's structured client/server errors if present.
    """
    # Handle structured weather errors explicitly
    if intent == "get_weather":
        # Match by type name to avoid tight coupling if imports change
        if err.__class__.__name__ in ("WeatherClientError", "WeatherServerError"):
            status = getattr(err, "status", None)
            msg = str(err).strip()
            prefix = f"{intent}"
            if status:
                prefix += f" (HTTP {status})"
            return f"{prefix}: {msg}"
    # Fallback for any other error types
    return f"{intent}: {str(err).strip() or err.__class__.__name__}"


# ---- Core runner --------------------------------------------------------------
def run_agent(query: str) -> InvocationLog:
    tools = _detect_intents(query)
    intents = [i for i, _, _ in tools]
    tool_used = len(tools) > 0

    if not tools:
        ans = (
            "I can provide weather (e.g., 'weather in Madrid') and local time "
            "(e.g., 'time in Europe/Madrid' or 'time in Madrid')."
        )
        return InvocationLog(
            query=query,
            intents=[],
            tool_used=False,
            params={},
            success=True,
            latency_ms=0.0,
            error=None,
            answer=ans,
        )

    start = time.time()
    try:
        answers: List[str] = []
        errors: List[str] = []
        params_merged: Dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=len(tools)) as pool:
            future_map = {}
            for intent, params, plugin in tools:
                params_merged[intent] = params
                future = pool.submit(_run_one, plugin, params)
                future_map[future] = (intent, params, plugin)

            for future in as_completed(future_map):
                intent, _, _ = future_map[future]
                try:
                    ans = future.result()
                    answers.append(ans)
                except Exception as e:
                    errors.append(_stringify_error(intent, e))

        latency = round((time.time() - start) * 1000.0)

        if answers and not errors:
            final_answer = " \n- ".join(["Results:"] + answers)
            return InvocationLog(
                query=query,
                intents=intents,
                tool_used=tool_used,
                params=params_merged,
                success=True,
                latency_ms=latency,
                error=None,
                answer=final_answer,
            )

        if answers and errors:
            final_answer = " \n- ".join(["Partial results:"] + answers)
            final_answer += "\n\nErrors:\n• " + "\n• ".join(errors)
            return InvocationLog(
                query=query,
                intents=intents,
                tool_used=tool_used,
                params=params_merged,
                success=False,  # partial failure
                latency_ms=latency,
                error="; ".join(errors),
                answer=final_answer,
            )

        # Only errors (no answers)
        final_answer = "One or more tools failed:\n• " + "\n• ".join(errors)
        return InvocationLog(
            query=query,
            intents=intents,
            tool_used=tool_used,
            params=params_merged,
            success=False,
            latency_ms=latency,
            error="; ".join(errors),
            answer=final_answer,
        )

    except Exception as e:
        latency = (time.time() - start) * 1000.0
        return InvocationLog(
            query=query,
            intents=intents,
            tool_used=tool_used,
            params={i: p for i, p, _ in tools},
            success=False,
            latency_ms=latency,
            error=str(e),
            answer=f"Runner error: {e}",
        )


# ---- CLI ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="MCP-style agent runner")
    parser.add_argument("--query", type=str, required=True, help="English NL prompt")
    parser.add_argument(
        "--log-json", type=str, help="Optional path to append JSON log line"
    )
    parser.add_argument(
        "--descriptor", action="store_true", help="Print agent descriptor JSON and exit"
    )
    args = parser.parse_args()

    if args.descriptor:
        print(json.dumps(AGENT_DESCRIPTOR, indent=2))
        return

    log = run_agent(args.query)
    print("Answer:\n" + log.answer)
    print("\nInvocation Log:")
    print(json.dumps(asdict(log), indent=2))

    if args.log_json:
        with open(args.log_json, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(log)) + "\n")
            print(f"Appended log to {args.log_json}")


if __name__ == "__main__":  # pragma: no cover
    main()
