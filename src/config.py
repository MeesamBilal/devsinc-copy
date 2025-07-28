import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Audio Configuration
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))
    CHANNELS = int(os.getenv("CHANNELS", 1))
    FORMAT = "linear16"
    
    # Model Configuration
    DEEPGRAM_MODEL = "nova-2"
    DEEPGRAM_TTS_MODEL = "aura-asteria-en"
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    # Performance Settings
    RESPONSE_TIMEOUT = float(os.getenv("RESPONSE_TIMEOUT", 1.0))
    VAD_THRESHOLD = 0.5
    SILENCE_TIMEOUT = 1.5
    
    # Deepgram STT Settings
    STT_SETTINGS = {
        "model": DEEPGRAM_MODEL,
        "language": "en-US",
        "smart_format": True,
        "interim_results": True,
        "vad_events": True,
        "endpointing": 300,
        "utterance_end_ms": 1000,
    }
    
    # Deepgram TTS Settings
    TTS_SETTINGS = {
        "model": DEEPGRAM_TTS_MODEL,
        "encoding": "linear16",
        "sample_rate": SAMPLE_RATE,
    }
    
    # OpenAI Settings
    OPENAI_SETTINGS = {
        "model": OPENAI_MODEL,
        "temperature": 0.7,
        "max_tokens": 150,
        "stream": True,
    }