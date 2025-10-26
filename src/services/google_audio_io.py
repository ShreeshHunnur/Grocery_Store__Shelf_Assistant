#!/usr/bin/env python3
"""
Google-based Audio I/O Service using Google TTS and Google STT.
This provides much better quality than the local alternatives.
"""

import logging
import tempfile
import os
import io
import numpy as np
from typing import Optional, Dict, Any
from gtts import gTTS
import speech_recognition as sr
import pyaudio
import wave

logger = logging.getLogger(__name__)

class GoogleAudioIOService:
    """Audio I/O service using Google TTS and Google STT for better quality."""
    
    def __init__(self):
        """Initialize the Google Audio I/O service."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Audio parameters
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        
        # Initialize PyAudio for recording
        self.pyaudio_instance = pyaudio.PyAudio()
        
        logger.info("Google Audio I/O service initialized")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the audio service."""
        try:
            # Test microphone access
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
            
            return {
                'google_stt': 'healthy',
                'google_tts': 'healthy',
                'microphone': 'healthy',
                'overall': 'healthy'
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'google_stt': 'unhealthy',
                'google_tts': 'unhealthy', 
                'microphone': 'unhealthy',
                'overall': 'unhealthy',
                'error': str(e)
            }
    
    def record(self, duration: float = 3.0) -> Optional[np.ndarray]:
        """Record audio from microphone using PyAudio."""
        try:
            logger.info(f"Recording for {duration} seconds...")
            
            # Open audio stream
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            num_chunks = int(self.sample_rate * duration / self.chunk_size)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            logger.info(f"Recording completed: {len(audio_float)} samples")
            return audio_float
            
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using Google Speech Recognition."""
        try:
            logger.info("Starting Google STT transcription...")
            
            # Convert numpy array back to audio data
            audio_int16 = (audio_data * 32768).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # Create AudioData object for speech_recognition
            audio_data_obj = sr.AudioData(
                audio_bytes,
                self.sample_rate,
                2  # 2 bytes per sample (16-bit)
            )
            
            # Use Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(audio_data_obj)
                logger.info(f"Google STT transcription completed: '{text}'")
                return text
            except sr.UnknownValueError:
                logger.warning("Google STT could not understand the audio")
                return ""
            except sr.RequestError as e:
                logger.error(f"Google STT request failed: {e}")
                return ""
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    def synthesize(self, text: str, language: str = 'en') -> tuple:
        """Synthesize text to speech using Google TTS.
        
        Returns:
            tuple: (audio_data, file_path) where audio_data is the binary MP3 data
                  and file_path is the path to the temporary file containing the audio
        """
        try:
            logger.info(f"Google TTS synthesizing: '{text[:50]}...'")
            
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name
            
            # Save TTS to file
            tts.save(temp_file_path)
            
            # Read the MP3 file
            with open(temp_file_path, 'rb') as f:
                audio_data = f.read()
            
            logger.info(f"Google TTS synthesis completed: {len(audio_data)} bytes")
            return audio_data, temp_file_path
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return b"", ""
    
    def play(self, audio_data: bytes) -> None:
        """Play audio data using PyAudio."""
        try:
            # For MP3 data from Google TTS, we need to convert to WAV
            # For now, save to temp file and play using system player
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Use system command to play (Windows)
            import subprocess
            subprocess.run(['start', temp_file_path], shell=True, check=False)
            
            # Clean up after a delay
            import threading
            def cleanup():
                import time
                time.sleep(5)  # Wait for playback
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            if hasattr(self, 'pyaudio_instance'):
                self.pyaudio_instance.terminate()
            logger.info("Google Audio I/O service cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
