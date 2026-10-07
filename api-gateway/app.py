from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os


app = FastAPI(
    title="CloudPack API Gateway",
    description="Single entry point for CloudPack microservices",
    version="1.0.0"
)




AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
WEATHER_SERVICE_URL = os.getenv("WEATHER_SERVICE_URL", "http://localhost:8001")
MEMORY_SERVICE_URL = os.getenv("MEMORY_SERVICE_URL", "http://localhost:8002")

class AgentRequest(BaseModel):
    session_id: str
    goal: str


class TripRequest(BaseModel):
    destination: str
    days: int
    trip_type: str


@app.get("/")
def root():
    return {
        "service": "api-gateway",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/agent/run")
def run_agent(request: AgentRequest):

    try:

        response = requests.post(
            f"{AGENT_SERVICE_URL}/agent/run",
            json={
                "session_id": request.session_id,
                "goal": request.goal
            },
            timeout=500
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Agent service unavailable: {str(exc)}"
        )


@app.get("/api/weather/{city}")
def get_weather(city: str):

    try:

        response = requests.get(
            f"{WEATHER_SERVICE_URL}/weather/{city}",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Weather service unavailable: {str(exc)}"
        )


@app.post("/api/memory/{session_id}/trip")
def start_trip(
    session_id: str,
    request: TripRequest
):

    try:

        response = requests.post(
            f"{MEMORY_SERVICE_URL}/memory/{session_id}/trip",
            json={
                "destination": request.destination,
                "days": request.days,
                "trip_type": request.trip_type
            },
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Memory service unavailable: {str(exc)}"
        )