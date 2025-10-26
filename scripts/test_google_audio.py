#!/usr/bin/env python3
"""
Test Google TTS and STT functionality.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.google_audio_io import GoogleAudioIOService

def test_google_audio():
    """Test Google TTS and STT."""
    print("🎤 Testing Google Audio I/O")
    print("=" * 50)
    
    try:
        # Initialize service
        print("1. Initializing Google Audio I/O Service...")
        audio_service = GoogleAudioIOService()
        
        # Check health
        print("2. Checking service health...")
        health = audio_service.get_health_status()
        print(f"   Health Status: {health}")
        
        if health.get('overall') != 'healthy':
            print("❌ Service is not healthy!")
            return False
        
        print("✅ Service is healthy!")
        
        # Test TTS
        print("\n3. Testing Google TTS...")
        test_text = "Hello, this is a test of Google Text to Speech. Can you hear me clearly?"
        print(f"   Synthesizing: '{test_text}'")
        
        tts_audio = audio_service.synthesize(test_text)
        
        if not tts_audio:
            print("❌ TTS synthesis failed!")
            return False
        
        print(f"✅ TTS synthesis successful! ({len(tts_audio)} bytes)")
        
        # Test playback
        print("\n4. Testing audio playback...")
        print("   Playing TTS audio...")
        audio_service.play(tts_audio)
        print("   (You should hear the TTS output)")
        
        # Test STT
        print("\n5. Testing Google STT...")
        print("   Speak clearly for 3 seconds...")
        print("   Recording starts in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("   🎤 RECORDING NOW - SPEAK CLEARLY!")
        
        # Record audio
        audio_data = audio_service.record(duration=3.0)
        
        if audio_data is None or len(audio_data) == 0:
            print("❌ No audio recorded!")
            return False
        
        print(f"✅ Recorded {len(audio_data)} samples")
        
        # Transcribe
        print("\n6. Testing Google STT transcription...")
        transcribed_text = audio_service.transcribe(audio_data)
        
        if not transcribed_text or not transcribed_text.strip():
            print("❌ No speech detected!")
            return False
        
        print(f"✅ Transcription successful!")
        print(f"   Transcribed text: '{transcribed_text}'")
        
        # Cleanup
        print("\n7. Cleaning up...")
        audio_service.cleanup()
        
        print("\n🎉 All Google Audio tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_audio()
    if success:
        print("\n🎉 Google Audio I/O is working perfectly!")
    else:
        print("\n❌ Google Audio I/O test failed!")
        sys.exit(1)
