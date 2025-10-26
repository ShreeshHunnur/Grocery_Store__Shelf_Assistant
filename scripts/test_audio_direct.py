#!/usr/bin/env python3
"""
Direct audio I/O test script to verify microphone recording and transcription.
This bypasses the web interface to test the core audio functionality.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.audio_io import AudioIOService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_audio_io():
    """Test the audio I/O service directly."""
    print("🎤 Testing Audio I/O Service")
    print("=" * 50)
    
    try:
        # Initialize audio service
        print("1. Initializing Audio I/O Service...")
        audio_service = AudioIOService()
        
        # Check health
        print("2. Checking service health...")
        health = audio_service.get_health_status()
        print(f"   Health Status: {health}")
        
        if not health.get('overall') == 'healthy':
            print("❌ Audio service is not healthy!")
            return False
        
        print("✅ Audio service is healthy!")
        
        # Test recording
        print("\n3. Testing microphone recording...")
        print("   Speak clearly into your microphone for 3 seconds...")
        print("   Recording starts in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("   🎤 RECORDING NOW - SPEAK CLEARLY!")
        
        # Record audio
        audio_data = audio_service.record(duration=3.0)
        
        if audio_data is None or len(audio_data) == 0:
            print("❌ No audio data recorded!")
            return False
        
        print(f"✅ Recorded {len(audio_data)} samples")
        print(f"   Audio shape: {audio_data.shape}")
        print(f"   Audio range: {audio_data.min():.4f} to {audio_data.max():.4f}")
        print(f"   Non-zero samples: {len(audio_data[audio_data != 0])}")
        
        # Test transcription
        print("\n4. Testing speech-to-text transcription...")
        print("   Transcribing your speech...")
        
        transcribed_text = audio_service.transcribe(audio_data)
        
        if not transcribed_text or not transcribed_text.strip():
            print("❌ No speech detected in audio!")
            print("   This could mean:")
            print("   - Microphone is not working")
            print("   - Audio was too quiet")
            print("   - No speech was detected")
            return False
        
        print(f"✅ Transcription successful!")
        print(f"   Transcribed text: '{transcribed_text}'")
        
        # Test TTS
        print("\n5. Testing text-to-speech synthesis...")
        test_text = "Hello, this is a test of the text to speech system."
        print(f"   Synthesizing: '{test_text}'")
        
        tts_audio = audio_service.synthesize(test_text)
        
        if tts_audio is None or len(tts_audio) == 0:
            print("❌ TTS synthesis failed!")
            return False
        
        print(f"✅ TTS synthesis successful!")
        print(f"   Generated {len(tts_audio)} audio samples")
        
        # Test playback (optional)
        print("\n6. Testing audio playback...")
        print("   Playing back the synthesized audio...")
        print("   (You should hear the TTS output)")
        
        audio_service.play(tts_audio)
        
        print("✅ Audio playback completed!")
        
        # Cleanup
        print("\n7. Cleaning up...")
        audio_service.cleanup()
        
        print("\n🎉 All audio tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        logger.exception("Audio test failed")
        return False

def test_microphone_permissions():
    """Test if microphone permissions are working."""
    print("\n🔍 Testing Microphone Permissions")
    print("=" * 50)
    
    try:
        import pyaudio
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # List audio devices
        print("Available audio devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  Device {i}: {info['name']} (Input channels: {info['maxInputChannels']})")
        
        # Test opening a stream
        print("\nTesting microphone access...")
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("✅ Microphone access successful!")
        
        # Close stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return True
        
    except Exception as e:
        print(f"❌ Microphone permission test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Audio I/O Direct Test")
    print("=" * 50)
    
    # Test microphone permissions first
    mic_ok = test_microphone_permissions()
    
    if not mic_ok:
        print("\n❌ Microphone permissions test failed!")
        print("Please check:")
        print("1. Microphone is connected and working")
        print("2. Microphone permissions are granted")
        print("3. No other applications are using the microphone")
        sys.exit(1)
    
    # Test full audio I/O
    audio_ok = test_audio_io()
    
    if audio_ok:
        print("\n🎉 All audio tests passed!")
        print("The audio system is working correctly.")
    else:
        print("\n❌ Audio tests failed!")
        print("Please check the error messages above.")
        sys.exit(1)
