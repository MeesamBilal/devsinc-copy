import pyaudio
import numpy as np
import wave
import threading
import queue
import time
from config import Config

class AudioCapture:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.silence_start = None
        
    def start_recording(self):
        """Start recording audio in a separate thread"""
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
            
    def _record_audio(self):
        """Internal method to record audio"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=Config.CHANNELS,
            rate=Config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=Config.CHUNK_SIZE
        )
        
        try:
            while self.is_recording:
                data = stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)
                self.audio_queue.put(data)
        finally:
            stream.stop_stream()
            stream.close()
            
    def get_audio_chunk(self):
        """Get the next audio chunk from the queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
            
    def detect_silence(self, audio_data):
        """Detect if the audio chunk contains silence"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_array**2))
        normalized_rms = rms / 32768.0  # Normalize to 0-1 range
        
        is_silent = normalized_rms < Config.SILENCE_THRESHOLD
        
        if is_silent:
            if self.silence_start is None:
                self.silence_start = time.time()
            elif time.time() - self.silence_start > Config.SILENCE_DURATION:
                return True
        else:
            self.silence_start = None
            
        return False
        
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.audio.terminate()

class AudioPlayer:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_playing = False
        
    def play_audio(self, audio_data, sample_rate=Config.TTS_SAMPLE_RATE):
        """Play audio data"""
        if self.is_playing:
            return
            
        self.is_playing = True
        
        # Create a stream for playback
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True
        )
        
        try:
            # Play the audio data
            stream.write(audio_data)
        finally:
            stream.stop_stream()
            stream.close()
            self.is_playing = False
            
    def cleanup(self):
        """Clean up audio resources"""
        self.audio.terminate()