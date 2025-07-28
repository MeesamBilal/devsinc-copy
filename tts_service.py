import asyncio
import aiohttp
import io
from deepgram import DeepgramClient
from config import Config
import queue
import threading

class TTSService:
    def __init__(self):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.audio_queue = queue.Queue()
        
    async def synthesize_speech(self, text):
        """Convert text to speech using Deepgram TTS"""
        try:
            print(f"Synthesizing speech for: {text}")
            
            # Configure TTS options for low latency
            options = {
                "model": Config.TTS_MODEL,
                "encoding": Config.TTS_ENCODING,
                "sample_rate": Config.TTS_SAMPLE_RATE,
            }
            
            # Generate speech
            response = await self.client.speak.asyncrest.v("1").stream(
                {"text": text}, 
                options
            )
            
            # Get the audio data
            audio_data = b""
            async for chunk in response.iter_content():
                if chunk:
                    audio_data += chunk
                    
            print(f"Generated {len(audio_data)} bytes of audio")
            return audio_data
            
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return None
            
    async def synthesize_speech_streaming(self, text, callback=None):
        """Convert text to speech with streaming callback for real-time playback"""
        try:
            print(f"Synthesizing streaming speech for: {text}")
            
            # Configure TTS options
            options = {
                "model": Config.TTS_MODEL,
                "encoding": Config.TTS_ENCODING,
                "sample_rate": Config.TTS_SAMPLE_RATE,
            }
            
            # Generate speech
            response = await self.client.speak.asyncrest.v("1").stream(
                {"text": text}, 
                options
            )
            
            # Stream audio data
            audio_chunks = []
            async for chunk in response.iter_content():
                if chunk:
                    audio_chunks.append(chunk)
                    if callback:
                        callback(chunk)
                        
            # Return complete audio data
            complete_audio = b"".join(audio_chunks)
            print(f"Generated {len(complete_audio)} bytes of streaming audio")
            return complete_audio
            
        except Exception as e:
            print(f"Error synthesizing streaming speech: {e}")
            if callback:
                callback(None)  # Signal error to callback
            return None
            
    async def synthesize_speech_fast(self, text):
        """Fast synthesis optimized for minimum latency"""
        try:
            # Use the fastest available model and settings
            options = {
                "model": "aura-luna-en",  # Fast model
                "encoding": Config.TTS_ENCODING,
                "sample_rate": 16000,  # Lower sample rate for speed
            }
            
            # Keep text short for faster processing
            if len(text) > 200:
                text = text[:200] + "..."
                
            response = await self.client.speak.asyncrest.v("1").stream(
                {"text": text}, 
                options
            )
            
            audio_data = b""
            async for chunk in response.iter_content():
                if chunk:
                    audio_data += chunk
                    
            return audio_data
            
        except Exception as e:
            print(f"Error in fast synthesis: {e}")
            return None
            
    def add_to_queue(self, audio_data):
        """Add audio data to the playback queue"""
        self.audio_queue.put(audio_data)
        
    def get_from_queue(self):
        """Get audio data from the playback queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
            
    def clear_queue(self):
        """Clear the audio queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break