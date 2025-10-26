#!/usr/bin/env python3
"""
Simple microphone level test to check if audio is being captured properly.
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyaudio

def test_microphone_level():
    """Test microphone input levels in real-time."""
    print("🎤 Microphone Level Test")
    print("=" * 50)
    print("Speak into your microphone and watch the levels...")
    print("Press Ctrl+C to stop")
    print()
    
    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    try:
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print("Listening... (Speak now!)")
        print("Level: |" + "=" * 50 + "|")
        
        while True:
            # Read audio data
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calculate level
            level = np.abs(audio_data).mean()
            max_level = np.abs(audio_data).max()
            
            # Convert to percentage
            level_percent = min(100, (level / 32768) * 100)
            max_percent = min(100, (max_level / 32768) * 100)
            
            # Create visual level bar
            bar_length = int(level_percent / 2)  # Scale to 50 chars
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            # Color coding
            if level_percent > 20:
                color = "🟢"  # Green - good level
            elif level_percent > 5:
                color = "🟡"  # Yellow - low level
            else:
                color = "🔴"  # Red - very low level
            
            # Print level
            print(f"\r{color} Level: {level_percent:5.1f}% |{bar}| Max: {max_percent:5.1f}%", end="", flush=True)
            
            # Small delay
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping microphone test...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("\n✅ Microphone test completed!")

if __name__ == "__main__":
    test_microphone_level()
