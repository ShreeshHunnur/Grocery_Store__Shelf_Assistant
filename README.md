# Grocery Store Shelf Assistant

A comprehensive multi-modal retail assistant that helps customers find product locations and get product information using voice, text, and vision inputs. The system combines local LLMs, SQLite product catalog, and advanced AI models for a complete grocery assistance experience.

## 🚀 Features

- **🎤 Voice Interface**: Speech-to-text product queries with audio responses
- **💬 Text Interface**: Fast text-based product search and information
- **👁️ Vision Interface**: Image-based product recognition and location finding
- **📊 Analytics Dashboard**: Real-time query tracking and performance monitoring
- **🖥️ Cross-Platform**: Web browser, Electron desktop app, and API access
- **🔍 Smart Search**: Hybrid search with FTS and vector similarity
- **🤖 Local AI**: Privacy-focused with local LLM inference via Ollama

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.11 or higher (3.12 recommended)
- **RAM**: 2GB available memory
- **Storage**: 3GB free space
- **CPU**: 4 cores (x64 architecture)
- **Network**: 10 Mbps for model downloads

### Recommended Requirements
- **RAM**: 4GB+ (6GB+ with AI models loaded)
- **Storage**: 5GB+ free space
- **CPU**: 8 cores for optimal performance
- **Network**: 50 Mbps for faster setup
- **GPU**: CUDA-compatible GPU (optional, for faster AI inference)

## 🛠️ Installation Guide

### 📥 Step 1: Clone the Repository

```bash
git clone https://github.com/ShreeshHunnur/Grocery_Store__Shelf_Assistant.git
cd Grocery_Store__Shelf_Assistant
```

### 🐍 Step 2: Set Up Python Environment

#### Windows (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### macOS
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install additional macOS dependencies
brew install ffmpeg  # For audio processing
```

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg portaudio19-dev python3-dev

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# Install system dependencies
sudo dnf install -y python3-pip python3-virtualenv ffmpeg portaudio-devel python3-devel

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 🗄️ Step 3: Initialize the Database

Generate the product database with sample data:

#### Windows
```powershell
# Create data directory
New-Item -ItemType Directory -Force -Path .\data

# Generate database with 1000 products
python .\database\seed_data.py --products 1000 --output .\data\products.db
```

#### macOS/Linux
```bash
# Create data directory
mkdir -p ./data

# Generate database with 1000 products
python ./database/seed_data.py --products 1000 --output ./data/products.db
```

### 🤖 Step 4: Set Up AI Models

#### Install Ollama (Required for LLM)

**Windows:**
1. Download Ollama from [ollama.ai](https://ollama.ai/download)
2. Run the installer
3. Open PowerShell and install models:
```powershell
ollama pull mistral
# or
ollama pull phi3
```

**macOS:**
```bash
# Install via Homebrew
brew install ollama

# Start Ollama service
brew services start ollama

# Install models
ollama pull mistral
ollama pull phi3
```

**Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
systemctl start ollama

# Install models
ollama pull mistral
ollama pull phi3
```

#### Install FFmpeg (Required for Voice)

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to system PATH, or install via winget:
```powershell
winget install Gyan.FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# CentOS/RHEL/Fedora
sudo dnf install ffmpeg
```

### 🎵 Step 5: Verify Audio Setup

Check if voice dependencies are properly installed:

```bash
python scripts/check_voice_deps.py
```

This will verify:
- FFmpeg availability
- Speech recognition libraries
- Audio device detection

## 🚀 Running the Application

### 🌐 Method 1: Web Interface (Recommended)

1. **Start the Backend Server:**

#### Windows
```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Start the server
python scripts\start_server.py
# or manually:
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### macOS/Linux
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Start the server
python scripts/start_server.py
# or manually:
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Access the Application:**
   - Open your browser and go to: `http://localhost:8000/ui`
   - For analytics dashboard: `http://localhost:8000/analytics.html`

3. **Verify Health:**
   ```bash
   curl http://localhost:8000/health
   ```

### 🖥️ Method 2: Desktop App (Electron)

1. **Install Node.js Dependencies:**

#### Windows
```powershell
cd electron
npm install
```

#### macOS/Linux
```bash
cd electron
npm install
```

2. **Start the Desktop App:**

#### Windows
```powershell
npm start
```

#### macOS/Linux
```bash
npm start
```

The Electron app will automatically start the Python backend and open the desktop interface.

### 📱 Method 3: API Only

For development or integration purposes:

```bash
# Start only the API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Test API endpoints
curl -X POST "http://localhost:8000/api/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "Where can I find milk?", "session_id": "test123"}'
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration
DATABASE_PATH=./data/products.db

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Audio Configuration
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# Vision Configuration
VISION_MODEL=microsoft/git-base-coco
```

### Advanced Configuration

Edit `config/settings.py` for detailed configuration options:

```python
# LLM settings
LLM_CONFIG = {
    "base_url": "http://localhost:11434",
    "model_name": "mistral",  # or "phi3"
    "max_tokens": 200,
    "temperature": 0.3,
    "timeout": 60
}

# Audio settings
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "max_recording_duration": 10,
}
```

## 🧪 Testing

### Run All Tests
```bash
# Activate virtual environment first
python -m pytest

# Run with coverage
python -m pytest --cov=src tests/
```

### Performance Testing
```bash
# Quick performance test
python scripts/quick_performance_test.py

# Comprehensive performance test
python scripts/performance_test.py --mode all --iterations 5

# Test specific mode
python scripts/performance_test.py --mode voice --iterations 10
```

### API Contract Testing
```bash
python scripts/test_api_contracts.py
```

### Component Testing
```bash
# Test LLM integration
python scripts/test_llm_service.py

# Test voice processing
python scripts/test_voice_io.py

# Test analytics
python scripts/test_analytics.py
```

## 📊 Performance Monitoring

### Real-time Analytics
Access the analytics dashboard at: `http://localhost:8000/analytics.html`

Features:
- Query performance metrics
- Popular product searches
- Success/failure rates
- Response time trends

### Generate Performance Reports
```bash
# Create performance visualizations
python scripts/performance_visualizations.py

# Export analytics data
python scripts/validate_analytics.py
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Voice Processing Fails
```bash
# Check voice dependencies
python scripts/check_voice_deps.py

# Test audio devices
python scripts/test_microphone_level.py
```

#### 2. LLM Not Responding
```bash
# Check Ollama status
ollama list

# Test LLM connection
python scripts/test_ollama_integration.py
```

#### 3. Database Issues
```bash
# Regenerate database
python database/seed_data.py --products 1000 --output ./data/products.db

# Test database queries
python scripts/test_db_queries.py
```

#### 4. Port Already in Use
```bash
# Windows - kill process on port 8000
netstat -ano | findstr 8000
taskkill /PID <process_id> /F

# macOS/Linux - kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Platform-Specific Issues

#### Windows
- **Permission Errors**: Run PowerShell as Administrator
- **Path Issues**: Ensure Python and Git are in system PATH
- **FFmpeg Issues**: Install via winget or add to PATH manually

#### macOS
- **Homebrew Required**: Install Homebrew for easy dependency management
- **Microphone Permissions**: Grant microphone access in System Preferences
- **M1/M2 Macs**: Some dependencies may need Rosetta 2

#### Linux
- **Audio Issues**: Install PulseAudio development headers
- **Permission Errors**: Add user to audio group: `sudo usermod -a -G audio $USER`
- **Display Issues**: For desktop app, ensure X11/Wayland support

## 📁 Project Structure

```
grocery_assistant_project/
├── 📁 config/              # Configuration files
├── 📁 data/                # Database and data files
├── 📁 database/            # Database schema and seed scripts
├── 📁 electron/            # Electron desktop app
├── 📁 logs/                # Application logs
├── 📁 performance_charts/  # Performance visualization outputs
├── 📁 scripts/             # Utility and test scripts
├── 📁 src/                 # Main application source code
│   ├── 📁 api/             # FastAPI application
│   ├── 📁 nlu/             # Natural Language Understanding
│   ├── 📁 services/        # Core business logic services
│   └── 📁 tests/           # Unit tests
├── 📁 web/                 # Web UI assets
├── 📄 requirements.txt     # Python dependencies
└── 📄 README.md           # This file
```

## 🚀 Development

### Setting Up Development Environment

1. **Fork and Clone:**
```bash
git clone https://github.com/YOUR_USERNAME/Grocery_Store__Shelf_Assistant.git
cd Grocery_Store__Shelf_Assistant
```

2. **Install Development Dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

3. **Pre-commit Hooks:**
```bash
pre-commit install
```

### Contributing

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open a Pull Request

## 📚 API Documentation

Once the server is running, access:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

### Key Endpoints

- `GET /health` - System health check
- `POST /api/v1/ask` - Text-based queries
- `POST /api/v1/ask-voice` - Voice-based queries
- `POST /api/v1/vision` - Image-based queries
- `GET /analytics/*` - Analytics dashboard endpoints

## 🔒 Security Notes

- **Local Processing**: All AI models run locally for privacy
- **No External APIs**: Voice and vision processing happens on-device
- **Secure Defaults**: CORS and input validation enabled
- **Data Privacy**: No query data sent to external services

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/ShreeshHunnur/Grocery_Store__Shelf_Assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ShreeshHunnur/Grocery_Store__Shelf_Assistant/discussions)
- **Wiki**: [Project Wiki](https://github.com/ShreeshHunnur/Grocery_Store__Shelf_Assistant/wiki)

---

**Happy Coding! 🛒🤖**
