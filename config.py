import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Audio settings
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = 8192
    AUDIO_FORMAT = "linear16"
    
    # Deepgram STT settings
    STT_MODEL = "nova-2"
    STT_LANGUAGE = "en-US"
    STT_PUNCTUATE = True
    STT_SMART_FORMAT = True
    STT_INTERIM_RESULTS = True
    
    # Deepgram TTS settings
    TTS_MODEL = "aura-asteria-en"  # Fast, natural voice
    TTS_ENCODING = "linear16"
    TTS_SAMPLE_RATE = 24000
    
    # OpenAI settings
    LLM_MODEL = "gpt-3.5-turbo"  # Fast model for low latency
    LLM_MAX_TOKENS = 150
    LLM_TEMPERATURE = 0.7
    
    # Pipeline settings
    SILENCE_THRESHOLD = 0.01
    SILENCE_DURATION = 1.0  # seconds of silence before processing
    MAX_RECORDING_TIME = 30  # maximum recording time in seconds
    
    # System prompt for the customer support agent
    SYSTEM_PROMPT = """You are a helpful customer support agent. You should:
    - Be concise and direct in your responses
    - Speak in a natural, conversational tone
    - Keep responses under 2-3 sentences when possible
    - Be empathetic and professional
    - Ask clarifying questions if needed
    - Provide solutions quickly
    
    Remember: You are speaking, not writing, so use natural speech patterns."""