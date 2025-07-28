import pyaudio
import threading
import queue
import logging
from typing import Optional, Callable
from ..config import Config

logger = logging.getLogger(__name__)

class Microphone:
    def __init__(self, on_audio_chunk: Optional[Callable[[bytes], None]] = None):
        self.sample_rate = Config.SAMPLE_RATE
        self.chunk_size = Config.CHUNK_SIZE
        self.channels = Config.CHANNELS
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.on_audio_chunk = on_audio_chunk
        
        self._setup_stream()
    
    def _setup_stream(self):
        """Initialize the audio stream"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback,
                start=False
            )
            logger.info("Microphone stream initialized")
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            raise
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_recording and in_data:
            if self.on_audio_chunk:
                self.on_audio_chunk(in_data)
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def start_recording(self):
        """Start recording audio"""
        if not self.is_recording:
            self.is_recording = True
            if self.stream:
                self.stream.start_stream()
            logger.info("Started recording")
    
    def stop_recording(self):
        """Stop recording audio"""
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
            logger.info("Stopped recording")
    
    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """Get audio chunk from queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def close(self):
        """Clean up resources"""
        self.stop_recording()
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        logger.info("Microphone closed")