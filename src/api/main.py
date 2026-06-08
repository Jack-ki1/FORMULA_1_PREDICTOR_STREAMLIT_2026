"""F1 Predictor 2026 — FastAPI Application."""
from fastapi import FastAPI

app = FastAPI(
    title="F1 Predictor 2026 API",
    description="Monte Carlo Race Prediction System API",
    version="3.1.0"
)

@app.get("/")
async def root():
    return {"message": "F1 Predictor 2026 API", "version": "3.1.0"}
