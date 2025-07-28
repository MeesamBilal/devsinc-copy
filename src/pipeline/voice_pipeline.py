import asyncio
import logging
import threading
import time
from typing import Optional, Callable
from ..services.stt_service import STTService
from ..services.llm_service import LLMService
from ..services.tts_service import TTSService
from ..audio.microphone import Microphone
from ..audio.speaker import Speaker
from ..config import Config

logger = logging.getLogger(__name__)

class VoicePipeline:
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None):
        # Components
        self.microphone: Optional[Microphone] = None
        self.speaker: Optional[Speaker] = None
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[TTSService] = None
        
        # State
        self.is_running = False
        self.is_listening = False
        self.is_speaking = False
        self.on_status_change = on_status_change
        
        # Processing queues and buffers
        self.audio_queue = asyncio.Queue()
        self.text_queue = asyncio.Queue()
        self.response_buffer = ""
        self.current_utterance = ""
        
        # Tasks
        self.audio_processing_task = None
        self.response_processing_task = None
        
        # Timing for latency monitoring
        self.last_utterance_time = None
        self.response_start_time = None
        
    async def initialize(self):
        """Initialize all pipeline components"""
        try:
            logger.info("Initializing voice pipeline...")
            
            # Initialize services
            self.stt_service = STTService(on_transcript=self._on_transcript)
            self.llm_service = LLMService(on_response_chunk=self._on_llm_chunk)
            self.tts_service = TTSService(on_audio_chunk=self._on_tts_chunk)
            
            # Initialize audio components
            self.microphone = Microphone(on_audio_chunk=self._on_audio_chunk)
            self.speaker = Speaker()
            
            # Start STT connection
            await self.stt_service.start_connection()
            
            logger.info("Voice pipeline initialized successfully")
            self._update_status("initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    def _on_audio_chunk(self, audio_data: bytes):
        """Handle audio chunk from microphone"""
        if self.is_listening and not self.is_speaking:
            # Send audio to STT service asynchronously
            if self.stt_service and self.stt_service.is_connected:
                asyncio.create_task(self.stt_service.send_audio(audio_data))
    
    def _on_transcript(self, transcript: str, is_final: bool):
        """Handle transcript from STT service"""
        if is_final and transcript.strip():
            self.current_utterance = transcript.strip()
            self.last_utterance_time = time.time()
            
            logger.info(f"Final transcript: {self.current_utterance}")
            
            # Stop listening temporarily while processing
            self._set_listening(False)
            
            # Process the utterance
            asyncio.create_task(self._process_utterance(self.current_utterance))
    
    def _on_llm_chunk(self, text_chunk: str):
        """Handle text chunk from LLM"""
        if not self.response_start_time:
            self.response_start_time = time.time()
            if self.last_utterance_time:
                latency = self.response_start_time - self.last_utterance_time
                logger.info(f"Response latency: {latency:.3f}s")
        
        # Add to text queue for TTS processing
        asyncio.create_task(self.text_queue.put(text_chunk))
    
    def _on_tts_chunk(self, audio_chunk: bytes):
        """Handle audio chunk from TTS"""
        if self.speaker and audio_chunk:
            self.speaker.play_audio_chunk(audio_chunk)
    
    async def _process_utterance(self, utterance: str):
        """Process user utterance through LLM and TTS"""
        try:
            self._update_status("processing")
            self.response_start_time = None
            
            # Start speaking state
            self._set_speaking(True)
            
            # Start TTS processing task
            self.response_processing_task = asyncio.create_task(
                self._process_tts_queue()
            )
            
            # Generate LLM response (streaming)
            response_text = ""
            async for chunk in self.llm_service.generate_response(utterance):
                response_text += chunk
                # LLM chunks are automatically sent to TTS via _on_llm_chunk
            
            # Signal end of response
            await self.text_queue.put(None)  # Sentinel value
            
            # Wait for TTS processing to complete
            if self.response_processing_task:
                await self.response_processing_task
            
            logger.info(f"Complete response: {response_text}")
            
            # Resume listening after a short delay
            await asyncio.sleep(0.5)
            self._set_speaking(False)
            self._set_listening(True)
            self._update_status("listening")
            
        except Exception as e:
            logger.error(f"Error processing utterance: {e}")
            self._set_speaking(False)
            self._set_listening(True)
            self._update_status("error")
    
    async def _process_tts_queue(self):
        """Process text queue for TTS synthesis"""
        buffer = ""
        sentence_endings = ['.', '!', '?']
        
        while True:
            try:
                # Get text from queue
                text_chunk = await asyncio.wait_for(self.text_queue.get(), timeout=0.1)
                
                if text_chunk is None:  # End of response
                    # Process any remaining text
                    if buffer.strip():
                        async for audio_chunk in self.tts_service.synthesize_speech(buffer.strip()):
                            pass  # Audio chunks are handled by _on_tts_chunk
                    break
                
                buffer += text_chunk
                
                # Check for complete sentences
                for ending in sentence_endings:
                    if ending in buffer:
                        sentences = buffer.split(ending)
                        for i, sentence in enumerate(sentences[:-1]):
                            if sentence.strip():
                                complete_sentence = sentence.strip() + ending
                                # Synthesize complete sentence
                                async for audio_chunk in self.tts_service.synthesize_speech(complete_sentence):
                                    pass  # Audio chunks are handled by _on_tts_chunk
                        
                        # Keep remaining incomplete sentence
                        buffer = sentences[-1]
                        break
                
                self.text_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in TTS processing: {e}")
                break
    
    def _set_listening(self, listening: bool):
        """Set listening state"""
        self.is_listening = listening
        if listening:
            if self.microphone:
                self.microphone.start_recording()
        else:
            if self.microphone:
                self.microphone.stop_recording()
    
    def _set_speaking(self, speaking: bool):
        """Set speaking state"""
        self.is_speaking = speaking
        if speaking:
            if self.speaker:
                self.speaker.start_playback()
        else:
            if self.speaker:
                # Clear any remaining audio in queue
                self.speaker.clear_queue()
    
    def _update_status(self, status: str):
        """Update pipeline status"""
        if self.on_status_change:
            self.on_status_change(status)
    
    async def start(self):
        """Start the voice pipeline"""
        if self.is_running:
            return
        
        try:
            logger.info("Starting voice pipeline...")
            self.is_running = True
            
            # Start listening
            self._set_listening(True)
            self._update_status("listening")
            
            logger.info("Voice pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the voice pipeline"""
        if not self.is_running:
            return
        
        logger.info("Stopping voice pipeline...")
        self.is_running = False
        
        # Stop listening and speaking
        self._set_listening(False)
        self._set_speaking(False)
        
        # Cancel running tasks
        if self.response_processing_task and not self.response_processing_task.done():
            self.response_processing_task.cancel()
        
        # Stop services
        if self.stt_service:
            await self.stt_service.stop_connection()
        
        # Close audio components
        if self.microphone:
            self.microphone.close()
        if self.speaker:
            self.speaker.close()
        
        self._update_status("stopped")
        logger.info("Voice pipeline stopped")
    
    def get_status(self) -> dict:
        """Get current pipeline status"""
        return {
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking,
            "stt_connected": self.stt_service.is_connected if self.stt_service else False,
            "current_utterance": self.current_utterance,
        }
    
    def clear_conversation(self):
        """Clear conversation history"""
        if self.llm_service:
            self.llm_service.clear_history()
        self.current_utterance = ""
        logger.info("Conversation cleared")