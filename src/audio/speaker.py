import pyaudio
import threading
import queue
import logging
from typing import Optional
from ..config import Config

logger = logging.getLogger(__name__)

class Speaker:
    def __init__(self):
        self.sample_rate = Config.SAMPLE_RATE
        self.chunk_size = Config.CHUNK_SIZE
        self.channels = Config.CHANNELS
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_playing = False
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        
        self._setup_stream()
    
    def _setup_stream(self):
        """Initialize the audio output stream"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size,
                start=False
            )
            logger.info("Speaker stream initialized")
        except Exception as e:
            logger.error(f"Failed to initialize speaker: {e}")
            raise
    
    def _playback_worker(self):
        """Worker thread for audio playback"""
        while self.is_playing:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                if audio_chunk and self.stream:
                    self.stream.write(audio_chunk)
                self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Playback error: {e}")
    
    def start_playback(self):
        """Start audio playback"""
        if not self.is_playing:
            self.is_playing = True
            if self.stream:
                self.stream.start_stream()
            
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
            logger.info("Started playback")
    
    def stop_playback(self):
        """Stop audio playback"""
        if self.is_playing:
            self.is_playing = False
            
            # Wait for queue to empty
            self.audio_queue.join()
            
            if self.stream:
                self.stream.stop_stream()
            
            if self.playback_thread:
                self.playback_thread.join(timeout=1.0)
            
            logger.info("Stopped playback")
    
    def play_audio_chunk(self, audio_chunk: bytes):
        """Add audio chunk to playback queue"""
        if self.is_playing:
            self.audio_queue.put(audio_chunk)
    
    def play_audio_stream(self, audio_stream):
        """Play audio from a stream (generator)"""
        for chunk in audio_stream:
            if chunk:
                self.play_audio_chunk(chunk)
    
    def clear_queue(self):
        """Clear the audio queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
    
    def close(self):
        """Clean up resources"""
        self.stop_playback()
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        logger.info("Speaker closed")