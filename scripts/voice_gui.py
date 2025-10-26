#!/usr/bin/env python3
"""
Simple GUI for voice I/O testing.
"""
import sys
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from src.services.audio_io import AudioIOService
from src.api.orchestrator import BackendOrchestrator

class VoiceGUI:
    """Simple GUI for voice I/O testing."""
    
    def __init__(self):
        """Initialize the GUI."""
        if not GUI_AVAILABLE:
            print("GUI not available. Please install tkinter.")
            sys.exit(1)
        
        self.root = tk.Tk()
        self.root.title("Retail Shelf Assistant - Voice I/O")
        self.root.geometry("600x500")
        
        # Initialize services
        self.audio_service = AudioIOService()
        self.orchestrator = BackendOrchestrator()
        self.session_id = f"gui_session_{int(time.time())}"
        
        # State
        self.is_listening = False
        self.is_processing = False
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Retail Shelf Assistant", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.listen_button = ttk.Button(button_frame, text="Start Listening", 
                                       command=self.toggle_listening)
        self.listen_button.grid(row=0, column=0, padx=(0, 10))
        
        self.test_button = ttk.Button(button_frame, text="Test Audio", 
                                    command=self.test_audio)
        self.test_button.grid(row=0, column=1, padx=(0, 10))
        
        self.health_button = ttk.Button(button_frame, text="Check Health", 
                                       command=self.check_health)
        self.health_button.grid(row=0, column=2)
        
        # Input/Output frame
        io_frame = ttk.LabelFrame(main_frame, text="Input/Output", padding="5")
        io_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Input text
        ttk.Label(io_frame, text="Transcribed Text:").grid(row=0, column=0, sticky=tk.W)
        self.input_text = scrolledtext.ScrolledText(io_frame, height=3, width=60)
        self.input_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Output text
        ttk.Label(io_frame, text="Response:").grid(row=2, column=0, sticky=tk.W)
        self.output_text = scrolledtext.ScrolledText(io_frame, height=6, width=60)
        self.output_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        io_frame.columnconfigure(0, weight=1)
        io_frame.rowconfigure(1, weight=1)
        io_frame.rowconfigure(3, weight=1)
        
    def toggle_listening(self):
        """Toggle listening state."""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start listening for voice input."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Already processing a request")
            return
        
        self.is_listening = True
        self.listen_button.config(text="Stop Listening")
        self.status_label.config(text="Listening... Speak now")
        self.progress.start()
        
        # Start listening in separate thread
        thread = threading.Thread(target=self.listen_and_process)
        thread.daemon = True
        thread.start()
    
    def stop_listening(self):
        """Stop listening."""
        self.is_listening = False
        self.listen_button.config(text="Start Listening")
        self.status_label.config(text="Ready")
        self.progress.stop()
    
    def listen_and_process(self):
        """Listen and process voice input."""
        try:
            # Record audio
            audio_data = self.audio_service.record()
            
            if len(audio_data) == 0:
                self.root.after(0, lambda: self.status_label.config(text="No audio recorded"))
                self.root.after(0, self.stop_listening)
                return
            
            # Transcribe
            self.root.after(0, lambda: self.status_label.config(text="Transcribing..."))
            text = self.audio_service.transcribe(audio_data)
            
            if not text.strip():
                self.root.after(0, lambda: self.status_label.config(text="No speech detected"))
                self.root.after(0, self.stop_listening)
                return
            
            # Update input text
            self.root.after(0, lambda: self.input_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.input_text.insert(1.0, text))
            
            # Process query
            self.root.after(0, lambda: self.status_label.config(text="Processing query..."))
            response = self.orchestrator.process_text_query(text, self.session_id)
            
            # Update output text
            output_text = self.format_response(response)
            self.root.after(0, lambda: self.output_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.output_text.insert(1.0, output_text))
            
            # Synthesize and play response
            if "answer" in response:
                answer_text = response["answer"]
                self.root.after(0, lambda: self.status_label.config(text="Speaking response..."))
                
                audio_response = self.audio_service.synthesize(answer_text)
                if len(audio_response) > 0:
                    self.audio_service.play(audio_response)
            
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            self.root.after(0, self.stop_listening)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Voice processing error: {e}"))
            self.root.after(0, lambda: self.status_label.config(text="Error occurred"))
            self.root.after(0, self.stop_listening)
    
    def format_response(self, response):
        """Format response for display."""
        if "error" in response:
            return f"Error: {response['error']}"
        
        output = []
        
        if response.get("query_type") == "location":
            output.append("Query Type: Location")
            output.append(f"Product: {response.get('normalized_product', 'Unknown')}")
            
            matches = response.get("matches", [])
            if matches:
                output.append("\nFound locations:")
                for i, match in enumerate(matches[:3], 1):
                    output.append(f"  {i}. {match.get('product_name', 'Unknown')} - "
                                f"Aisle {match.get('aisle', '?')}, "
                                f"Bay {match.get('bay', '?')}, "
                                f"Shelf {match.get('shelf', '?')} "
                                f"(confidence: {match.get('confidence', 0):.2f})")
            else:
                output.append("No locations found")
                
            if response.get("disambiguation_needed"):
                output.append("\nDisambiguation needed - please be more specific")
                
        elif response.get("query_type") == "information":
            output.append("Query Type: Information")
            output.append(f"Product: {response.get('normalized_product', 'Unknown')}")
            output.append(f"Answer: {response.get('answer', 'No answer available')}")
            
            caveats = response.get("caveats")
            if caveats:
                output.append(f"Caveats: {caveats}")
            
            confidence = response.get("confidence", 0)
            output.append(f"Confidence: {confidence:.2f}")
        
        return "\n".join(output)
    
    def test_audio(self):
        """Test audio components."""
        def test_thread():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Testing audio..."))
                
                health = self.audio_service.get_health_status()
                
                # Test recording
                audio_data = self.audio_service.record(duration=2.0)
                
                if len(audio_data) > 0:
                    text = self.audio_service.transcribe(audio_data)
                    result = f"Audio test successful!\nRecording: {len(audio_data)} samples\nTranscription: '{text}'\n\nHealth Status:\n"
                    for component, status in health.items():
                        result += f"  {component}: {status}\n"
                else:
                    result = "Audio test failed - no audio recorded"
                
                self.root.after(0, lambda: self.output_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.output_text.insert(1.0, result))
                self.root.after(0, lambda: self.status_label.config(text="Audio test completed"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Audio test failed: {e}"))
                self.root.after(0, lambda: self.status_label.config(text="Audio test failed"))
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def check_health(self):
        """Check system health."""
        def health_thread():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Checking health..."))
                
                # Audio service health
                audio_health = self.audio_service.get_health_status()
                
                # Orchestrator health
                orchestrator_health = self.orchestrator.get_health_status()
                
                result = "System Health Check:\n\n"
                result += "Audio Service:\n"
                for component, status in audio_health.items():
                    result += f"  {component}: {status}\n"
                
                result += "\nOrchestrator:\n"
                for component, status in orchestrator_health.items():
                    result += f"  {component}: {status}\n"
                
                self.root.after(0, lambda: self.output_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.output_text.insert(1.0, result))
                self.root.after(0, lambda: self.status_label.config(text="Health check completed"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Health check failed: {e}"))
                self.root.after(0, lambda: self.status_label.config(text="Health check failed"))
        
        thread = threading.Thread(target=health_thread)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Run the GUI."""
        try:
            self.root.mainloop()
        finally:
            self.audio_service.cleanup()

def main():
    """Main entry point."""
    if not GUI_AVAILABLE:
        print("GUI not available. Please install tkinter.")
        print("You can use the CLI version instead: python scripts/voice_loop.py")
        sys.exit(1)
    
    try:
        app = VoiceGUI()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
