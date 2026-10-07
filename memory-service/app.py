from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from memory import memory_store



app = FastAPI(
    title="CloudPack Memory Service",
    description="Session and trip memory for Smart Packing Agent",
    version="1.0.0"
)
Instrumentator().instrument(app).expose(app)

# -----------------------------
# Request models
# -----------------------------

class TripRequest(BaseModel):
    destination: str
    days: int
    trip_type: str


class WeatherRequest(BaseModel):
    weather: dict


class ItemRequest(BaseModel):
    item: str
    reason: str = ""


# -----------------------------
# Basic endpoints
# -----------------------------

@app.get("/")
def root():
    return {
        "service": "memory-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# -----------------------------
# Trip endpoints
# -----------------------------

@app.post("/memory/{session_id}/trip")
def start_trip(session_id: str, request: TripRequest):

    return memory_store.start_trip(
        session_id=session_id,
        destination=request.destination,
        days=request.days,
        trip_type=request.trip_type
    )


@app.get("/memory/{session_id}")
def get_memory(session_id: str):

    trip = memory_store.get_trip(session_id)

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="No active trip found for this session"
        )

    return trip


# -----------------------------
# Weather memory
# -----------------------------

@app.post("/memory/{session_id}/weather")
def store_weather(
    session_id: str,
    request: WeatherRequest
):

    try:
        return memory_store.store_weather(
            session_id=session_id,
            weather=request.weather
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


# -----------------------------
# Packing items
# -----------------------------

@app.post("/memory/{session_id}/items")
def add_item(
    session_id: str,
    request: ItemRequest
):

    try:
        return memory_store.add_item(
            session_id=session_id,
            item=request.item,
            reason=request.reason
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


# -----------------------------
# End trip
# -----------------------------

@app.delete("/memory/{session_id}")
def end_trip(session_id: str):

    try:
        return memory_store.end_trip(session_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )