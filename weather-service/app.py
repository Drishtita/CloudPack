from fastapi import FastAPI
from weather import check_weather
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="CloudPack Weather Service",
    description="Weather microservice for Smart Packing Agent",
    version="1.0.0"
)
Instrumentator().instrument(app).expose(app)

@app.get("/")
def root():
    return {
        "service": "weather-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/weather/{city}")
def get_weather(city: str):
    return check_weather(city)