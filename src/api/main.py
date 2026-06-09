"""F1 Predictor 2026 — FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize resources
    print("F1 Predictor API starting...")
    yield
    # Shutdown: Clean up resources
    print("F1 Predictor API shutting down...")


app = FastAPI(
    title="F1 Predictor 2026 API",
    description="Monte Carlo Race Prediction System API",
    version="3.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "F1 Predictor 2026 API", "version": "3.1.0"}
