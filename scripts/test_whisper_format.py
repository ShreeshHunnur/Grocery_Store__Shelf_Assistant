#!/usr/bin/env python3
"""
Test Whisper with different audio formats to see what works best.
"""

import sys
import os
import numpy as np
import tempfile
import wave
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.audio_io import AudioIOService

def create_test_audio():
    """Create a simple test audio signal."""
    # Generate a simple sine wave at 440Hz (A note)
    sample_rate = 16000
    duration = 2.0
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t) * 0.3  # 30% volume
    
    return audio.astype(np.float32), sample_rate

def test_whisper_with_different_formats():
    """Test Whisper with different audio formats."""
    print("🧪 Testing Whisper with Different Audio Formats")
    print("=" * 60)
    
    try:
        # Initialize audio service
        audio_service = AudioIOService()
        
        # Test 1: Generate test audio
        print("1. Creating test audio signal...")
        test_audio, sample_rate = create_test_audio()
        print(f"   Generated {len(test_audio)} samples at {sample_rate}Hz")
        print(f"   Audio range: {test_audio.min():.4f} to {test_audio.max():.4f}")
        
        # Test 2: Try transcribing the test audio
        print("\n2. Testing Whisper with generated audio...")
        result = audio_service.transcribe(test_audio)
        print(f"   Transcription result: '{result}'")
        
        # Test 3: Record real audio and analyze
        print("\n3. Recording real audio for analysis...")
        print("   Speak clearly for 3 seconds...")
        
        import time
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("   🎤 RECORDING NOW!")
        real_audio = audio_service.record(duration=3.0)
        
        if real_audio is not None:
            print(f"   Recorded {len(real_audio)} samples")
            print(f"   Audio range: {real_audio.min():.4f} to {real_audio.max():.4f}")
            print(f"   Non-zero samples: {np.count_nonzero(real_audio)}")
            print(f"   RMS level: {np.sqrt(np.mean(real_audio**2)):.6f}")
            
            # Test 4: Try different audio preprocessing
            print("\n4. Testing different audio preprocessing...")
            
            # Normalize audio
            normalized_audio = real_audio / np.max(np.abs(real_audio)) if np.max(np.abs(real_audio)) > 0 else real_audio
            print(f"   Normalized audio range: {normalized_audio.min():.4f} to {normalized_audio.max():.4f}")
            
            # Amplify audio
            amplified_audio = real_audio * 10  # 10x amplification
            print(f"   Amplified audio range: {amplified_audio.min():.4f} to {amplified_audio.max():.4f}")
            
            # Test transcription with amplified audio
            print("\n5. Testing transcription with amplified audio...")
            result_amp = audio_service.transcribe(amplified_audio)
            print(f"   Amplified transcription: '{result_amp}'")
            
            # Test transcription with normalized audio
            print("\n6. Testing transcription with normalized audio...")
            result_norm = audio_service.transcribe(normalized_audio)
            print(f"   Normalized transcription: '{result_norm}'")
            
        else:
            print("   ❌ No audio recorded!")
        
        # Cleanup
        audio_service.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_whisper_with_different_formats()
