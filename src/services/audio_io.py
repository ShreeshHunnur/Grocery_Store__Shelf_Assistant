"""
Audio I/O service for voice input/output with STT and TTS capabilities.
This is now a compatibility layer that uses Google services internally.
"""
import logging
from typing import Optional, Callable, Dict, Any
import numpy as np

from config.settings import AUDIO_CONFIG
from src.services.google_audio_io import GoogleAudioIOService

logger = logging.getLogger(__name__)

class AudioIOService:
    """Service for handling audio input/output with STT and TTS.
    This is now a wrapper around GoogleAudioIOService."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize audio I/O service."""
        self.config = config or AUDIO_CONFIG
        self.google_service = GoogleAudioIOService()
        
        # State management
        self.is_recording = False
        self.is_playing = False
        self.barge_in_detected = False
        
    def record(self, duration: Optional[float] = None, 
               callback: Optional[Callable] = None) -> np.ndarray:
        """Record audio from microphone."""
        self.is_recording = True
        try:
            # Google service doesn't support VAD-based recording, so use fixed duration
            if duration is None:
                duration = self.config.get("max_recording_duration", 10.0)
            
            audio_data = self.google_service.record(duration)
            return audio_data
        finally:
            self.is_recording = False
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio to text using Google STT."""
        return self.google_service.transcribe(audio_data)
    
    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to speech using Google TTS."""
        # Google service returns bytes, but this method expects np.ndarray
        # For compatibility, we'll return an empty array and handle this in play()
        self._last_synthesized_text = text  # Store for play method
        return np.array([])
    
    def play(self, audio_data: np.ndarray, 
             interrupt_callback: Optional[Callable] = None) -> bool:
        """Play audio data through speakers."""
        self.is_playing = True
        try:
            # If audio_data is empty, use the last synthesized text
            if len(audio_data) == 0 and hasattr(self, '_last_synthesized_text'):
                audio_bytes = self.google_service.synthesize(self._last_synthesized_text)
                self.google_service.play(audio_bytes)
                return True
            else:
                # This is a simplified approach - in a real implementation,
                # you'd need to convert np.ndarray to bytes properly
                logger.warning("Direct playback of numpy arrays not fully supported")
                return False
        finally:
            self.is_playing = False
    
    def stop_playback(self):
        """Stop current audio playback."""
        self.is_playing = False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of audio components."""
        return self.google_service.get_health_status()
    
    def cleanup(self):
        """Clean up resources."""
        self.google_service.cleanup()


# Convenience functions for easy integration
def record_audio(duration: Optional[float] = None) -> np.ndarray:
    """Record audio using default settings."""
    service = AudioIOService()
    try:
        return service.record(duration)
    finally:
        service.cleanup()

def transcribe_audio(audio_data: np.ndarray) -> str:
    """Transcribe audio using default settings."""
    service = AudioIOService()
    try:
        return service.transcribe(audio_data)
    finally:
        service.cleanup()

def synthesize_text(text: str) -> np.ndarray:
    """Synthesize text using default settings."""
    service = AudioIOService()
    try:
        return service.synthesize(text)
    finally:
        service.cleanup()

def play_audio(audio_data: np.ndarray) -> bool:
    """Play audio using default settings."""
    service = AudioIOService()
    try:
        return service.play(audio_data)
    finally:
        service.cleanup()
