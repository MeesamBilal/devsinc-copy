import asyncio
import json
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from config import Config
import threading
import queue

class STTService:
    def __init__(self, on_transcript_callback=None):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.connection = None
        self.on_transcript_callback = on_transcript_callback
        self.transcript_queue = queue.Queue()
        self.is_listening = False
        
    async def start_listening(self):
        """Start the STT connection"""
        try:
            # Configure Deepgram options for low latency
            options = LiveOptions(
                model=Config.STT_MODEL,
                language=Config.STT_LANGUAGE,
                encoding=Config.AUDIO_FORMAT,
                channels=Config.CHANNELS,
                sample_rate=Config.SAMPLE_RATE,
                punctuate=Config.STT_PUNCTUATE,
                smart_format=Config.STT_SMART_FORMAT,
                interim_results=Config.STT_INTERIM_RESULTS,
                endpointing=300,  # ms of silence before considering end of speech
                vad_events=True,  # Voice Activity Detection events
            )
            
            # Create the connection
            self.connection = self.client.listen.asyncwebsocket.v("1")
            
            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start the connection
            if await self.connection.start(options):
                self.is_listening = True
                print("STT connection started successfully")
                return True
            else:
                print("Failed to start STT connection")
                return False
                
        except Exception as e:
            print(f"Error starting STT: {e}")
            return False
            
    async def send_audio(self, audio_data):
        """Send audio data to Deepgram for transcription"""
        if self.connection and self.is_listening:
            try:
                self.connection.send(audio_data)
            except Exception as e:
                print(f"Error sending audio: {e}")
                
    async def stop_listening(self):
        """Stop the STT connection"""
        if self.connection:
            try:
                await self.connection.finish()
                self.is_listening = False
                print("STT connection stopped")
            except Exception as e:
                print(f"Error stopping STT: {e}")
                
    def _on_open(self, *args, **kwargs):
        """Handler for connection open"""
        print("STT connection opened")
        
    def _on_message(self, *args, **kwargs):
        """Handler for transcript messages"""
        try:
            result = kwargs.get('result')
            if result:
                transcript = result.channel.alternatives[0].transcript
                is_final = result.is_final
                
                if transcript and is_final:
                    print(f"Final transcript: {transcript}")
                    
                    # Add to queue for processing
                    self.transcript_queue.put(transcript)
                    
                    # Call callback if provided
                    if self.on_transcript_callback:
                        self.on_transcript_callback(transcript)
                        
        except Exception as e:
            print(f"Error processing transcript: {e}")
            
    def _on_error(self, error, **kwargs):
        """Handler for errors"""
        print(f"STT Error: {error}")
        
    def _on_close(self, *args, **kwargs):
        """Handler for connection close"""
        print("STT connection closed")
        self.is_listening = False
        
    def get_transcript(self):
        """Get the next transcript from the queue"""
        try:
            return self.transcript_queue.get_nowait()
        except queue.Empty:
            return None