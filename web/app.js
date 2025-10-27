/**
 * Retail Shelf Assistant - Web UI JavaScript
 * Handles voice recording, audio upload, and response playback
 */

class VoiceAssistant {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isPlaying = false;
        this.audioContext = null;
        this.currentAudio = null;
        this.sessionId = this.generateSessionId();
        
        // DOM elements
        this.elements = {
            permissionStatus: document.getElementById('permission-status'),
            mainInterface: document.getElementById('main-interface'),
            micButton: document.getElementById('mic-button'),
            recordingIndicator: document.getElementById('recording-indicator'),
            textInput: document.getElementById('text-input'),
            textSubmit: document.getElementById('text-submit'),
            responseArea: document.getElementById('response-area'),
            responseStatus: document.getElementById('response-status'),
            transcribedText: document.getElementById('transcribed-text'),
            responseText: document.getElementById('response-text'),
            audioControls: document.getElementById('audio-controls'),
            playButton: document.getElementById('play-button'),
            audioVisualizer: document.getElementById('audio-visualizer'),
            errorMessage: document.getElementById('error-message'),
            loadingState: document.getElementById('loading-state'),
            exampleButtons: document.querySelectorAll('.example-button')
        };

        // Vision / camera elements (added dynamically in HTML)
        this.elements.cameraToggle = document.getElementById('camera-toggle');
        this.elements.captureButton = document.getElementById('capture-button');
        this.elements.closeCamera = document.getElementById('close-camera');
        this.elements.cameraArea = document.getElementById('camera-area');
        this.elements.cameraVideo = document.getElementById('camera-video');
        this.elements.captureCanvas = document.getElementById('capture-canvas');
        this.elements.visionPreview = document.getElementById('vision-preview');
        
        this.init();
    }
    
    init() {
        console.log('VoiceAssistant initializing...');
        this.setupEventListeners();
        this.checkMicrophoneSupport();
        // Always show the main interface, even if mic support is limited
        this.hidePermissionPrompt();
        console.log('VoiceAssistant initialized successfully');
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        // Microphone button
        this.elements.micButton.addEventListener('click', () => {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        });
        
        // Text input
        this.elements.textSubmit.addEventListener('click', () => {
            this.handleTextQuery();
        });
        
        this.elements.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleTextQuery();
            }
        });
        
        // Play button
        this.elements.playButton.addEventListener('click', () => {
            this.togglePlayback();
        });
        
        // Example buttons
        this.elements.exampleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const query = button.dataset.query;
                this.elements.textInput.value = query;
                this.handleTextQuery();
            });
        });

        // Camera controls
        if (this.elements.cameraToggle) {
            this.elements.cameraToggle.addEventListener('click', () => this.openCamera());
        }
        if (this.elements.captureButton) {
            this.elements.captureButton.addEventListener('click', () => this.captureImage());
        }
        if (this.elements.closeCamera) {
            this.elements.closeCamera.addEventListener('click', () => this.closeCamera());
        }
        
        // Audio context resume on user interaction
        document.addEventListener('click', () => {
            if (this.audioContext && this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
        });
    }
    
    checkMicrophoneSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn('Microphone access is not supported in this browser.');
            return false;
        }
        
        if (!window.MediaRecorder) {
            console.warn('Audio recording is not supported in this browser.');
            return false;
        }
        
        console.log('Microphone support detected');
        return true;
    }
    
    showPermissionPrompt() {
        this.elements.permissionStatus.classList.remove('hidden');
        this.elements.mainInterface.classList.add('hidden');
    }
    
    hidePermissionPrompt() {
        this.elements.permissionStatus.classList.add('hidden');
        this.elements.mainInterface.classList.remove('hidden');
    }
    
    async startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100,  // Higher sample rate for better quality
                    channelCount: 1,    // Mono
                    volume: 1.0         // Full volume
                } 
            });
            
            this.hidePermissionPrompt();
            
            // Stop any current playback
            this.stopPlayback();
            
            // Check supported MIME types - prefer WebM with Opus codec
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/mp4;codecs=aac',
                'audio/mp4',
                'audio/wav'
            ];
            
            let mimeType = '';
            for (const type of mimeTypes) {
                if (MediaRecorder.isTypeSupported(type)) {
                    mimeType = type;
                    break;
                }
            }
            
            if (!mimeType) {
                throw new Error('No supported audio format found');
            }
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
                stream.getTracks().forEach(track => track.stop());
            };
            
            // Start recording
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            
            // Update UI
            this.elements.micButton.classList.add('recording');
            this.elements.micButton.querySelector('.mic-text').textContent = 'Stop Recording';
            this.elements.recordingIndicator.classList.remove('hidden');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            // Show a friendly message instead of blocking the interface
            this.showError('Microphone access denied. You can still use the text input below to ask questions.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.elements.micButton.classList.remove('recording');
            this.elements.micButton.querySelector('.mic-text').textContent = 'Tap to Speak';
            this.elements.recordingIndicator.classList.add('hidden');
            
            // Show loading state
            this.showLoadingState();
        }
    }
    
    async processRecording() {
        try {
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { 
                type: this.audioChunks[0]?.type || 'audio/webm' 
            });
            
            // Upload to server
            await this.uploadAudio(audioBlob);
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.showError('Failed to process audio recording.');
            this.hideLoadingState();
        }
    }
    
    async uploadAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'recording.webm');
            formData.append('session_id', this.sessionId);
            formData.append('return_audio', 'true');
            
            const response = await fetch('/api/v1/ask-voice', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.error || 'Server error');
            }
            
            // Check if response is audio or JSON
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('audio/')) {
                // Handle audio response
                const audioBlob = await response.blob();
                await this.playAudioResponse(audioBlob);
                
                // Also try to get text response for display
                await this.getTextResponse(audioBlob);
            } else {
                // Handle JSON response
                const data = await response.json();
                this.displayResponse(data);
            }
            
        } catch (error) {
            console.error('Error uploading audio:', error);
            this.showError('Failed to upload audio: ' + error.message);
        } finally {
            this.hideLoadingState();
        }
    }
    
    async getTextResponse(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'recording.webm');
            formData.append('session_id', this.sessionId);
            formData.append('return_audio', 'false');
            
            const response = await fetch('/api/v1/ask-voice', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayResponse(data);
            }
        } catch (error) {
            console.error('Error getting text response:', error);
        }
    }
    
    async handleTextQuery() {
        const query = this.elements.textInput.value.trim();
        if (!query) return;
        
        this.showLoadingState();
        
        try {
            const response = await fetch('/api/v1/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.error || 'Server error');
            }
            
            const data = await response.json();
            this.displayResponse({
                transcribed_text: query,
                response: data
            });
            
        } catch (error) {
            console.error('Error processing text query:', error);
            this.showError('Failed to process query: ' + error.message);
        } finally {
            this.hideLoadingState();
        }
    }

    async openCamera() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.showError('Camera not supported in this browser.');
                return;
            }

            const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
            this.cameraStream = stream;
            this.elements.cameraVideo.srcObject = stream;
            this.elements.cameraArea.classList.remove('hidden');
            this.elements.captureButton.classList.remove('hidden');
            this.elements.closeCamera.classList.remove('hidden');
            this.elements.cameraToggle.classList.add('hidden');
        } catch (err) {
            console.error('Error opening camera', err);
            this.showError('Unable to access camera: ' + err.message);
        }
    }

    closeCamera() {
        try {
            if (this.cameraStream) {
                this.cameraStream.getTracks().forEach(t => t.stop());
                this.cameraStream = null;
            }
            this.elements.cameraArea.classList.add('hidden');
            this.elements.captureButton.classList.add('hidden');
            this.elements.closeCamera.classList.add('hidden');
            this.elements.cameraToggle.classList.remove('hidden');
        } catch (err) {
            console.error('Error closing camera', err);
        }
    }

    async captureImage() {
        try {
            const video = this.elements.cameraVideo;
            const canvas = this.elements.captureCanvas;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert to blob (jpeg)
            canvas.toBlob(async (blob) => {
                if (!blob) {
                    this.showError('Failed to capture image');
                    return;
                }

                // Show preview
                const url = URL.createObjectURL(blob);
                this.elements.visionPreview.innerHTML = `<img src="${url}" alt="capture" width="320" />`;

                // Upload to server
                await this.uploadImage(blob);
            }, 'image/jpeg', 0.9);

        } catch (err) {
            console.error('Error capturing image', err);
            this.showError('Error capturing image: ' + err.message);
        }
    }

    async uploadImage(imageBlob) {
        try {
            this.showLoadingState();

            const formData = new FormData();
            formData.append('image_file', imageBlob, 'capture.jpg');
            formData.append('session_id', this.sessionId);

            const response = await fetch('/api/v1/vision', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail?.error || 'Vision API error');
            }

            const data = await response.json();
            // Wrap in display structure similar to text responses
            this.displayResponse({ transcribed_text: 'Image captured', response: data });

        } catch (err) {
            console.error('Error uploading image', err);
            this.showError('Image upload failed: ' + err.message);
        } finally {
            this.hideLoadingState();
        }
    }
    
    displayResponse(data) {
        const { transcribed_text, response } = data;
        
        // Show transcribed text
        if (transcribed_text) {
            this.elements.transcribedText.textContent = transcribed_text;
        }
        
        // Show response
        if (response) {
            if (response.query_type === 'location') {
                this.displayLocationResponse(response);
            } else if (response.query_type === 'information') {
                this.displayInformationResponse(response);
            } else {
                this.elements.responseText.textContent = response.answer || 'No response available';
            }
            
            // Show response area
            this.elements.responseArea.classList.remove('hidden');
            this.elements.responseStatus.textContent = 'Success';
            this.elements.responseStatus.className = 'response-status success';
        }
    }
    
    displayLocationResponse(response) {
        let html = `<strong>Product:</strong> ${response.normalized_product || 'Unknown'}<br><br>`;
        
        if (response.matches && response.matches.length > 0) {
            html += '<strong>Found locations:</strong><br>';
            response.matches.slice(0, 3).forEach((match, index) => {
                html += `${index + 1}. ${match.product_name || 'Unknown'} - `;
                html += `Aisle ${match.aisle || '?'}, Bay ${match.bay || '?'}, Shelf ${match.shelf || '?'} `;
                html += `(confidence: ${(match.confidence || 0).toFixed(2)})<br>`;
            });
        } else {
            html += 'No locations found';
        }
        
        if (response.disambiguation_needed) {
            html += '<br><br><em>Please be more specific about which product you\'re looking for.</em>';
        }
        
        this.elements.responseText.innerHTML = html;
    }
    
    displayInformationResponse(response) {
        let html = `<strong>Product:</strong> ${response.normalized_product || 'Unknown'}<br><br>`;
        html += `<strong>Answer:</strong> ${response.answer || 'No answer available'}<br>`;
        
        if (response.caveats) {
            html += `<br><strong>Caveats:</strong> ${response.caveats}`;
        }
        
        html += `<br><br><strong>Confidence:</strong> ${(response.confidence || 0).toFixed(2)}`;
        
        this.elements.responseText.innerHTML = html;
    }
    
    async playAudioResponse(audioBlob) {
        try {
            // Create audio URL
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create audio element
            const audio = new Audio(audioUrl);
            this.currentAudio = audio;
            
            // Setup audio context for visualization
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Show audio controls
            this.elements.audioControls.classList.remove('hidden');
            this.elements.playButton.classList.remove('playing');
            this.elements.playButton.querySelector('.play-text').textContent = 'Play Response';
            
            // Store audio for playback
            this.currentAudio = audio;
            
            // Clean up URL when audio ends
            audio.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
                this.elements.playButton.classList.remove('playing');
                this.elements.playButton.querySelector('.play-text').textContent = 'Play Response';
                this.isPlaying = false;
            });
            
        } catch (error) {
            console.error('Error playing audio:', error);
            this.showError('Failed to play audio response.');
        }
    }
    
    togglePlayback() {
        if (!this.currentAudio) return;
        
        if (this.isPlaying) {
            this.stopPlayback();
        } else {
            this.startPlayback();
        }
    }
    
    startPlayback() {
        if (this.currentAudio) {
            this.currentAudio.play();
            this.isPlaying = true;
            this.elements.playButton.classList.add('playing');
            this.elements.playButton.querySelector('.play-text').textContent = 'Stop';
        }
    }
    
    stopPlayback() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.isPlaying = false;
            this.elements.playButton.classList.remove('playing');
            this.elements.playButton.querySelector('.play-text').textContent = 'Play Response';
        }
    }
    
    showLoadingState() {
        this.elements.loadingState.classList.remove('hidden');
        this.elements.responseArea.classList.add('hidden');
        this.elements.errorMessage.classList.add('hidden');
    }
    
    hideLoadingState() {
        this.elements.loadingState.classList.add('hidden');
    }
    
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorMessage.classList.remove('hidden');
        this.elements.responseArea.classList.add('hidden');
        this.hideLoadingState();
    }
}

// Initialize the voice assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAssistant();
});
