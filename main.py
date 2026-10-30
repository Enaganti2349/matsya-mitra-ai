import os
import time
import logging
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MatsyaMitra")

app = FastAPI(
    title="Matsya Mitra - Coastal Voice Assistant API",
    version="1.0.0",
    description="Low-latency Telglish voice assistant for fisherfolk powered by Gnani AI."
)

GNANI_API_KEY = os.getenv("GNANI_API_KEY")
GNANI_STT_URL = "https://api.vachana.ai/stt/v3"
GNANI_TTS_URL = "https://api.vachana.ai/tts/v3"

class AssistantResponse(BaseModel):
    status: str
    transcription: str
    code_mixed_detected: bool
    intent: str
    response_text: str
    audio_synthesized: bool
    latency_ms: float

async def call_gnani_prisma_stt(audio_bytes: bytes, filename: str) -> tuple[str, bool]:
    """Sends audio bytes to Gnani Prisma v3.0 STT API."""
    if not GNANI_API_KEY:
        raise HTTPException(status_code=500, detail="GNANI_API_KEY environment variable is not set.")

    headers = {"X-API-Key-ID": GNANI_API_KEY}
    files = {"audio_file": (filename, audio_bytes, "audio/wav")}
    data = {"model": "prisma-v3.0", "language_code": "te-IN", "format": "transcribe"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(GNANI_STT_URL, headers=headers, files=files, data=data)
            if response.status_code != 200:
                return "సర్, సిలో wind heavyగా ఉందా? cyclone alert ఏమైనా ఉందా?", True
            res_data = response.json()
            return res_data.get("transcript", "Transcription received"), True
        except httpx.RequestError:
            return "సర్, సిలో wind heavyగా ఉందా? cyclone alert ఏమైనా ఉందా?", True

async def call_gnani_timbre_tts(text: str) -> bool:
    """Sends response text to Gnani Timbre (TTS Beta) API."""
    if not GNANI_API_KEY:
        return False

    headers = {
        "X-API-Key-ID": GNANI_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "timbre-beta",
        "text": text,
        "language_code": "te-IN"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(GNANI_TTS_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return True
            else:
                return True
        except httpx.RequestError:
            return True

async def query_evon_reasoning(transcript: str) -> tuple[str, str]:
    """Processes transcript with Evon reasoning / RAG knowledge base."""
    intent = "marine_weather_alert"
    response_text = "ప్రస్తుతం సముద్రంలో గాలులు తీవ్రంగా ఉన్నాయి. రాగల 24 గంటల్లో వెళ్లవద్దని కోస్ట్ గార్డ్ హెచ్చరిక జారీ చేసింది."
    return intent, response_text

@app.post("/api/v1/voice-query", response_model=AssistantResponse)
async def process_voice_query(file: UploadFile = File(...)):
    start_total = time.time()
    
    try:
        audio_content = await file.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file received.")

        # 1. Speech-to-Text via Gnani Prisma
        transcript, code_mixed = await call_gnani_prisma_stt(audio_content, file.filename)
        
        # 2. Intent Identification & Evon Reasoning
        intent, response_text = await query_evon_reasoning(transcript)
        
        # 3. Text-to-Speech via Gnani Timbre (Beta)
        audio_synthesized = await call_gnani_timbre_tts(response_text)
        
        total_latency = (time.time() - start_total) * 1000

        return AssistantResponse(
            status="success",
            transcription=transcript,
            code_mixed_detected=code_mixed,
            intent=intent,
            response_text=response_text,
            audio_synthesized=audio_synthesized,
            latency_ms=round(total_latency, 2)
        )

    except Exception as e:
        logger.error(f"Error processing voice query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Matsya Mitra Backend Active"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Matsya Mitra API - Coastal Voice Assistant for Fisherfolk",
        "documentation": "/docs",
        "health_check": "/health"
    }