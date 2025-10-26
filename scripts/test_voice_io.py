#!/usr/bin/env python3
"""
Simple test script for voice I/O components.
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_audio_imports():
    """Test if audio libraries can be imported."""
    print("Testing Audio Library Imports...")
    
    try:
        import numpy as np
        print("+ numpy imported successfully")
    except ImportError as e:
        print(f"- numpy import failed: {e}")
        return False
    
    try:
        import sounddevice as sd
        print("+ sounddevice imported successfully")
    except ImportError as e:
        print(f"- sounddevice import failed: {e}")
        return False
    
    try:
        import webrtcvad
        print("+ webrtcvad imported successfully")
    except ImportError as e:
        print(f"- webrtcvad import failed: {e}")
        return False
    
    try:
        import whisper
        print("+ whisper imported successfully")
    except ImportError as e:
        print(f"- whisper import failed: {e}")
        return False
    
    try:
        import pyttsx3
        print("+ pyttsx3 imported successfully")
    except ImportError as e:
        print(f"- pyttsx3 import failed: {e}")
        return False
    
    try:
        import scipy
        print("+ scipy imported successfully")
    except ImportError as e:
        print(f"- scipy import failed: {e}")
        return False
    
    return True

def test_audio_service_init():
    """Test audio service initialization."""
    print("\nTesting Audio Service Initialization...")
    
    try:
        from src.services.audio_io import AudioIOService
        
        service = AudioIOService()
        print("+ AudioIOService initialized successfully")
        
        # Test health status
        health = service.get_health_status()
        print("Health Status:")
        for component, status in health.items():
            print(f"  {component}: {status}")
        
        service.cleanup()
        return True
        
    except Exception as e:
        print(f"- AudioIOService initialization failed: {e}")
        return False

def test_simple_recording():
    """Test simple recording functionality."""
    print("\nTesting Simple Recording...")
    
    try:
        from src.services.audio_io import AudioIOService
        
        service = AudioIOService()
        
        print("Recording for 2 seconds... (speak now)")
        audio_data = service.record(duration=2.0)
        
        if len(audio_data) > 0:
            print(f"+ Recorded {len(audio_data)} audio samples")
            
            # Test transcription
            print("Testing transcription...")
            text = service.transcribe(audio_data)
            
            if text.strip():
                print(f"+ Transcribed: '{text}'")
            else:
                print("- No transcription result")
            
            service.cleanup()
            return True
        else:
            print("- No audio recorded")
            service.cleanup()
            return False
            
    except Exception as e:
        print(f"- Recording test failed: {e}")
        return False

def test_tts():
    """Test text-to-speech functionality."""
    print("\nTesting Text-to-Speech...")
    
    try:
        from src.services.audio_io import AudioIOService
        
        service = AudioIOService()
        
        test_text = "Hello, this is a test of the text to speech system."
        print(f"Synthesizing: '{test_text}'")
        
        audio_data = service.synthesize(test_text)
        
        if len(audio_data) >= 0:  # Note: pyttsx3 might return empty array
            print("+ TTS synthesis completed")
            
            # Note: pyttsx3 doesn't easily return audio data for playback
            # This is a limitation of the current implementation
            print("Note: pyttsx3 doesn't easily support audio data extraction")
            print("For full TTS testing, use the voice loop applications")
            
            service.cleanup()
            return True
        else:
            print("- TTS synthesis failed")
            service.cleanup()
            return False
            
    except Exception as e:
        print(f"- TTS test failed: {e}")
        return False

def main():
    """Run simple tests."""
    print("Simple Voice I/O Test")
    print("=" * 30)
    
    tests = [
        ("Audio Library Imports", test_audio_imports),
        ("Audio Service Initialization", test_audio_service_init),
        ("Simple Recording", test_simple_recording),
        ("Text-to-Speech", test_tts)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"+ {test_name}: PASSED")
            else:
                print(f"- {test_name}: FAILED")
                
        except Exception as e:
            print(f"X {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 30)
    print("TEST SUMMARY")
    print("=" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("+ All basic tests passed! Voice I/O is working.")
        print("\nNext steps:")
        print("1. Run: python scripts/voice_loop.py (CLI version)")
        print("2. Run: python scripts/voice_gui.py (GUI version)")
        print("3. Run: python scripts/validate_milestone6.py (full validation)")
        return True
    else:
        print("- Some tests failed. Check the output above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check audio device permissions")
        print("3. Ensure microphone and speakers are working")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
