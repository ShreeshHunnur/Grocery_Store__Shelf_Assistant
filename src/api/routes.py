"""
API routes for the Retail Shelf Assistant.
"""
import logging
import io
import tempfile
from pathlib import Path
# Update imports - remove AudioIOService
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional
import numpy as np
from starlette.background import BackgroundTask

from .models import (
    TextQueryRequest, 
    ProductLocationResponse, 
    ProductInfoResponse,
    ErrorResponse
)
from .orchestrator import BackendOrchestrator
# Remove this line
# from src.services.audio_io import AudioIOService
# Keep only this import
from src.services.google_audio_io import GoogleAudioIOService
from typing import Dict

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/ask", response_model=dict)
async def process_text_query(request: TextQueryRequest):
    """
    Process a text-based product query.
    
    This endpoint accepts a text query and returns either:
    - ProductLocationResponse: For location queries
    - ProductInfoResponse: For information queries
    """
    try:
        logger.info(f"Processing text query: {request.query[:50]}...")
        
        # Get orchestrator instance
        from .main import orchestrator
        response = orchestrator.process_text_query(request.query, request.session_id)
        
        # Check if response is an error
        if "error" in response:
            error_code = response.get("error_code", "UNKNOWN_ERROR")
            if error_code in ["DB_ERROR", "LLM_ERROR", "PROCESSING_ERROR"]:
                raise HTTPException(status_code=500, detail=response)
            else:
                raise HTTPException(status_code=400, detail=response)
        
        return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing text query: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Internal server error",
                error_code="INTERNAL_ERROR",
                details={"message": str(e)}
            ).dict()
        )

@router.post("/ask-voice")
async def process_voice_query(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    return_audio: bool = Form(True)
):
    """
    Process an audio file containing a product query.
    
    This endpoint accepts an audio file and returns either:
    - JSON response with text answer (if return_audio=False)
    - Audio file response with TTS (if return_audio=True)
    """
    try:
        logger.info(f"Processing voice query from file: {audio_file.filename}")
        
        # Validate file type
        if not audio_file.content_type or not any(
            fmt in audio_file.content_type for fmt in ["audio/", "application/octet-stream"]
        ):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="Invalid file type",
                    error_code="INVALID_FILE_TYPE",
                    details={"accepted_types": ["audio/wav", "audio/mp3", "audio/m4a", "audio/flac", "audio/webm"]}
                ).dict()
            )
        
        # Read audio file content
        audio_content = await audio_file.read()
        
        # Initialize Google audio service
        audio_service = GoogleAudioIOService()
        
        try:
            # Save the audio content to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name
            
            try:
                # Convert WebM to WAV using FFmpeg
                import subprocess
                import os
                
                # Create output WAV file path
                wav_path = temp_file_path.replace('.webm', '.wav')
                
                # Use FFmpeg to convert WebM to WAV
                ffmpeg_exe = None
                possible_ffmpeg_paths = [
                    r'C:\Users\Shreesh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffmpeg.exe',
                    r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                    r'C:\ffmpeg\bin\ffmpeg.exe',
                    'ffmpeg.exe'  # Try system PATH
                ]
                
                # Find available FFmpeg
                for path in possible_ffmpeg_paths:
                    try:
                        if path == 'ffmpeg.exe':
                            # Test if ffmpeg is in PATH
                            result = subprocess.run([path, '-version'], capture_output=True, timeout=5)
                            if result.returncode == 0:
                                ffmpeg_exe = path
                                break
                        elif os.path.exists(path):
                            ffmpeg_exe = path
                            break
                    except:
                        continue
                
                if not ffmpeg_exe:
                    raise FileNotFoundError("FFmpeg not found. Please install FFmpeg and add it to PATH.")
                
                logger.info(f"Using FFmpeg at: {ffmpeg_exe}")
                
                ffmpeg_cmd = [
                    ffmpeg_exe,
                    '-i', temp_file_path,
                    '-acodec', 'pcm_s16le',
                    '-ac', '1',  # mono
                    '-ar', '16000',  # 16kHz sample rate
                    '-y',  # overwrite output file
                    wav_path
                ]
                
                logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info("FFmpeg conversion successful")
                    
                    # Now use speech_recognition with the WAV file
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    
                    with sr.AudioFile(wav_path) as source:
                        audio_data = recognizer.record(source)
                        transcribed_text = recognizer.recognize_google(audio_data)
                    
                    if not transcribed_text.strip():
                        logger.error("No speech detected in audio")
                        raise HTTPException(
                            status_code=400,
                            detail=ErrorResponse(
                                error="No speech detected",
                                error_code="NO_SPEECH_DETECTED",
                                details={
                                    "message": "No speech was detected in the audio file. Please try speaking more clearly or check your microphone."
                                }
                            ).dict()
                        )
                    
                    logger.info(f"Transcribed text: {transcribed_text}")
                    
                    # Process the query through the orchestrator
                    from .main import orchestrator
                    response = orchestrator.process_text_query(transcribed_text, session_id, input_method="voice")
                    
                    # Check if response is an error
                    if "error" in response:
                        error_code = response.get("error_code", "UNKNOWN_ERROR")
                        if error_code in ["DB_ERROR", "LLM_ERROR", "PROCESSING_ERROR"]:
                            raise HTTPException(status_code=500, detail=response)
                        else:
                            raise HTTPException(status_code=400, detail=response)
                    
                    # If return_audio is False, return JSON response
                    if not return_audio:
                        return {
                            "transcribed_text": transcribed_text,
                            "response": response
                        }
                    
                    # Generate TTS audio for the response.
                    # Some response types (e.g. location) don't include an `answer` field,
                    # so build a human-friendly summary for TTS when needed.
                    def _build_tts_text(resp: dict) -> str:
                        # Prefer explicit 'answer' when present
                        if isinstance(resp, dict) and resp.get('answer'):
                            return resp.get('answer')

                        # Location responses: summarize matches
                        matches = resp.get('matches') if isinstance(resp, dict) else None
                        normalized = resp.get('normalized_product') if isinstance(resp, dict) else None
                        if matches is not None:
                            try:
                                count = len(matches)
                            except Exception:
                                count = 0

                            if count > 0:
                                top = matches[0]
                                name = top.get('product_name', normalized or 'the product')
                                aisle = top.get('aisle')
                                bay = top.get('bay')
                                shelf = top.get('shelf')
                                loc_parts = []
                                if aisle is not None:
                                    loc_parts.append(f"aisle {aisle}")
                                if bay is not None:
                                    loc_parts.append(f"bay {bay}")
                                if shelf is not None:
                                    loc_parts.append(f"shelf {shelf}")
                                loc_str = ', '.join(loc_parts) if loc_parts else 'an unknown location'
                                return f"I found {count} match{'es' if count != 1 else ''} for {normalized or name}. The top result is {name} located at {loc_str}."
                            else:
                                return f"I couldn't find any locations for {normalized or 'that product'}."

                        # Information responses without 'answer' fallback
                        if isinstance(resp, dict) and resp.get('query_type') == 'information':
                            # Try common fields
                            if resp.get('caveats'):
                                return resp.get('caveats')
                            if resp.get('summary'):
                                return resp.get('summary')

                        # Default fallback
                        return "I'm sorry, I couldn't process your request."

                    answer_text = _build_tts_text(response)
                    logger.info(f"Generating TTS for: {answer_text[:120]}...")

                    # Use Google TTS to generate audio
                    tts_audio, temp_file_path = audio_service.synthesize(answer_text)
                    
                    # Important: Keep a reference to audio_service until after the response is sent
                    # to prevent premature cleanup
                    
                    # Create a background task to clean up after response is sent
                    def cleanup_after_response():
                        # Now it's safe to clean up
                        audio_service.cleanup()
                    
                    # No need to create a new temporary file, use the one from synthesize
                    return FileResponse(
                        temp_file_path,
                        media_type="audio/mp3",
                        filename="response.mp3",
                        headers={"Content-Disposition": "attachment; filename=response.mp3"},
                        background=BackgroundTask(cleanup_after_response)
                    )
                else:
                    logger.error(f"FFmpeg failed: {result.stderr}")
                    error_msg = result.stderr
                    
                    # Check for specific error types
                    if "Invalid data found when processing input" in error_msg:
                        raise HTTPException(
                            status_code=400,
                            detail=ErrorResponse(
                                error="Invalid audio file",
                                error_code="INVALID_AUDIO_FORMAT",
                                details={
                                    "message": "The uploaded file is not a valid audio format or is corrupted. Please upload a valid audio file (WAV, MP3, M4A, FLAC, or WebM)."
                                }
                            ).dict()
                        )
                    elif "Format" in error_msg and "detected only with low score" in error_msg:
                        raise HTTPException(
                            status_code=400,
                            detail=ErrorResponse(
                                error="Audio format not recognized",
                                error_code="UNRECOGNIZED_AUDIO_FORMAT",
                                details={
                                    "message": "The audio format could not be recognized. Please use WAV, MP3, M4A, FLAC, or WebM format."
                                }
                            ).dict()
                        )
                    else:
                        # Generic FFmpeg error
                        raise Exception(f"FFmpeg conversion failed: {error_msg}")
            finally:
                # Clean up temporary files
                import os
                try:
                    # Don't delete temp_file_path here as it's needed by FileResponse
                    # os.unlink(temp_file_path)  # Remove this line
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)
                except:
                    pass
        finally:
            audio_service.cleanup()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice query: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to process voice query",
                error_code="VOICE_PROCESSING_ERROR",
                details={"message": str(e)}
            ).dict()
        )


@router.post("/vision", response_model=dict)
async def process_vision_image(image_file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """
    Process an uploaded image using the configured vision model (Moondream VLM).

    Returns a ProductInfoResponse-like dict with an image description and confidence.
    """
    import time
    import uuid
    from src.services.analytics_service import QueryAnalytics
    
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"Processing vision image: {image_file.filename}")

        # Basic validation
        if not image_file.content_type or not image_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=ErrorResponse(
                error="Invalid file type",
                error_code="INVALID_FILE_TYPE",
                details={"accepted_types": ["image/jpeg", "image/png", "image/webp"]}
            ).dict())

        image_bytes = await image_file.read()

        # Call LLMService vision method via orchestrator
        from .main import orchestrator

        # The orchestrator exposes llm_service; call the vision method
        try:
            vision_response = orchestrator.llm_service.generate_vision_answer(image_bytes, filename=image_file.filename)
        except Exception as e:
            logger.error(f"Vision service call failed: {e}")
            raise HTTPException(status_code=500, detail=ErrorResponse(
                error="Vision service failed",
                error_code="VLM_ERROR",
                details={"message": str(e)}
            ).dict())

        # Track analytics for vision query
        try:
            latency_ms = int((time.time() - start_time) * 1000)
            analytics = QueryAnalytics(
                session_id=session_id or f"session_{trace_id}",
                query_text=f"Image analysis: {image_file.filename}",
                query_type="vision",
                input_method="image",
                response_time_ms=latency_ms,
                confidence_score=vision_response.confidence if hasattr(vision_response, 'confidence') else None,
                success=True
            )
            orchestrator.analytics_service.track_query(analytics)
        except Exception as e:
            logger.warning(f"Failed to track analytics for vision query: {e}")

        # vision_response is a ProductInfoResponse
        return vision_response.dict()

    except HTTPException:
        raise
    except Exception as e:
        # Track failed vision query in analytics
        try:
            latency_ms = int((time.time() - start_time) * 1000)
            analytics = QueryAnalytics(
                session_id=session_id or f"session_{trace_id}",
                query_text=f"Image analysis: {image_file.filename if 'image_file' in locals() else 'unknown'}",
                query_type="vision",
                input_method="image",
                response_time_ms=latency_ms,
                confidence_score=0.0,
                success=False,
                error_message=str(e)
            )
            from .main import orchestrator
            orchestrator.analytics_service.track_query(analytics)
        except Exception:
            pass  # Don't fail on analytics tracking failure
        
        logger.error(f"Error processing vision image: {e}")
        raise HTTPException(status_code=500, detail=ErrorResponse(
            error="Failed to process image",
            error_code="VISION_PROCESSING_ERROR",
            details={"message": str(e)}
        ).dict())
