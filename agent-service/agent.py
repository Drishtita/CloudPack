import os
import json
import requests

from typing import Any
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = os.getenv("GROQ_ENDPOINT", "https://api.groq.com/openai/v1")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
USE_NATIVE_TOOL_CALLING = True

WEATHER_SERVICE_URL = os.getenv(
    "WEATHER_SERVICE_URL",
    "http://localhost:8001"
)

MEMORY_SERVICE_URL = os.getenv(
    "MEMORY_SERVICE_URL",
    "http://localhost:8002"
)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_ENDPOINT
)

# ============================================================
# Tool Schemas
# ============================================================

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "check_weather",
            "description": (
                "Fetch the 5-day weather forecast for a city from "
                "OpenWeatherMap. ALWAYS call this before recommending "
                "any weather-dependent items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "City name, e.g. 'Manali' or 'Goa'."
                        ),
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_item",
            "description": (
                "Add a single item to the packing list with a short "
                "reason. Call this once per item."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Item to pack.",
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "One-line reason referencing weather "
                            "or trip details."
                        ),
                    },
                },
                "required": ["item"],
            },
        },
    },
]


# ============================================================
# System Prompts
# ============================================================

def build_system_prompt_native(trip_info: str) -> str:

    return f"""
You are a smart travel packing assistant with access to two tools:

• check_weather(city)
  - get real weather data before suggesting weather-dependent items

• add_item(item, reason)
  - add one item to the packing list; call once per item


STRICT RULES:

1. You MUST call check_weather BEFORE adding any
   weather-dependent item.

2. Add items one at a time using add_item.
   Never batch them.

3. Each add_item call must include a specific reason
   referencing the weather or trip type.

4. After building the initial list, do one final
   reasoning pass over the trip type to check for
   missing items.

5. When you are satisfied the list is complete,
   respond with a plain-text summary.
   Do NOT call any more tools.


Current trip info:

{trip_info}
"""


def build_system_prompt_fallback(trip_info: str) -> str:

    return f"""
You are a smart travel packing assistant.

You must output EXACTLY one JSON object per turn.

Available actions:

{{"action": "check_weather", "city": "<city_name>"}}

{{"action": "add_item",
  "item": "<item>",
  "reason": "<reason>"}}

{{"action": "finish",
  "message": "<final summary text>"}}


STRICT RULES:

1. Call check_weather BEFORE any weather-dependent item.

2. Add items one at a time via add_item with a specific reason.

3. After the initial list, do one pass to check for items
   missing given the trip_type.

4. Use finish when done.

Output ONLY the JSON object.
No markdown fences.
No extra text.


Current trip info:

{trip_info}
"""


# ============================================================
# Memory helpers
# ============================================================

def get_memory(session_id: str) -> dict:

    response = requests.get(
        f"{MEMORY_SERVICE_URL}/memory/{session_id}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def store_weather(
    session_id: str,
    weather: dict
) -> dict:

    response = requests.post(
        f"{MEMORY_SERVICE_URL}/memory/{session_id}/weather",
        json={
            "weather": weather
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def add_memory_item(
    session_id: str,
    item: str,
    reason: str
) -> dict:

    response = requests.post(
        f"{MEMORY_SERVICE_URL}/memory/{session_id}/items",
        json={
            "item": item,
            "reason": reason,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# Weather service helper
# ============================================================

def call_weather_service(city: str) -> dict:

    response = requests.get(
        f"{WEATHER_SERVICE_URL}/weather/{city}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# Tool dispatcher
# ============================================================

def dispatch_tool(
    name: str,
    args: dict,
    session_id: str
) -> Any:

    if name == "check_weather":

        city = args.get("city", "")

        result = call_weather_service(city)

        # Save weather into memory-service
        store_weather(
            session_id=session_id,
            weather=result,
        )

        return result


    elif name == "add_item":

        item = args.get("item", "")
        reason = args.get("reason", "")

        return add_memory_item(
            session_id=session_id,
            item=item,
            reason=reason,
        )


    else:

        return {
            "error": f"Unknown tool: {name}"
        }


# ============================================================
# Result summary
# ============================================================

def result_summary(
    tool_name: str,
    result: Any
) -> str:

    if tool_name == "check_weather":

        if isinstance(result, dict) and "error" in result:
            return f"ERROR: {result['error']}"

        if (
            isinstance(result, dict)
            and result.get("list")
        ):

            first = result["list"][0]

            temp = (
                first
                .get("main", {})
                .get("temp", "?")
            )

            desc = (
                first
                .get("weather", [{}])[0]
                .get("description", "?")
            )

            count = result.get("cnt", 0)

            city = (
                result
                .get("city", {})
                .get("name", "?")
            )

            return (
                f"{city}: {count} forecast slots, "
                f"first entry = {temp}°C, {desc}"
            )

    return str(result)[:120]


# ============================================================
# LLM Calls
# ============================================================

def llm_call_native(
    messages: list[dict]
) -> Any:

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        return response

    except Exception as exc:

        raise RuntimeError(
            f"Groq API error (native): {exc}"
        ) from exc


def llm_call_fallback(
    messages: list[dict],
    retry: bool = False
) -> str:

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        return (
            response
            .choices[0]
            .message
            .content
            or ""
        )

    except Exception as exc:

        raise RuntimeError(
            f"Groq API error (fallback): {exc}"
        ) from exc


# ============================================================
# JSON fallback parser
# ============================================================

def parse_fallback_json(
    text: str
) -> dict | None:

    text = text.strip()

    if text.startswith("```"):

        lines = text.splitlines()

        if lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1])
        else:
            text = "\n".join(lines[1:])

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        return None


# ============================================================
# Review prompt
# ============================================================

def build_review_prompt(
    memory: dict
) -> str:

    items = memory.get("items", [])

    weather = memory.get(
        "weather",
        {}
    )

    trip_type = memory.get(
        "trip_type",
        ""
    )

    return (
        "You have built this packing list so far "
        "(read from memory):\n"
        f"{items}\n\n"
        "Weather snapshot from stored data:\n"
        f"{weather}\n\n"
        f"Given the trip type '{trip_type}', "
        "are there any important items still missing? "
        "If yes, call add_item for each one. "
        "If the list is already complete, say you are done."
    )


# ============================================================
# Native Tool Calling Path
# ============================================================

def _run_native(
    goal: str,
    session_id: str,
    trip_info: str,
    max_steps: int,
    trace: list,
) -> str:

    messages: list[dict] = [
        {
            "role": "system",
            "content": build_system_prompt_native(
                trip_info
            ),
        },
        {
            "role": "user",
            "content": goal,
        },
    ]

    review_done = False

    for step in range(max_steps):

        response = llm_call_native(messages)

        choice = response.choices[0]

        finish_reason = choice.finish_reason

        msg = choice.message

        # Add only supported fields from assistant response
        assistant_dict = {
            "role": "assistant",
            "content": msg.content or ""
        }

        if msg.tool_calls:
            assistant_dict["tool_calls"] = []

            for tc in msg.tool_calls:
                assistant_dict["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        messages.append(assistant_dict)

        # ----------------------------------------------------
        # No tool call → possible finish
        # ----------------------------------------------------

        if (
            finish_reason == "stop"
            or not msg.tool_calls
        ):

            memory = get_memory(session_id)

            if (
                not review_done
                and memory.get("items")
            ):

                review_done = True

                review_msg = build_review_prompt(
                    memory
                )

                messages.append({
                    "role": "user",
                    "content": review_msg,
                })

                continue

            return (
                msg.content
                or "(no final message)"
            )

        # ----------------------------------------------------
        # Tool calls
        # ----------------------------------------------------

        for tc in msg.tool_calls:

            tool_name = tc.function.name

            try:
                tool_args = json.loads(
                    tc.function.arguments
                )
            except json.JSONDecodeError:
                tool_args = {}

            trace.append(
                (
                    "TOOL_CALL",
                    tool_name,
                    tool_args,
                )
            )

            result = dispatch_tool(
                tool_name,
                tool_args,
                session_id,
            )

            summary = result_summary(
                tool_name,
                result,
            )

            trace.append(
                (
                    "TOOL_RESULT",
                    tool_name,
                    summary,
                )
            )

            # Limit huge weather responses
            if (
                tool_name == "check_weather"
                and isinstance(result, dict)
                and "list" in result
            ):

                trimmed = {
                    k: v
                    for k, v in result.items()
                    if k != "list"
                }

                trimmed["list"] = result["list"][:8]

                result_str = json.dumps(
                    trimmed
                )

            else:

                result_str = (
                    json.dumps(result)
                    if isinstance(result, dict)
                    else str(result)
                )

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tool_name,
                "content": result_str,
            })

    return (
        "(max steps reached – "
        "partial list may be incomplete)"
    )

# ============================================================
# JSON Fallback Path
# ============================================================

def _run_fallback(
    goal: str,
    session_id: str,
    trip_info: str,
    max_steps: int,
    trace: list,
) -> str:

    messages: list[dict] = [
        {
            "role": "system",
            "content": build_system_prompt_fallback(
                trip_info
            ),
        },
        {
            "role": "user",
            "content": goal,
        },
    ]

    review_done = False

    for step in range(max_steps):

        raw_text = llm_call_fallback(
            messages
        )

        parsed = parse_fallback_json(
            raw_text
        )


        # ----------------------------------------------------
        # Retry once if JSON is invalid
        # ----------------------------------------------------

        if parsed is None:

            messages.append({
                "role": "assistant",
                "content": raw_text,
            })

            messages.append({
                "role": "user",
                "content": (
                    "Your last response was not valid JSON. "
                    "Output ONLY a single JSON object – "
                    "no markdown, no extra text."
                ),
            })

            raw_text = llm_call_fallback(
                messages,
                retry=True,
            )

            parsed = parse_fallback_json(
                raw_text
            )


        if parsed is None:

            return (
                "(JSON parse failed twice; "
                f"last output: {raw_text[:200]})"
            )


        action = parsed.get(
            "action",
            ""
        )


        # ----------------------------------------------------
        # Finish
        # ----------------------------------------------------

        if action == "finish":

            memory = get_memory(
                session_id
            )

            if (
                not review_done
                and memory.get("items")
            ):

                review_done = True

                messages.append({
                    "role": "assistant",
                    "content": raw_text,
                })

                messages.append({
                    "role": "user",
                    "content": build_review_prompt(
                        memory
                    ),
                })

                continue

            return parsed.get(
                "message",
                "(no message)"
            )


        # ----------------------------------------------------
        # Tool call
        # ----------------------------------------------------

        if action in (
            "check_weather",
            "add_item",
        ):

            tool_args = {
                k: v
                for k, v in parsed.items()
                if k != "action"
            }

            trace.append(
                (
                    "TOOL_CALL",
                    action,
                    tool_args,
                )
            )

            result = dispatch_tool(
                action,
                tool_args,
                session_id,
            )

            summary = result_summary(
                action,
                result,
            )

            trace.append(
                (
                    "TOOL_RESULT",
                    action,
                    summary,
                )
            )


            if (
                action == "check_weather"
                and isinstance(result, dict)
                and "list" in result
            ):

                trimmed = {
                    k: v
                    for k, v in result.items()
                    if k != "list"
                }

                trimmed["list"] = result[
                    "list"
                ][:8]

                result_str = json.dumps(
                    trimmed
                )

            else:

                result_str = (
                    json.dumps(result)
                    if isinstance(result, dict)
                    else str(result)
                )


            messages.append({
                "role": "assistant",
                "content": raw_text,
            })

            messages.append({
                "role": "user",
                "content": (
                    f"Tool '{action}' returned: "
                    f"{result_str}\n\n"
                    "What next?"
                ),
            })


        else:

            messages.append({
                "role": "assistant",
                "content": raw_text,
            })

            messages.append({
                "role": "user",
                "content": (
                    f"Unknown action '{action}'. "
                    "Use check_weather, add_item, "
                    "or finish."
                ),
            })


    return (
        "(max steps reached – "
        "partial list may be incomplete)"
    )


# ============================================================
# Main Agent
# ============================================================

def run_agent(
    goal: str,
    session_id: str,
    max_steps: int = 20,
) -> tuple[str, list]:

    trace: list = []

    # Get current trip from memory-service
    memory = get_memory(
        session_id
    )

    trip_info = (
        f"Destination: "
        f"{memory.get('destination')}\n"
        f"Duration: "
        f"{memory.get('days')} days\n"
        f"Trip type: "
        f"{memory.get('trip_type')}"
    )


    if USE_NATIVE_TOOL_CALLING:

        final_message = _run_native(
            goal=goal,
            session_id=session_id,
            trip_info=trip_info,
            max_steps=max_steps,
            trace=trace,
        )

    else:

        final_message = _run_fallback(
            goal=goal,
            session_id=session_id,
            trip_info=trip_info,
            max_steps=max_steps,
            trace=trace,
        )


    trace.append(
        (
            "FINAL ANSWER",
            final_message,
        )
    )

    return final_message, trace
