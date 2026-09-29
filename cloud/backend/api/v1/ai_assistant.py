"""
AI Assistant API — powered by local Ollama (LLaMA 3 8B)

Provides:
  POST /api/v1/ai/chat   — send a question with optional sensor context
  GET  /api/v1/ai/status  — check Ollama availability
"""

import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from core.sensor_storage import get_latest, get_history
from core.twin_accuracy import get_physics_model_summary, get_accuracy_stats

router = APIRouter(tags=["AI Assistant"])

OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3:8b"

SYSTEM_PROMPT = (
    "You are an agricultural AI assistant helping manage a microgreens smart farm.\n"
    "You have access to real-time sensor data AND a digital twin physics engine.\n\n"
    "The digital twin uses 6 physics models:\n"
    "  1. Soil Moisture Balance: M_{t+1} = M_t + I - E - U\n"
    "  2. Evaporation Model: E ∝ T × (1 − H)\n"
    "  3. Plant Water Uptake: U = k × Light_intensity\n"
    "  4. Light Influence: growth_rate = a × light_level\n"
    "  5. Temperature Effect: evaporation_rate = base × temp_factor\n"
    "  6. Time Evolution: step-by-step moisture prediction\n\n"
    "Where M=moisture, I=irrigation, E=evaporation, U=plant uptake, T=temperature, H=humidity.\n\n"
    "Optimal ranges for microgreens:\n"
    "  • Temperature: 20–28 °C\n"
    "  • Humidity: 50–70 %\n"
    "  • Soil moisture: 60–80 %\n"
    "  • Light level: 40–80 % (full-spectrum LED or sunlight)\n\n"
    "Rules:\n"
    "  1. Always reference the actual sensor values AND digital twin predictions when provided.\n"
    "  2. Explain your reasoning using the physics models (mention which model applies).\n"
    "  3. Clearly state whether each parameter is within, below, or above the optimal range.\n"
    "  4. When predicting future conditions, cite the Time Evolution model.\n"
    "  5. Provide short, actionable recommendations.\n"
    "  6. Keep responses concise (3–6 sentences) unless the user asks for detail.\n"
    "  7. If asked about twin accuracy, reference the accuracy metrics.\n"
    "  8. If the user asks a question unrelated to farming, politely redirect.\n"
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    include_sensor_data: bool = Field(
        True, description="Automatically append latest sensor readings to prompt"
    )
    farm_id: str = Field("farm_001")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    reply: str
    sensor_snapshot: Optional[dict] = None
    model: str = MODEL


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _build_sensor_context(farm_id: str) -> tuple[str, dict]:
    """Fetch latest readings + DT Brain physics data and format as context text."""
    snap = {}
    lines = []
    try:
        latest = get_latest(farm_id)
        if latest and "error" not in latest:
            snap = {
                "temperature": latest.get("temperature"),
                "humidity": latest.get("humidity"),
                "light_level": latest.get("light_level"),
                "soil_moisture": latest.get("soil_moisture"),
                "timestamp": latest.get("timestamp"),
            }
            lines += [
                "\n--- Current sensor readings ---",
                f"Temperature : {snap['temperature']} °C",
                f"Humidity    : {snap['humidity']} %",
                f"Light level : {snap['light_level']} %",
                f"Soil moisture: {snap['soil_moisture']} %",
                f"Timestamp   : {snap['timestamp']}",
            ]
    except Exception as e:
        logger.warning(f"Could not fetch sensor context: {e}")

    # DT Brain physics model data
    try:
        brain = get_physics_model_summary(farm_id, hours=24)
        accuracy_stats = get_accuracy_stats(farm_id, hours=24)
        snap["twin_brain"] = brain

        lines += [
            "\n--- Digital Twin Brain ---",
            f"Twin Accuracy     : {brain.get('twin_accuracy_pct', 'N/A')}%",
            f"Model Reliability : {brain.get('model_reliability_pct', 'N/A')}%",
            f"Avg Pred Error    : {brain.get('avg_prediction_error', 'N/A')}%",
            f"Predictions Tracked: {brain.get('sample_count', 0)}",
        ]

        # Latest twin prediction
        lp = brain.get("latest_prediction", {})
        if lp:
            lines += [
                f"Twin predicted soil moisture: {lp.get('predicted_soil_moisture', 'N/A')}%",
                f"Actual soil moisture        : {lp.get('actual_soil_moisture', 'N/A')}%",
                f"Prediction error            : {lp.get('error', 'N/A')}%",
            ]

        # Physics models summary
        models = brain.get("physics_models", {})
        m1 = models.get("1_soil_moisture_balance", {})
        m2 = models.get("2_evaporation_model", {})
        m6 = models.get("6_time_evolution", {})
        lines += [
            "\n--- Physics Model States ---",
            f"Soil Moisture Balance: {m1.get('status', 'N/A')} (deficit={m1.get('water_deficit_mm', 0):.1f}mm)",
            f"Evaporation: {m2.get('rate_label', 'N/A')} (factor={m2.get('evaporation_factor', 0)})",
            f"Time Evolution: {m6.get('prediction', 'N/A')} (loss={m6.get('moisture_loss_per_hour_pct', 0)}%/hr)",
        ]
    except Exception as e:
        logger.debug(f"DT Brain context not available: {e}")

    return "\n".join(lines) if lines else "", snap


async def _ollama_generate(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Call Ollama /api/generate and return the full response text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 512,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"].strip()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@router.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """
    Send a message to the farm AI assistant.

    If `include_sensor_data` is true (default), the latest sensor readings
    are automatically appended so the model can reference them.
    """
    sensor_text = ""
    snap = {}
    if req.include_sensor_data:
        sensor_text, snap = _build_sensor_context(req.farm_id)

    user_prompt = req.message + sensor_text

    try:
        reply = await _ollama_generate(user_prompt)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not reachable at localhost:11434. Make sure it is running.",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e.response.text}")

    return ChatResponse(reply=reply, sensor_snapshot=snap or None, model=MODEL)


@router.get("/ai/status")
async def ai_status():
    """Check whether the Ollama backend is reachable and the model is loaded."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            available = MODEL in models
            return {
                "ollama_reachable": True,
                "model": MODEL,
                "model_available": available,
                "all_models": models,
            }
    except Exception as e:
        return {
            "ollama_reachable": False,
            "model": MODEL,
            "model_available": False,
            "error": str(e),
        }
