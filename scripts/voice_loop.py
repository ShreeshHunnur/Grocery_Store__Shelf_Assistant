#!/usr/bin/env python3
"""
Voice Loop CLI for testing voice I/O integration.
"""
import sys
import time
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.audio_io import AudioIOService
from src.api.orchestrator import BackendOrchestrator

class VoiceLoop:
    """Voice loop for interactive voice queries."""
    
    def __init__(self):
        """Initialize voice loop."""
        self.audio_service = AudioIOService()
        self.orchestrator = BackendOrchestrator()
        self.running = False
        self.session_id = f"voice_session_{int(time.time())}"
        
    def start(self):
        """Start the voice loop."""
        print("Voice Loop - Retail Shelf Assistant")
        print("=" * 50)
        print("Commands:")
        print("  speak     - Start listening for voice input")
        print("  test      - Test audio components")
        print("  health    - Check system health")
        print("  quit      - Exit the application")
        print()
        
        self.running = True
        
        while self.running:
            try:
                command = input("> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    self.stop()
                elif command == 'speak':
                    self.handle_voice_input()
                elif command == 'test':
                    self.test_audio_components()
                elif command == 'health':
                    self.check_health()
                elif command == 'help':
                    self.show_help()
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.stop()
            except Exception as e:
                print(f"Error: {e}")
    
    def handle_voice_input(self):
        """Handle voice input and processing."""
        try:
            print("\nListening... (speak now)")
            
            # Record audio
            start_time = time.time()
            audio_data = self.audio_service.record()
            recording_time = time.time() - start_time
            
            if len(audio_data) == 0:
                print("No audio recorded. Please try again.")
                return
            
            print(f"Recording completed in {recording_time:.2f}s")
            print("Transcribing...")
            
            # Transcribe audio
            transcription_start = time.time()
            text = self.audio_service.transcribe(audio_data)
            transcription_time = time.time() - transcription_start
            
            if not text.strip():
                print("No speech detected. Please try again.")
                return
            
            print(f"Transcription ({transcription_time:.2f}s): '{text}'")
            print("Processing query...")
            
            # Process query through orchestrator
            processing_start = time.time()
            response = self.orchestrator.process_text_query(text, self.session_id)
            processing_time = time.time() - processing_start
            
            # Handle response
            if "error" in response:
                print(f"Error: {response['error']}")
                return
            
            print(f"Response ({processing_time:.2f}s):")
            self.display_response(response)
            
            # Synthesize and play response
            if "answer" in response:
                answer_text = response["answer"]
                print(f"\nSpeaking: '{answer_text[:100]}...'")
                
                synthesis_start = time.time()
                audio_response = self.audio_service.synthesize(answer_text)
                synthesis_time = time.time() - synthesis_start
                
                if len(audio_response) > 0:
                    playback_start = time.time()
                    completed = self.audio_service.play(
                        audio_response, 
                        interrupt_callback=self.audio_service.detect_barge_in
                    )
                    playback_time = time.time() - playback_start
                    
                    status = "completed" if completed else "interrupted"
                    print(f"Playback {status} in {playback_time:.2f}s")
                else:
                    print("TTS synthesis failed")
            
            total_time = time.time() - start_time
            print(f"\nTotal processing time: {total_time:.2f}s")
            
        except Exception as e:
            print(f"Error in voice processing: {e}")
    
    def display_response(self, response):
        """Display the response in a formatted way."""
        if response.get("query_type") == "location":
            print(f"Query Type: Location")
            print(f"Product: {response.get('normalized_product', 'Unknown')}")
            
            matches = response.get("matches", [])
            if matches:
                print("Found locations:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"  {i}. {match.get('product_name', 'Unknown')} - "
                          f"Aisle {match.get('aisle', '?')}, "
                          f"Bay {match.get('bay', '?')}, "
                          f"Shelf {match.get('shelf', '?')} "
                          f"(confidence: {match.get('confidence', 0):.2f})")
            else:
                print("No locations found")
                
            if response.get("disambiguation_needed"):
                print("Disambiguation needed - please be more specific")
                
        elif response.get("query_type") == "information":
            print(f"Query Type: Information")
            print(f"Product: {response.get('normalized_product', 'Unknown')}")
            print(f"Answer: {response.get('answer', 'No answer available')}")
            
            caveats = response.get("caveats")
            if caveats:
                print(f"Caveats: {caveats}")
            
            confidence = response.get("confidence", 0)
            print(f"Confidence: {confidence:.2f}")
    
    def test_audio_components(self):
        """Test audio components."""
        print("\nTesting Audio Components...")
        
        # Test VAD
        print("Testing VAD...")
        health = self.audio_service.get_health_status()
        print(f"VAD Status: {health.get('vad', 'unknown')}")
        
        # Test STT
        print("Testing STT...")
        print(f"STT Status: {health.get('stt', 'unknown')}")
        
        # Test TTS
        print("Testing TTS...")
        print(f"TTS Status: {health.get('tts', 'unknown')}")
        
        # Test recording
        print("\nTesting recording (3 seconds)...")
        try:
            audio_data = self.audio_service.record(duration=3.0)
            if len(audio_data) > 0:
                print(f"Recording successful: {len(audio_data)} samples")
                
                # Test transcription
                print("Testing transcription...")
                text = self.audio_service.transcribe(audio_data)
                print(f"Transcription: '{text}'")
            else:
                print("Recording failed")
        except Exception as e:
            print(f"Recording test failed: {e}")
        
        print("Audio component test completed")
    
    def check_health(self):
        """Check system health."""
        print("\nSystem Health Check...")
        
        # Audio service health
        audio_health = self.audio_service.get_health_status()
        print("Audio Service:")
        for component, status in audio_health.items():
            print(f"  {component}: {status}")
        
        # Orchestrator health
        orchestrator_health = self.orchestrator.get_health_status()
        print("\nOrchestrator:")
        for component, status in orchestrator_health.items():
            print(f"  {component}: {status}")
        
        print("\nHealth check completed")
    
    def show_help(self):
        """Show help information."""
        print("\nAvailable Commands:")
        print("  speak     - Start listening for voice input")
        print("  test      - Test audio components")
        print("  health    - Check system health")
        print("  help      - Show this help message")
        print("  quit      - Exit the application")
        print("\nVoice Commands:")
        print("  Ask about product locations: 'Where is the milk?'")
        print("  Ask about product information: 'What are the ingredients in bread?'")
        print("  During TTS playback, speak to interrupt (barge-in)")
    
    def stop(self):
        """Stop the voice loop."""
        print("Stopping voice loop...")
        self.running = False
        self.audio_service.cleanup()
        print("Goodbye!")

def main():
    """Main entry point."""
    try:
        voice_loop = VoiceLoop()
        voice_loop.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
