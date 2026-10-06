from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import run_agent


app = FastAPI(
    title="CloudPack Agent Service",
    description="AI orchestration service for Smart Packing Agent",
    version="1.0.0"
)


class AgentRequest(BaseModel):
    session_id: str
    goal: str


@app.get("/")
def root():
    return {
        "service": "agent-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/agent/run")
def run_agent_endpoint(request: AgentRequest):

    try:

        final_message, trace = run_agent(
            goal=request.goal,
            session_id=request.session_id,
        )

        return {
            "message": final_message,
            "trace": trace,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )