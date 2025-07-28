import asyncio
import json
import logging
import websockets
from typing import Optional, Callable, AsyncGenerator
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from ..config import Config

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, on_transcript: Optional[Callable[[str, bool], None]] = None):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.connection = None
        self.is_connected = False
        self.on_transcript = on_transcript
        self._transcript_buffer = ""
        
    async def start_connection(self):
        """Start the STT connection"""
        try:
            options = LiveOptions(
                model=Config.STT_SETTINGS["model"],
                language=Config.STT_SETTINGS["language"],
                smart_format=Config.STT_SETTINGS["smart_format"],
                interim_results=Config.STT_SETTINGS["interim_results"],
                vad_events=Config.STT_SETTINGS["vad_events"],
                endpointing=Config.STT_SETTINGS["endpointing"],
                utterance_end_ms=Config.STT_SETTINGS["utterance_end_ms"],
            )
            
            self.connection = self.client.listen.asyncwebsocket.v("1")
            
            # Set up event handlers
            self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start the connection
            if await self.connection.start(options):
                self.is_connected = True
                logger.info("STT connection established")
                return True
            else:
                logger.error("Failed to start STT connection")
                return False
                
        except Exception as e:
            logger.error(f"STT connection error: {e}")
            return False
    
    async def _on_open(self, connection, **kwargs):
        """Handle connection open"""
        logger.info("STT connection opened")
    
    async def _on_transcript(self, connection, result, **kwargs):
        """Handle transcript results"""
        try:
            sentence = result.channel.alternatives[0].transcript
            
            if len(sentence) == 0:
                return
            
            is_final = result.is_final
            
            if is_final:
                # Final transcript
                self._transcript_buffer += sentence + " "
                if self.on_transcript:
                    self.on_transcript(sentence, True)
                logger.debug(f"Final transcript: {sentence}")
            else:
                # Interim transcript
                if self.on_transcript:
                    self.on_transcript(sentence, False)
                logger.debug(f"Interim transcript: {sentence}")
                
        except Exception as e:
            logger.error(f"Transcript processing error: {e}")
    
    async def _on_utterance_end(self, connection, **kwargs):
        """Handle utterance end"""
        if self._transcript_buffer.strip():
            complete_utterance = self._transcript_buffer.strip()
            logger.info(f"Complete utterance: {complete_utterance}")
            
            # Trigger callback for complete utterance
            if self.on_transcript:
                self.on_transcript(complete_utterance, True)
            
            # Clear buffer
            self._transcript_buffer = ""
    
    async def _on_error(self, connection, error, **kwargs):
        """Handle connection errors"""
        logger.error(f"STT error: {error}")
    
    async def _on_close(self, connection, **kwargs):
        """Handle connection close"""
        logger.info("STT connection closed")
        self.is_connected = False
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to STT service"""
        if self.is_connected and self.connection:
            try:
                self.connection.send(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to STT: {e}")
    
    async def stop_connection(self):
        """Stop the STT connection"""
        if self.connection:
            try:
                await self.connection.finish()
                self.is_connected = False
                logger.info("STT connection stopped")
            except Exception as e:
                logger.error(f"Error stopping STT connection: {e}")
    
    def get_buffered_transcript(self) -> str:
        """Get the current buffered transcript"""
        return self._transcript_buffer.strip()
    
    def clear_transcript_buffer(self):
        """Clear the transcript buffer"""
        self._transcript_buffer = ""