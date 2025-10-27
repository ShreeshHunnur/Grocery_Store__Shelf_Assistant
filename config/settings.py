"""
Configuration settings for the Retail Shelf Assistant.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Audio settings
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_size": 1024,
    "format": "mp3",  # Changed from wav to mp3 for Google TTS
    "language": "en",
    "channels": 1,  # Mono
    "bit_depth": 16,
    "max_recording_duration": 10,  # seconds
    "playback_device": None,  # None = default device
    "recording_device": None,  # None = default device
}

# Database settings
DATABASE_CONFIG = {
    "path": DATA_DIR / "products.db",
    "init_script": BASE_DIR / "scripts" / "init_db.py"
}

# LLM settings
LLM_CONFIG = {
    "base_url": "http://localhost:11434",
    "model_name": "phi3",
    "max_tokens": 150,
    "temperature": 0.3,
    "timeout": 60
}

# Vision / VLM settings (Microsoft GiT configuration)
VLM_CONFIG = {
    "enabled": True,
    "provider": "huggingface",
    "hf_model": "microsoft/git-base-coco",
    "trust_remote_code": False,  # GiT doesn't require trust_remote_code
    "timeout": 30,
    # HTTP fallback settings (disabled when using HuggingFace)
    "base_url": None,
    "api_key": None,
    "predict_path": "/v1/vision/predict"
}

# Classification settings
CLASSIFICATION_CONFIG = {
    "location_keywords": [
        "where", "find", "located", "aisle", "section", "shelf", 
        "near", "next to", "position", "place", "spot"
    ],
    "information_keywords": [
        "ingredients", "nutrition", "calories", "price", "vegan", 
        "gluten-free", "halal", "kosher", "size", "return policy", 
        "warranty", "expiration", "allergens", "dietary"
    ],
    "confidence_threshold": 0.6,
    "disambiguation_threshold": 0.8,
    "location_threshold": 0.3,
    "information_threshold": 0.3,
    "negation_penalty": 0.3,
    "trigram_threshold": 0.6,
    "fuzzy_threshold": 0.7,
    "exact_match_weight": 1.0,
    "synonym_match_weight": 0.9,
    "fuzzy_match_weight": 0.8,
    "trigram_match_weight": 0.7
}

# API settings
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_audio_formats": ["wav", "mp3", "m4a", "flac"]
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": BASE_DIR / "logs" / "app.log"
}

# Performance settings
PERFORMANCE_CONFIG = {
    "max_response_time": 2.5,  # seconds
    "cache_size": 100,
    "batch_size": 1
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary."""
    return {
        "audio": AUDIO_CONFIG,
        "database": DATABASE_CONFIG,
        "llm": LLM_CONFIG,
        "classification": CLASSIFICATION_CONFIG,
        "api": API_CONFIG,
        "logging": LOGGING_CONFIG,
        "performance": PERFORMANCE_CONFIG
    }

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
(BASE_DIR / "logs").mkdir(exist_ok=True)
