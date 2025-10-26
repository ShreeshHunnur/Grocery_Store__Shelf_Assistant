#!/usr/bin/env python3
"""
Validation script for Milestone 6: Voice I/O performance testing.
"""
import sys
import time
import statistics
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.audio_io import AudioIOService
from src.api.orchestrator import BackendOrchestrator

def test_audio_components():
    """Test individual audio components."""
    print("Testing Audio Components...")
    print("=" * 40)
    
    service = AudioIOService()
    
    try:
        # Test health status
        health = service.get_health_status()
        print("Component Health:")
        for component, status in health.items():
            print(f"  {component}: {status}")
        
        # Test VAD
        print("\nTesting VAD...")
        if health.get('vad') == 'healthy':
            print("+ VAD is working")
        else:
            print("- VAD is not working")
        
        # Test STT
        print("\nTesting STT...")
        if health.get('stt') == 'healthy':
            print("+ STT model is loaded")
        else:
            print("- STT model is not loaded")
        
        # Test TTS
        print("\nTesting TTS...")
        if health.get('tts') == 'healthy':
            print("+ TTS engine is working")
        else:
            print("- TTS engine is not working")
        
        return health.get('overall') == 'healthy'
        
    finally:
        service.cleanup()

def test_recording_performance():
    """Test recording performance."""
    print("\nTesting Recording Performance...")
    print("=" * 40)
    
    service = AudioIOService()
    
    try:
        # Test fixed duration recording
        durations = [1.0, 2.0, 3.0]
        recording_times = []
        
        for duration in durations:
            print(f"Testing {duration}s recording...")
            
            start_time = time.time()
            audio_data = service.record(duration=duration)
            recording_time = time.time() - start_time
            
            if len(audio_data) > 0:
                print(f"+ Recorded {len(audio_data)} samples in {recording_time:.2f}s")
                recording_times.append(recording_time)
            else:
                print(f"- Recording failed for {duration}s")
        
        if recording_times:
            avg_time = statistics.mean(recording_times)
            print(f"\nAverage recording time: {avg_time:.2f}s")
            return avg_time < 1.0  # Should be close to requested duration
        else:
            print("- No successful recordings")
            return False
            
    finally:
        service.cleanup()

def test_transcription_performance():
    """Test transcription performance."""
    print("\nTesting Transcription Performance...")
    print("=" * 40)
    
    service = AudioIOService()
    
    try:
        # Test with different audio lengths
        test_cases = [
            ("Short audio", 1.0),
            ("Medium audio", 3.0),
            ("Long audio", 5.0)
        ]
        
        transcription_times = []
        
        for test_name, duration in test_cases:
            print(f"Testing {test_name} ({duration}s)...")
            
            # Record audio
            audio_data = service.record(duration=duration)
            
            if len(audio_data) > 0:
                # Transcribe
                start_time = time.time()
                text = service.transcribe(audio_data)
                transcription_time = time.time() - start_time
                
                if text.strip():
                    print(f"+ Transcribed '{text[:50]}...' in {transcription_time:.2f}s")
                    transcription_times.append(transcription_time)
                else:
                    print(f"- No transcription for {test_name}")
            else:
                print(f"- No audio recorded for {test_name}")
        
        if transcription_times:
            avg_time = statistics.mean(transcription_times)
            print(f"\nAverage transcription time: {avg_time:.2f}s")
            return avg_time < 2.0  # Should be under 2 seconds
        else:
            print("- No successful transcriptions")
            return False
            
    finally:
        service.cleanup()

def test_end_to_end_performance():
    """Test end-to-end voice query performance."""
    print("\nTesting End-to-End Performance...")
    print("=" * 40)
    
    service = AudioIOService()
    orchestrator = BackendOrchestrator()
    
    try:
        # Test queries
        test_queries = [
            "where is the milk",
            "find apples",
            "what are the ingredients in bread",
            "is this product gluten free",
            "how many calories in yogurt"
        ]
        
        total_times = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test {i}: '{query}'")
            
            # Record audio (simulate voice input)
            start_time = time.time()
            audio_data = service.record(duration=2.0)  # Simulate 2s of speech
            
            if len(audio_data) == 0:
                print(f"- No audio recorded for test {i}")
                continue
            
            # Transcribe
            text = service.transcribe(audio_data)
            
            if not text.strip():
                print(f"- No transcription for test {i}")
                continue
            
            # Process query
            response = orchestrator.process_text_query(text, f"test_session_{i}")
            
            # Synthesize response
            if "answer" in response:
                answer_text = response["answer"]
                audio_response = service.synthesize(answer_text)
                
                # Play response (simulate)
                if len(audio_response) > 0:
                    completed = service.play(audio_response)
            
            total_time = time.time() - start_time
            total_times.append(total_time)
            
            print(f"+ Completed in {total_time:.2f}s")
        
        if total_times:
            median_time = statistics.median(total_times)
            avg_time = statistics.mean(total_times)
            
            print(f"\nPerformance Results:")
            print(f"  Median time: {median_time:.2f}s")
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Target: < 3.5s")
            
            success = median_time < 3.5
            print(f"  Result: {'PASS' if success else 'FAIL'}")
            
            return success
        else:
            print("- No successful end-to-end tests")
            return False
            
    finally:
        service.cleanup()

def test_barge_in_functionality():
    """Test barge-in functionality."""
    print("\nTesting Barge-in Functionality...")
    print("=" * 40)
    
    service = AudioIOService()
    
    try:
        # Test barge-in detection
        print("Testing barge-in detection...")
        
        # Create dummy audio data for playback
        dummy_audio = service.record(duration=1.0)
        
        if len(dummy_audio) > 0:
            # Test barge-in detection
            barge_in_detected = service.detect_barge_in()
            print(f"Barge-in detection: {'Working' if barge_in_detected is not None else 'Not working'}")
            
            # Test playback with barge-in callback
            print("Testing playback with barge-in...")
            completed = service.play(dummy_audio, interrupt_callback=service.detect_barge_in)
            print(f"Playback completed: {completed}")
            
            return True
        else:
            print("- No audio data for barge-in testing")
            return False
            
    finally:
        service.cleanup()

def main():
    """Run all validation tests."""
    print("Milestone 6: Voice I/O Validation")
    print("=" * 50)
    
    tests = [
        ("Audio Components", test_audio_components),
        ("Recording Performance", test_recording_performance),
        ("Transcription Performance", test_transcription_performance),
        ("End-to-End Performance", test_end_to_end_performance),
        ("Barge-in Functionality", test_barge_in_functionality)
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
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("+ All tests passed! Milestone 6 validation successful.")
        return True
    else:
        print("- Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
