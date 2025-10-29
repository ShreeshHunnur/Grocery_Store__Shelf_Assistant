/**
 * ShelfSense AI - Premium Grocery Assistant Interface
 * Advanced voice, text, and vision interactions with modern UI
 */

class ShelfSenseAI {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isPlaying = false;
        this.audioContext = null;
        this.currentAudio = null;
        this.sessionId = this.generateSessionId();
        this.cameraStream = null;
        this.theme = localStorage.getItem('theme') || 'light';
        
        // Modern UI elements
        this.elements = {
            // Core interface
            micButton: document.getElementById('mic-button'),
            recordingIndicator: document.getElementById('recording-indicator'),
            textInput: document.getElementById('text-input'),
            textSubmit: document.getElementById('text-submit'),
            clearInput: document.getElementById('clear-input'),
            
            // Camera controls
            cameraToggle: document.getElementById('camera-toggle'),
            captureButton: document.getElementById('capture-button'),
            closeCamera: document.getElementById('close-camera'),
            cameraArea: document.getElementById('camera-area'),
            cameraVideo: document.getElementById('camera-video'),
            captureCanvas: document.getElementById('capture-canvas'),
            visionPreview: document.getElementById('vision-preview'),
            
            // Results display
            resultsSection: document.getElementById('results-section'),
            closeResults: document.getElementById('close-results'),
            transcribedText: document.getElementById('transcribed-text'),
            responseText: document.getElementById('response-text'),
            queryDisplay: document.getElementById('query-display'),
            confidenceScore: document.getElementById('confidence-score'),
            confidenceBadge: document.getElementById('confidence-badge'),
            
            // Location & product info
            locationResults: document.getElementById('location-results'),
            locationGrid: document.getElementById('location-grid'),
            productInfo: document.getElementById('product-info'),
            infoSections: document.getElementById('info-sections'),
            
            // Audio player
            audioPlayer: document.getElementById('audio-player'),
            playButton: document.getElementById('play-button'),
            progressBar: document.getElementById('progress-bar'),
            audioVisualizer: document.getElementById('audio-visualizer'),
            
            // Status and feedback
            aiStatus: document.getElementById('ai-status'),
            voiceStatus: document.getElementById('voice-status'),
            cameraStatus: document.getElementById('camera-status'),
            
            // Loading and errors
            loadingOverlay: document.getElementById('loading-overlay'),
            loadingTitle: document.getElementById('loading-title'),
            loadingSubtitle: document.getElementById('loading-subtitle'),
            progressFill: document.getElementById('progress-fill'),
            errorToast: document.getElementById('error-toast'),
            errorMessage: document.getElementById('error-message'),
            closeError: document.getElementById('close-error'),
            
            // Modal and permissions
            permissionModal: document.getElementById('permission-modal'),
            closeModal: document.getElementById('close-modal'),
            enableMicrophone: document.getElementById('enable-microphone'),
            enableCamera: document.getElementById('enable-camera'),
            
            // Navigation
            themeToggle: document.getElementById('theme-toggle'),
            settingsBtn: document.getElementById('settings-btn'),
            
            // Quick actions
            quickActionBtns: document.querySelectorAll('.quick-action-btn')
        };
        
        this.init();
    }
    
    init() {
        console.log('🚀 ShelfSense AI initializing...');
        this.applyTheme();
        this.setupEventListeners();
        this.checkCapabilities();
        this.updateStatusIndicators();
        console.log('✅ ShelfSense AI ready!');
    }
    
    generateSessionId() {
        return `shelfsense_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    setupEventListeners() {
        // Voice controls
        this.elements.micButton?.addEventListener('click', () => this.toggleRecording());
        
        // Text input
        this.elements.textSubmit?.addEventListener('click', () => this.handleTextQuery());
        this.elements.textInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleTextQuery();
        });
        this.elements.textInput?.addEventListener('input', this.updateClearButton.bind(this));
        this.elements.clearInput?.addEventListener('click', this.clearTextInput.bind(this));
        
        // Camera controls
        this.elements.cameraToggle?.addEventListener('click', () => this.openCamera());
        this.elements.captureButton?.addEventListener('click', () => this.captureImage());
        this.elements.closeCamera?.addEventListener('click', () => this.closeCamera());
        
        // Results controls
        this.elements.closeResults?.addEventListener('click', () => this.hideResults());
        this.elements.playButton?.addEventListener('click', () => this.toggleAudioPlayback());
        
        // Error handling
        this.elements.closeError?.addEventListener('click', () => this.hideError());
        
        // Modal controls
        this.elements.closeModal?.addEventListener('click', () => this.hidePermissionModal());
        this.elements.enableMicrophone?.addEventListener('click', () => this.requestMicrophonePermission());
        this.elements.enableCamera?.addEventListener('click', () => this.requestCameraPermission());
        
        // Theme toggle
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());
        
        // Quick actions
        this.elements.quickActionBtns?.forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.dataset.query;
                if (query) {
                    this.elements.textInput.value = query;
                    this.handleTextQuery();
                }
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Auto-hide error toast
        setTimeout(() => this.hideError(), 10000);
    }
    
    handleKeyboardShortcuts(e) {
        // Space bar for voice (when not in input)
        if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            this.toggleRecording();
        }
        
        // Escape to close modals/results
        if (e.code === 'Escape') {
            this.hideResults();
            this.hidePermissionModal();
            this.hideError();
        }
        
        // Ctrl/Cmd + K for search focus
        if ((e.ctrlKey || e.metaKey) && e.code === 'KeyK') {
            e.preventDefault();
            this.elements.textInput?.focus();
        }
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const icon = this.elements.themeToggle?.querySelector('i');
        if (icon) {
            icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.applyTheme();
    }
    
    async checkCapabilities() {
        // Check microphone
        try {
            const hasAudio = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
            this.updateStatusIndicator('voice', hasAudio, hasAudio ? 'Voice Ready' : 'Voice Unavailable');
        } catch (e) {
            this.updateStatusIndicator('voice', false, 'Voice Unavailable');
        }
        
        // Check camera
        try {
            const hasVideo = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
            this.updateStatusIndicator('camera', hasVideo, hasVideo ? 'Vision Ready' : 'Camera Unavailable');
        } catch (e) {
            this.updateStatusIndicator('camera', false, 'Camera Unavailable');
        }
        
        // Check AI backend
        try {
            const response = await fetch('/health');
            const healthy = response.ok;
            this.updateStatusIndicator('ai', healthy, healthy ? 'AI Ready' : 'AI Offline');
        } catch (e) {
            this.updateStatusIndicator('ai', false, 'AI Offline');
        }
    }
    
    updateStatusIndicator(type, isReady, text) {
        const element = this.elements[`${type}Status`];
        if (!element) return;
        
        const icon = element.querySelector('i');
        const span = element.querySelector('span');
        
        if (span) span.textContent = text;
        
        element.style.color = isReady ? 'var(--success-600)' : 'var(--error-600)';
        
        if (icon) {
            if (type === 'ai') {
                icon.className = isReady ? 'fas fa-brain' : 'fas fa-exclamation-triangle';
            } else if (type === 'voice') {
                icon.className = isReady ? 'fas fa-microphone' : 'fas fa-microphone-slash';
            } else if (type === 'camera') {
                icon.className = isReady ? 'fas fa-camera' : 'fas fa-camera-slash';
            }
        }
    }
    
    updateStatusIndicators() {
        this.checkCapabilities();
    }
    
    updateClearButton() {
        const hasText = this.elements.textInput?.value.length > 0;
        if (this.elements.clearInput) {
            this.elements.clearInput.style.opacity = hasText ? '1' : '0';
        }
    }
    
    clearTextInput() {
        if (this.elements.textInput) {
            this.elements.textInput.value = '';
            this.elements.textInput.focus();
            this.updateClearButton();
        }
    }
    
    showLoading(title = 'Processing...', subtitle = 'Your AI assistant is thinking') {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.remove('hidden');
        }
        if (this.elements.loadingTitle) {
            this.elements.loadingTitle.textContent = title;
        }
        if (this.elements.loadingSubtitle) {
            this.elements.loadingSubtitle.textContent = subtitle;
        }
        
        // Animate progress bar
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = '0%';
            setTimeout(() => {
                this.elements.progressFill.style.width = '100%';
            }, 100);
        }
    }
    
    hideLoading() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.classList.add('hidden');
        }
    }
    
    showError(message, title = 'Something went wrong') {
        if (this.elements.errorToast) {
            this.elements.errorToast.classList.remove('hidden');
        }
        if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => this.hideError(), 5000);
    }
    
    hideError() {
        if (this.elements.errorToast) {
            this.elements.errorToast.classList.add('hidden');
        }
    }
    
    showPermissionModal() {
        if (this.elements.permissionModal) {
            this.elements.permissionModal.classList.remove('hidden');
        }
    }
    
    hidePermissionModal() {
        if (this.elements.permissionModal) {
            this.elements.permissionModal.classList.add('hidden');
        }
    }
    
    async requestMicrophonePermission() {
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            this.updateStatusIndicator('voice', true, 'Voice Ready');
            this.hidePermissionModal();
        } catch (e) {
            this.showError('Microphone permission denied. Please allow access in your browser settings.');
        }
    }
    
    async requestCameraPermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop()); // Stop immediately after permission check
            this.updateStatusIndicator('camera', true, 'Vision Ready');
            this.hidePermissionModal();
        } catch (e) {
            this.showError('Camera permission denied. Please allow access in your browser settings.');
        }
    }
    
    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            this.showLoading('Listening...', 'Speak clearly into your microphone');
            
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100,
                    channelCount: 1
                }
            });
            
            // Determine best audio format
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/mp4;codecs=aac',
                'audio/wav'
            ];
            
            let mimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
            
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
            
            this.mediaRecorder.start(100);
            this.isRecording = true;
            
            // Update UI
            this.elements.micButton?.classList.add('recording');
            const btnText = this.elements.micButton?.querySelector('.voice-btn-text');
            if (btnText) btnText.textContent = 'Release to Send';
            
            this.elements.recordingIndicator?.classList.remove('hidden');
            
            this.hideLoading();
            this.updateStatusIndicator('voice', true, 'Recording...');
            
        } catch (error) {
            console.error('Recording error:', error);
            this.hideLoading();
            this.showError('Unable to access microphone. Please check permissions.');
            this.updateStatusIndicator('voice', false, 'Voice Unavailable');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.elements.micButton?.classList.remove('recording');
            const btnText = this.elements.micButton?.querySelector('.voice-btn-text');
            if (btnText) btnText.textContent = 'Tap to Speak';
            
            this.elements.recordingIndicator?.classList.add('hidden');
            
            this.showLoading('Processing Audio...', 'Converting speech to text');
        }
    }
    
    async processRecording() {
        try {
            const audioBlob = new Blob(this.audioChunks, { 
                type: this.audioChunks[0]?.type || 'audio/webm'
            });
            
            await this.uploadAudio(audioBlob);
            
        } catch (error) {
            console.error('Processing error:', error);
            this.hideLoading();
            this.showError('Failed to process audio recording.');
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
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail?.error || `Server error: ${response.status}`);
            }
            
            // Check response type
            const contentType = response.headers.get('content-type');
            
            if (contentType?.includes('audio/')) {
                const audioBlob = await response.blob();
                await this.setupAudioResponse(audioBlob);
                // Also get text version
                await this.getTextResponseFromAudio(audioBlob);
            } else {
                const data = await response.json();
                this.displayResponse(data);
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.hideLoading();
            this.showError(`Failed to process voice: ${error.message}`);
        }
    }
    
    async getTextResponseFromAudio(audioBlob) {
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
                this.displayResponse(data, true); // true indicates audio response available
            }
        } catch (error) {
            console.error('Text response error:', error);
        }
    }
    
    async handleTextQuery() {
        const query = this.elements.textInput?.value.trim();
        if (!query) return;
        
        this.showLoading('Searching...', 'Finding the best answer for you');
        
        try {
            const response = await fetch('/api/v1/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail?.error || `Server error: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayResponse({
                transcribed_text: query,
                response: data
            });
            
            // Clear input after successful query
            this.clearTextInput();
            
        } catch (error) {
            console.error('Query error:', error);
            this.hideLoading();
            this.showError(`Failed to process query: ${error.message}`);
        }
    }
    
    displayResponse(data, hasAudio = false) {
        this.hideLoading();
        
        const { transcribed_text, response } = data;
        
        // Show query
        if (transcribed_text && this.elements.transcribedText) {
            this.elements.transcribedText.textContent = transcribed_text;
            this.elements.queryDisplay?.classList.remove('hidden');
        }
        
        // Show confidence if available
        if (response?.confidence && this.elements.confidenceScore) {
            const confidence = Math.round(response.confidence * 100);
            this.elements.confidenceScore.textContent = `${confidence}%`;
            
            // Color code confidence
            const badge = this.elements.confidenceBadge;
            if (badge) {
                badge.style.color = confidence >= 80 ? 'var(--success-600)' : 
                                   confidence >= 60 ? 'var(--warning-600)' : 'var(--error-600)';
            }
        }
        
        // Display response based on type
        if (response) {
            if (response.query_type === 'location') {
                this.displayLocationResponse(response);
            } else if (response.query_type === 'information') {
                this.displayInformationResponse(response);
            } else {
                this.displayGenericResponse(response);
            }
        }
        
        // Show audio player if audio response available
        if (hasAudio && this.elements.audioPlayer) {
            this.elements.audioPlayer.classList.remove('hidden');
        }
        
        // Show results section
        if (this.elements.resultsSection) {
            this.elements.resultsSection.classList.remove('hidden');
            this.elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    displayLocationResponse(response) {
        this.elements.locationResults?.classList.remove('hidden');
        this.elements.productInfo?.classList.add('hidden');
        
        if (!this.elements.locationGrid) return;
        
        const { matches, normalized_product, disambiguation_needed } = response;
        
        let html = '';
        
        if (matches && matches.length > 0) {
            matches.slice(0, 5).forEach((match, index) => {
                const confidenceColor = match.confidence >= 0.8 ? 'var(--success-500)' : 
                                      match.confidence >= 0.6 ? 'var(--warning-500)' : 'var(--error-500)';
                
                html += `
                    <div class="location-item">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-2);">
                            <h4 style="color: var(--neutral-900); font-weight: var(--font-weight-semibold);">
                                ${match.product_name || 'Unknown Product'}
                            </h4>
                            <span style="background: ${confidenceColor}; color: white; padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold);">
                                ${Math.round((match.confidence || 0) * 100)}%
                            </span>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: var(--space-2); margin-bottom: var(--space-2);">
                            <div>
                                <span style="font-size: var(--font-size-xs); color: var(--neutral-500); text-transform: uppercase; font-weight: var(--font-weight-semibold);">Aisle</span>
                                <div style="font-weight: var(--font-weight-semibold); color: var(--primary-600);">${match.aisle || '?'}</div>
                            </div>
                            <div>
                                <span style="font-size: var(--font-size-xs); color: var(--neutral-500); text-transform: uppercase; font-weight: var(--font-weight-semibold);">Bay</span>
                                <div style="font-weight: var(--font-weight-semibold); color: var(--primary-600);">${match.bay || '?'}</div>
                            </div>
                            <div>
                                <span style="font-size: var(--font-size-xs); color: var(--neutral-500); text-transform: uppercase; font-weight: var(--font-weight-semibold);">Shelf</span>
                                <div style="font-weight: var(--font-weight-semibold); color: var(--primary-600);">${match.shelf || '?'}</div>
                            </div>
                        </div>
                        ${match.brand ? `<p style="color: var(--neutral-600); font-size: var(--font-size-sm);"><strong>Brand:</strong> ${match.brand}</p>` : ''}
                        ${match.category ? `<p style="color: var(--neutral-600); font-size: var(--font-size-sm);"><strong>Category:</strong> ${match.category}</p>` : ''}
                    </div>
                `;
            });
        } else {
            html = `
                <div class="location-item" style="text-align: center; padding: var(--space-8);">
                    <i class="fas fa-search" style="font-size: var(--font-size-3xl); color: var(--neutral-400); margin-bottom: var(--space-4);"></i>
                    <h4 style="color: var(--neutral-700); margin-bottom: var(--space-2);">No locations found</h4>
                    <p style="color: var(--neutral-500);">We couldn't find "${normalized_product || 'that product'}" in our store.</p>
                </div>
            `;
        }
        
        if (disambiguation_needed) {
            html += `
                <div style="background: var(--warning-50); border: 1px solid var(--warning-200); border-radius: var(--radius-lg); padding: var(--space-4); margin-top: var(--space-4);">
                    <div style="display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2);">
                        <i class="fas fa-info-circle" style="color: var(--warning-600);"></i>
                        <strong style="color: var(--warning-800);">Need more details</strong>
                    </div>
                    <p style="color: var(--warning-700); font-size: var(--font-size-sm);">Please be more specific about which product you're looking for.</p>
                </div>
            `;
        }
        
        this.elements.locationGrid.innerHTML = html;
    }
    
    displayInformationResponse(response) {
        this.elements.productInfo?.classList.remove('hidden');
        this.elements.locationResults?.classList.add('hidden');
        
        if (!this.elements.infoSections) return;
        
        const { answer, caveats, normalized_product } = response;
        
        let html = `
            <div class="info-section">
                <h4 style="color: var(--neutral-900); margin-bottom: var(--space-3); display: flex; align-items: center; gap: var(--space-2);">
                    <i class="fas fa-info-circle" style="color: var(--primary-500);"></i>
                    Product Information
                </h4>
                <div style="line-height: 1.7; color: var(--neutral-800);">
                    ${this.formatResponseText(answer || 'No information available')}
                </div>
            </div>
        `;
        
        if (caveats) {
            html += `
                <div style="background: var(--warning-50); border-left: 4px solid var(--warning-500); border-radius: var(--radius-lg); padding: var(--space-4);">
                    <h5 style="color: var(--warning-800); margin-bottom: var(--space-2); display: flex; align-items: center; gap: var(--space-2);">
                        <i class="fas fa-exclamation-triangle" style="color: var(--warning-600);"></i>
                        Important Notes
                    </h5>
                    <p style="color: var(--warning-700); font-size: var(--font-size-sm);">${caveats}</p>
                </div>
            `;
        }
        
        this.elements.infoSections.innerHTML = html;
    }
    
    displayGenericResponse(response) {
        if (this.elements.responseText) {
            this.elements.responseText.innerHTML = this.formatResponseText(
                response.answer || response.message || 'Response received'
            );
        }
    }
    
    formatResponseText(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/, '<p>$1</p>');
    }
    
    hideResults() {
        if (this.elements.resultsSection) {
            this.elements.resultsSection.classList.add('hidden');
        }
        
        // Stop any playing audio
        this.stopAudioPlayback();
    }
    
    async setupAudioResponse(audioBlob) {
        try {
            const audioUrl = URL.createObjectURL(audioBlob);
            this.currentAudio = new Audio(audioUrl);
            
            this.currentAudio.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
                this.updatePlayButton(false);
            });
            
            this.currentAudio.addEventListener('timeupdate', () => {
                this.updateAudioProgress();
            });
            
            this.currentAudio.addEventListener('loadedmetadata', () => {
                this.updateAudioDuration();
            });
            
        } catch (error) {
            console.error('Audio setup error:', error);
            this.showError('Failed to setup audio playback.');
        }
    }
    
    toggleAudioPlayback() {
        if (!this.currentAudio) return;
        
        if (this.isPlaying) {
            this.stopAudioPlayback();
        } else {
            this.startAudioPlayback();
        }
    }
    
    startAudioPlayback() {
        if (this.currentAudio) {
            this.currentAudio.play();
            this.isPlaying = true;
            this.updatePlayButton(true);
            this.startAudioVisualizer();
        }
    }
    
    stopAudioPlayback() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.isPlaying = false;
            this.updatePlayButton(false);
            this.stopAudioVisualizer();
        }
    }
    
    updatePlayButton(playing) {
        const btn = this.elements.playButton;
        if (!btn) return;
        
        const icon = btn.querySelector('i');
        if (icon) {
            icon.className = playing ? 'fas fa-pause' : 'fas fa-play';
        }
        
        btn.classList.toggle('playing', playing);
    }
    
    updateAudioProgress() {
        if (!this.currentAudio || !this.elements.progressBar) return;
        
        const progress = (this.currentAudio.currentTime / this.currentAudio.duration) * 100;
        this.elements.progressBar.style.width = `${progress}%`;
    }
    
    updateAudioDuration() {
        if (!this.currentAudio) return;
        
        const duration = this.currentAudio.duration;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        
        const durationElement = this.elements.audioPlayer?.querySelector('.audio-duration');
        if (durationElement) {
            durationElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    startAudioVisualizer() {
        const visualizer = this.elements.audioVisualizer;
        if (visualizer) {
            visualizer.classList.add('playing');
        }
    }
    
    stopAudioVisualizer() {
        const visualizer = this.elements.audioVisualizer;
        if (visualizer) {
            visualizer.classList.remove('playing');
        }
    }
    
    // Camera methods
    async openCamera() {
        try {
            this.showLoading('Opening Camera...', 'Preparing vision scanner');
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            this.cameraStream = stream;
            
            if (this.elements.cameraVideo) {
                this.elements.cameraVideo.srcObject = stream;
            }
            
            // Update UI
            this.elements.cameraArea?.classList.remove('hidden');
            this.elements.captureButton?.classList.remove('hidden');
            this.elements.closeCamera?.classList.remove('hidden');
            this.elements.cameraToggle?.classList.add('hidden');
            
            this.hideLoading();
            this.updateStatusIndicator('camera', true, 'Camera Active');
            
        } catch (error) {
            console.error('Camera error:', error);
            this.hideLoading();
            this.showError('Unable to access camera. Please check permissions.');
            this.updateStatusIndicator('camera', false, 'Camera Unavailable');
        }
    }
    
    closeCamera() {
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(track => track.stop());
            this.cameraStream = null;
        }
        
        // Update UI
        this.elements.cameraArea?.classList.add('hidden');
        this.elements.captureButton?.classList.add('hidden');
        this.elements.closeCamera?.classList.add('hidden');
        this.elements.cameraToggle?.classList.remove('hidden');
        
        if (this.elements.visionPreview) {
            this.elements.visionPreview.innerHTML = '';
        }
        
        this.updateStatusIndicator('camera', true, 'Vision Ready');
    }
    
    async captureImage() {
        try {
            if (!this.elements.cameraVideo || !this.elements.captureCanvas) return;
            
            this.showLoading('Analyzing Image...', 'AI is examining the product');
            
            const video = this.elements.cameraVideo;
            const canvas = this.elements.captureCanvas;
            const ctx = canvas.getContext('2d');
            
            // Set canvas size to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw current video frame
            ctx.drawImage(video, 0, 0);
            
            // Convert to blob
            canvas.toBlob(async (blob) => {
                if (!blob) {
                    this.hideLoading();
                    this.showError('Failed to capture image');
                    return;
                }
                
                // Show preview
                const url = URL.createObjectURL(blob);
                if (this.elements.visionPreview) {
                    this.elements.visionPreview.innerHTML = `
                        <div style="margin-top: var(--space-4); text-align: center;">
                            <img src="${url}" alt="Captured image" style="max-width: 100%; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);" />
                            <p style="margin-top: var(--space-2); color: var(--neutral-600); font-size: var(--font-size-sm);">Image captured - analyzing...</p>
                        </div>
                    `;
                }
                
                // Upload for analysis
                await this.uploadImage(blob);
                
                // Cleanup
                setTimeout(() => URL.revokeObjectURL(url), 60000);
                
            }, 'image/jpeg', 0.9);
            
        } catch (error) {
            console.error('Capture error:', error);
            this.hideLoading();
            this.showError(`Capture failed: ${error.message}`);
        }
    }
    
    async uploadImage(imageBlob) {
        try {
            const formData = new FormData();
            formData.append('image_file', imageBlob, 'capture.jpg');
            formData.append('session_id', this.sessionId);
            
            const response = await fetch('/api/v1/vision', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail?.error || `Vision API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Display results
            this.displayResponse({
                transcribed_text: 'Image captured and analyzed',
                response: data
            });
            
        } catch (error) {
            console.error('Upload error:', error);
            this.hideLoading();
            this.showError(`Image analysis failed: ${error.message}`);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ShelfSenseAI();
});

// Legacy compatibility for existing elements
window.VoiceAssistant = ShelfSenseAI;
