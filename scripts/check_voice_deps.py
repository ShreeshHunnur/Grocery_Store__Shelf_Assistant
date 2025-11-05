#!/usr/bin/env python3
"""
Check if FFmpeg is available for voice processing
"""
import subprocess
import os
import sys

def check_ffmpeg():
    """Check if FFmpeg is available and working."""
    print("🔍 Checking FFmpeg availability...")
    
    # Common FFmpeg paths
    ffmpeg_paths = [
        'ffmpeg.exe',  # System PATH
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Users\Shreesh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin\ffmpeg.exe'
    ]
    
    ffmpeg_found = False
    working_path = None
    
    for path in ffmpeg_paths:
        try:
            print(f"   Testing: {path}")
            
            if path == 'ffmpeg.exe':
                # Test system PATH
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    print(f"   ✅ Found in system PATH")
                    ffmpeg_found = True
                    working_path = path
                    break
                else:
                    print(f"   ❌ Not in system PATH")
            else:
                # Test specific path
                if os.path.exists(path):
                    result = subprocess.run([path, '-version'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        print(f"   ✅ Found at: {path}")
                        ffmpeg_found = True
                        working_path = path
                        break
                    else:
                        print(f"   ❌ Exists but not working: {path}")
                else:
                    print(f"   ❌ Not found: {path}")
                    
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Timeout testing: {path}")
        except FileNotFoundError:
            print(f"   ❌ Not found: {path}")
        except Exception as e:
            print(f"   ❌ Error testing {path}: {e}")
    
    print("\n" + "="*50)
    
    if ffmpeg_found:
        print(f"✅ FFmpeg is available at: {working_path}")
        print("   Voice mode should work properly!")
        
        # Show version info
        try:
            result = subprocess.run([working_path, '-version'], 
                                  capture_output=True, text=True, timeout=5)
            version_line = result.stdout.split('\n')[0]
            print(f"   Version: {version_line}")
        except:
            pass
            
        return True
    else:
        print("❌ FFmpeg not found!")
        print("\n📋 To fix voice mode, install FFmpeg:")
        print("   1. Download from: https://ffmpeg.org/download.html")
        print("   2. Extract to C:\\ffmpeg\\")
        print("   3. Add C:\\ffmpeg\\bin\\ to your system PATH")
        print("   4. Or install via winget: winget install Gyan.FFmpeg")
        print("   5. Restart your terminal/VS Code after installation")
        return False

def check_speech_recognition():
    """Check if speech_recognition is available."""
    try:
        import speech_recognition as sr
        print("✅ speech_recognition library is available")
        return True
    except ImportError:
        print("❌ speech_recognition library not found")
        print("   Install with: pip install SpeechRecognition")
        return False

def main():
    print("🔧 Voice Mode Dependency Check")
    print("="*40)
    
    ffmpeg_ok = check_ffmpeg()
    sr_ok = check_speech_recognition()
    
    print("\n📊 Summary:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   SpeechRecognition: {'✅' if sr_ok else '❌'}")
    
    if ffmpeg_ok and sr_ok:
        print("\n🚀 Voice mode should work properly!")
        return 0
    else:
        print("\n🔧 Voice mode needs attention - fix the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())