import os
import requests
from dotenv import load_dotenv

load_dotenv()


def check_weather(city: str) -> dict:
    """
    Fetch a 5-day / 3-hour weather forecast for a city
    from OpenWeatherMap.
    """

    api_key = os.getenv("OPENWEATHER_API_KEY", "")

    if not api_key:
        return {
            "error": "OPENWEATHER_API_KEY not set in environment.",
            "city": city
        }

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={api_key}&units=metric"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as exc:
        return {
            "error": f"HTTP {exc.response.status_code}: "
                      f"{exc.response.text[:200]}",
            "city": city
        }

    except requests.exceptions.ConnectionError:
        return {
            "error": "Network connection failed.",
            "city": city
        }

    except requests.exceptions.Timeout:
        return {
            "error": "OpenWeatherMap request timed out.",
            "city": city
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "city": city
        }