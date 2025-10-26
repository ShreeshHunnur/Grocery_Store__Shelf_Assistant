# Retail Shelf Assistant - Architecture

## System Overview

The Retail Shelf Assistant is a voice-enabled system that helps customers find products and get product information in retail environments. The system processes natural language queries and routes them to either location-based database queries or information-based LLM responses.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Input   │    │   Text Input    │    │   Web Client    │
│   (Microphone)  │    │   (Keyboard)    │    │   (Browser)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI HTTP Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   /ask      │  │ /ask-voice  │  │   /health   │            │
│  │  (text)     │  │  (audio)    │  │  (status)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audio I/O Module                            │
│  ┌─────────────┐              ┌─────────────┐                  │
│  │     STT     │              │     TTS     │                  │
│  │  (Whisper)  │              │  (pyttsx3)  │                  │
│  └─────────────┘              └─────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NLU Router                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Query Classification                        │  │
│  │  • Location keywords: "where", "find", "aisle"          │  │
│  │  • Info keywords: "ingredients", "nutrition", "price"  │  │
│  │  • Confidence scoring                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────┐                    ┌─────────┐
    │Location │                    │Information│
    │ Route   │                    │  Route   │
    └────┬────┘                    └────┬────┘
         │                              │
         ▼                              ▼
┌─────────────────┐              ┌─────────────────┐
│   DB Service    │              │   LLM Service   │
│   (SQLite3)     │              │   (Mistral)     │
│                 │              │                 │
│ • Product catalog│              │ • Product info  │
│ • Location data │              │ • Nutrition     │
│ • Search & match│              │ • Ingredients   │
└─────────────────┘              └─────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Response Formatter                          │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │Location Response│              │Information Resp.│          │
│  │• Product matches│              │• LLM answer     │          │
│  │• Aisle/bay/shelf│              │• Confidence    │          │
│  │• Disambiguation│              │• Caveats        │          │
│  └─────────────────┘              └─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audio Output                                 │
│                    (TTS Playback)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Service Boundaries

### 1. Audio I/O Module
- **STT (Speech-to-Text)**: Whisper model for converting audio to text
- **TTS (Text-to-Speech)**: pyttsx3 for converting responses to audio
- **Audio Processing**: Handle various audio formats (WAV, MP3, M4A, FLAC)

### 2. NLU Router
- **Query Classification**: Keyword-based routing with confidence scoring
- **Intent Detection**: Distinguish between location and information queries
- **Query Normalization**: Clean and standardize user input

### 3. DB Service
- **Product Catalog**: SQLite database with 1000+ products
- **Location Data**: Aisle, bay, shelf information
- **Search & Matching**: Fuzzy matching and confidence scoring

### 4. LLM Service
- **Model**: Mistral-7B-Instruct for local inference
- **Product Information**: Nutrition, ingredients, dietary info
- **Response Generation**: Structured, helpful answers

### 5. API Layer
- **FastAPI**: HTTP endpoints and request/response handling
- **Validation**: Pydantic models for data validation
- **Error Handling**: Comprehensive error responses

## Request/Response Flow

### Location Query Flow
1. **Audio Input** → STT → Text
2. **Text** → NLU Router → Location Intent
3. **Location Intent** → DB Service → Product Matches
4. **Product Matches** → Response Formatter → JSON
5. **JSON** → TTS → Audio Output

### Information Query Flow
1. **Audio Input** → STT → Text
2. **Text** → NLU Router → Information Intent
3. **Information Intent** → LLM Service → Generated Answer
4. **Generated Answer** → Response Formatter → JSON
5. **JSON** → TTS → Audio Output

## Data Models

### ProductLocationResponse
```json
{
  "query_type": "location",
  "normalized_product": "string",
  "matches": [
    {
      "product_id": "string",
      "product_name": "string", 
      "brand": "string",
      "category": "string",
      "aisle": "string",
      "bay": "string",
      "shelf": "string",
      "confidence": 0.0
    }
  ],
  "disambiguation_needed": false,
  "notes": "string"
}
```

### ProductInfoResponse
```json
{
  "query_type": "information",
  "normalized_product": "string",
  "answer": "string",
  "caveats": "string",
  "confidence": 0.0
}
```

## Performance Considerations

- **Response Time**: <2.5s median for location queries
- **Caching**: LLM responses cached to reduce inference time
- **Batch Processing**: Single query processing for real-time response
- **Resource Management**: GPU/CPU auto-detection for LLM inference

## Security & Reliability

- **Input Validation**: All inputs validated through Pydantic models
- **Error Handling**: Comprehensive error responses with appropriate HTTP codes
- **Logging**: Structured logging for debugging and monitoring
- **Health Checks**: Component status monitoring via /health endpoint
