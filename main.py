"""
Hardstyle MIDI Generator - FastAPI Backend
Production-ready REST API for MIDI generation.
"""

import io
import os
import uuid
import zipfile
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from services.midi_parser import parse_midi
from services.generation_engine import HardstyleGenerationEngine, GenerationConfig
from services.trend_engine import get_trend_engine


# ─────────────────────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hardstyle MIDI Generator",
    description="AI-powered Hardstyle/Rawstyle MIDI generation from bassline input",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class GenerationResponse(BaseModel):
    session_id: str
    metadata: dict
    download_url: str


class HealthResponse(BaseModel):
    status: str
    version: str
    trend_engine_loaded: bool


class AnalysisResponse(BaseModel):
    bpm: float
    key: str
    scale: str
    total_bars: int
    note_count: int
    detected_style: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    try:
        trend = get_trend_engine()
        loaded = len(trend.melody_patterns.get("patterns", [])) > 0
    except Exception:
        loaded = False
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        trend_engine_loaded=loaded
    )


@app.post("/analyze")
async def analyze_midi(file: UploadFile = File(...)):
    """
    Analyze an uploaded MIDI file and return musical properties.
    Use this for a preview before full generation.
    """
    if not file.filename.endswith(('.mid', '.midi')):
        raise HTTPException(400, "File must be a MIDI file (.mid or .midi)")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(400, "MIDI file too large (max 5MB)")
    
    try:
        parsed = parse_midi(content)
    except ValueError as e:
        raise HTTPException(422, f"MIDI parsing error: {str(e)}")
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(500, "Failed to analyze MIDI file")
    
    trend = get_trend_engine()
    detected_style = trend.detect_style_from_bpm(parsed.bpm)
    
    return {
        "bpm": parsed.bpm,
        "key": parsed.key_name,
        "scale": parsed.scale_type,
        "total_bars": parsed.total_bars,
        "note_count": len(parsed.notes),
        "beats_per_bar": parsed.beats_per_bar,
        "detected_style": detected_style,
        "key_root": parsed.key_root,
    }


@app.post("/generate")
async def generate_midi(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    style: str = Form(default="rawstyle"),
    energy: str = Form(default="aggressive"),
    bars: int = Form(default=8),
):
    """
    Generate Hardstyle MIDI elements from a bassline MIDI file.
    
    Returns a ZIP file containing:
    - lead.mid
    - chords.mid  
    - pads.mid
    - metadata.json
    
    Parameters:
    - file: MIDI file (bassline)
    - style: "rawstyle" or "euphoric"
    - energy: "dark", "aggressive", "medium", "high"
    - bars: number of bars to generate (4, 8, 16)
    """
    # Validate inputs
    if style not in ["rawstyle", "euphoric"]:
        raise HTTPException(400, "style must be 'rawstyle' or 'euphoric'")
    if energy not in ["dark", "aggressive", "medium", "high"]:
        raise HTTPException(400, "energy must be 'dark', 'aggressive', 'medium', or 'high'")
    if bars not in [4, 8, 16, 32]:
        raise HTTPException(400, "bars must be 4, 8, 16, or 32")
    if not file.filename.endswith(('.mid', '.midi')):
        raise HTTPException(400, "File must be a MIDI file (.mid or .midi)")
    
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Empty MIDI file")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "MIDI file too large (max 5MB)")
    
    # Parse MIDI
    try:
        parsed = parse_midi(content)
        logger.info(f"Parsed MIDI: BPM={parsed.bpm}, Key={parsed.key_name}, Bars={parsed.total_bars}")
    except ValueError as e:
        raise HTTPException(422, f"MIDI parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to parse MIDI file")
    
    # Generate
    try:
        trend = get_trend_engine()
        engine = HardstyleGenerationEngine(trend)
        
        config = GenerationConfig(
            style=style,
            energy=energy,
            bars=bars,
        )
        
        result = engine.generate(parsed, config)
        logger.info(f"Generated MIDI using patterns: {result.pattern_ids_used}")
        
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(500, f"Generation failed: {str(e)}")
    
    # Package as ZIP
    session_id = str(uuid.uuid4())[:8].upper()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lead.mid", result.lead)
        zf.writestr("chords.mid", result.chords)
        zf.writestr("pads.mid", result.pads)
        
        import json
        metadata = {
            **result.metadata,
            "session_id": session_id,
            "generated_files": ["lead.mid", "chords.mid", "pads.mid"],
            "fl_studio_instructions": (
                "Drag each .mid file into FL Studio. "
                "Lead → Synth Lead channel. "
                "Chords → Pluck/Pad channel. "
                "Pads → Long Pad/Strings channel."
            )
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    zip_buffer.seek(0)
    
    # Background: record analytics
    background_tasks.add_task(
        trend.record_download,
        result.pattern_ids_used
    )
    
    filename = f"hardstyle_midi_{session_id}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Session-ID": session_id,
            "X-BPM": str(parsed.bpm),
            "X-Key": parsed.key_name,
        }
    )


@app.get("/trends")
async def get_trends():
    """
    Return current trend data and pattern analytics.
    """
    trend = get_trend_engine()
    return trend.get_trend_summary()


@app.get("/styles")
async def get_styles():
    """Return available generation styles and their descriptions."""
    return {
        "styles": [
            {
                "id": "rawstyle",
                "name": "Rawstyle",
                "description": "Dark, aggressive, distorted kicks with raw leads",
                "bpm_range": "150-165",
                "energy_options": ["dark", "aggressive"],
                "characteristics": ["Power chord stabs", "Phrygian scales", "Aggressive leads"]
            },
            {
                "id": "euphoric",
                "name": "Euphoric Hardstyle",
                "description": "Uplifting melodies, lush chords, emotional leads",
                "bpm_range": "155-170",
                "energy_options": ["medium", "high"],
                "characteristics": ["Lush pad chords", "Ascending melodies", "Harmonic richness"]
            }
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse({"error": "Not found", "path": str(request.url)}, status_code=404)


@app.exception_handler(500)
async def server_error(request, exc):
    return JSONResponse({"error": "Internal server error"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
