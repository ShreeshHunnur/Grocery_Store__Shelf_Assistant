#!/usr/bin/env python3
"""
Quick Performance Test Script
Simplified version for quick performance checks.
"""
import requests
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def quick_performance_test():
    """Run a quick performance test on all three modes."""
    base_url = "http://localhost:8000"
    
    print("🚀 Quick Performance Test for Grocery Assistant")
    print("="*50)
    
    # Check server health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not healthy: {response.status_code}")
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    results = {}
    
    # Test 1: Text Mode
    print("\n🔤 Testing Text Mode...")
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json={"query": "Where can I find milk?", "session_id": "perf_test"},
            timeout=15
        )
        text_time = (time.time() - start_time) * 1000
        text_success = response.status_code == 200
        
        if text_success:
            data = response.json()
            matches = len(data.get('matches', []))
            print(f"   ✅ Success: {text_time:.1f}ms, {matches} matches found")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        
        results['text'] = {'time_ms': text_time, 'success': text_success}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['text'] = {'time_ms': -1, 'success': False}
    
    # Test 2: Voice Mode (simplified - just test the endpoint)
    print("\n🎤 Testing Voice Mode...")
    start_time = time.time()
    try:
        # Create a simple test file
        test_data = b"fake audio data for testing"
        files = {'audio_file': ('test.wav', test_data, 'audio/wav')}
        data = {'session_id': 'perf_test', 'return_audio': 'false'}
        
        response = requests.post(
            f"{base_url}/api/v1/ask-voice",
            files=files,
            data=data,
            timeout=30
        )
        voice_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            voice_success = True
            print(f"   ✅ Success: {voice_time:.1f}ms")
        elif response.status_code == 400:
            voice_success = True  # Expected for fake audio
            try:
                error_detail = response.json()
                error_code = error_detail.get('detail', {}).get('error_code', '')
                if error_code in ['INVALID_AUDIO_FORMAT', 'UNRECOGNIZED_AUDIO_FORMAT']:
                    print(f"   ✅ Endpoint working: {voice_time:.1f}ms (expected error for fake audio)")
                else:
                    print(f"   ⚠️  Endpoint working: {voice_time:.1f}ms (error: {error_code})")
            except:
                print(f"   ⚠️  Endpoint working: {voice_time:.1f}ms (expected error for fake audio)")
        elif response.status_code == 500:
            voice_success = False
            try:
                error_detail = response.json()
                if "FFmpeg" in str(error_detail):
                    print(f"   ❌ FFmpeg not found: {voice_time:.1f}ms")
                    print(f"      Install FFmpeg: https://ffmpeg.org/download.html")
                elif "FileNotFoundError" in str(error_detail):
                    print(f"   ❌ Missing dependency: {voice_time:.1f}ms")
                    print(f"      Error: {error_detail}")
                else:
                    print(f"   ❌ Server error: {voice_time:.1f}ms")
                    print(f"      Error: {error_detail}")
            except:
                print(f"   ❌ Server error: {voice_time:.1f}ms (status: {response.status_code})")
        else:
            voice_success = False
            print(f"   ❌ Failed: {response.status_code}, {voice_time:.1f}ms")
        
        results['voice'] = {'time_ms': voice_time, 'success': voice_success}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['voice'] = {'time_ms': -1, 'success': False}
    
    # Test 3: Vision Mode (simplified - just test the endpoint)
    print("\n👁️  Testing Vision Mode...")
    start_time = time.time()
    try:
        # Create a simple test file
        test_data = b"fake image data for testing"
        files = {'image_file': ('test.jpg', test_data, 'image/jpeg')}
        data = {'session_id': 'perf_test'}
        
        response = requests.post(
            f"{base_url}/api/v1/vision",
            files=files,
            data=data,
            timeout=30
        )
        vision_time = (time.time() - start_time) * 1000
        vision_success = response.status_code in [200, 400]  # 400 might be expected for fake image
        
        if response.status_code == 200:
            print(f"   ✅ Success: {vision_time:.1f}ms")
        elif response.status_code == 400:
            print(f"   ⚠️  Endpoint working: {vision_time:.1f}ms (expected error for fake image)")
        else:
            print(f"   ❌ Failed: {response.status_code}")
        
        results['vision'] = {'time_ms': vision_time, 'success': vision_success}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['vision'] = {'time_ms': -1, 'success': False}
    
    # Summary
    print("\n📊 Performance Summary:")
    print("="*30)
    
    total_successful = sum(1 for r in results.values() if r['success'])
    avg_time = sum(r['time_ms'] for r in results.values() if r['time_ms'] > 0) / len([r for r in results.values() if r['time_ms'] > 0])
    
    for mode, result in results.items():
        status = "✅" if result['success'] else "❌"
        time_str = f"{result['time_ms']:.1f}ms" if result['time_ms'] > 0 else "Failed"
        print(f"   {status} {mode.capitalize()}: {time_str}")
    
    print(f"\nOverall: {total_successful}/3 modes working")
    if avg_time > 0:
        print(f"Average response time: {avg_time:.1f}ms")
    
    # Performance assessment
    if total_successful == 3:
        if avg_time < 1000:
            print("🚀 Excellent performance!")
        elif avg_time < 3000:
            print("⚡ Good performance!")
        else:
            print("⚠️  Performance could be improved")
    else:
        print("🔧 Some modes need attention")

if __name__ == "__main__":
    quick_performance_test()