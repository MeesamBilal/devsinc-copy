import asyncio
import logging
from typing import Optional, Callable, AsyncGenerator
from deepgram import DeepgramClient, SpeakOptions
from ..config import Config

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, on_audio_chunk: Optional[Callable[[bytes], None]] = None):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.on_audio_chunk = on_audio_chunk
        
    async def synthesize_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        """Convert text to speech with streaming"""
        try:
            if not text.strip():
                return
            
            # Configure TTS options
            options = SpeakOptions(
                model=Config.TTS_SETTINGS["model"],
                encoding=Config.TTS_SETTINGS["encoding"],
                sample_rate=Config.TTS_SETTINGS["sample_rate"],
            )
            
            # Generate speech
            response = await self.client.speak.asyncrest.v("1").stream_raw(
                {"text": text},
                options
            )
            
            # Stream audio chunks
            async for chunk in response:
                if chunk:
                    if self.on_audio_chunk:
                        self.on_audio_chunk(chunk)
                    yield chunk
                    
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    async def synthesize_speech_complete(self, text: str) -> bytes:
        """Convert text to speech (complete audio)"""
        try:
            if not text.strip():
                return b""
            
            # Configure TTS options
            options = SpeakOptions(
                model=Config.TTS_SETTINGS["model"],
                encoding=Config.TTS_SETTINGS["encoding"],
                sample_rate=Config.TTS_SETTINGS["sample_rate"],
            )
            
            # Generate speech
            response = await self.client.speak.asyncrest.v("1").save(
                "temp_audio.wav",
                {"text": text},
                options
            )
            
            # Read the generated audio file
            with open("temp_audio.wav", "rb") as f:
                audio_data = f.read()
            
            # Clean up temp file
            import os
            os.remove("temp_audio.wav")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""
    
    async def synthesize_streaming_text(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """Convert streaming text to streaming audio"""
        buffer = ""
        sentence_endings = ['.', '!', '?', '\n']
        
        async for text_chunk in text_stream:
            buffer += text_chunk
            
            # Check if we have a complete sentence
            for ending in sentence_endings:
                if ending in buffer:
                    sentences = buffer.split(ending)
                    for i, sentence in enumerate(sentences[:-1]):
                        if sentence.strip():
                            complete_sentence = sentence.strip() + ending
                            
                            # Synthesize the complete sentence
                            async for audio_chunk in self.synthesize_speech(complete_sentence):
                                yield audio_chunk
                    
                    # Keep the remaining incomplete sentence
                    buffer = sentences[-1]
                    break
        
        # Process any remaining text in buffer
        if buffer.strip():
            async for audio_chunk in self.synthesize_speech(buffer.strip()):
                yield audio_chunk
    
    async def synthesize_text_queue(self, text_queue: asyncio.Queue) -> AsyncGenerator[bytes, None]:
        """Convert text from queue to streaming audio"""
        while True:
            try:
                # Get text from queue with timeout
                text = await asyncio.wait_for(text_queue.get(), timeout=0.1)
                
                if text is None:  # Sentinel value to stop
                    break
                
                # Synthesize the text
                async for audio_chunk in self.synthesize_speech(text):
                    yield audio_chunk
                
                text_queue.task_done()
                
            except asyncio.TimeoutError:
                # No text available, continue
                continue
            except Exception as e:
                logger.error(f"Error processing text queue: {e}")
                break