import asyncio
import threading
import time
import queue
from audio_utils import AudioCapture, AudioPlayer
from stt_service import STTService
from llm_service import LLMService
from tts_service import TTSService
from config import Config

class VoicePipeline:
    def __init__(self):
        # Initialize components
        self.audio_capture = AudioCapture()
        self.audio_player = AudioPlayer()
        self.stt_service = STTService(on_transcript_callback=self._on_transcript)
        self.llm_service = LLMService()
        self.tts_service = TTSService()
        
        # Pipeline state
        self.is_running = False
        self.is_processing = False
        self.current_transcript = ""
        self.response_queue = queue.Queue()
        
        # Performance tracking
        self.last_speech_time = None
        self.response_start_time = None
        
    async def start(self):
        """Start the voice pipeline"""
        print("Starting Voice Pipeline...")
        
        try:
            # Start STT service
            if not await self.stt_service.start_listening():
                print("Failed to start STT service")
                return False
                
            # Start audio capture
            self.audio_capture.start_recording()
            
            # Start main pipeline loop
            self.is_running = True
            
            # Run pipeline tasks concurrently
            tasks = [
                asyncio.create_task(self._audio_processing_loop()),
                asyncio.create_task(self._response_processing_loop()),
                asyncio.create_task(self._audio_playback_loop())
            ]
            
            print("Voice Pipeline started successfully!")
            print("Speak now... (Press Ctrl+C to stop)")
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            print("\nStopping Voice Pipeline...")
            await self.stop()
        except Exception as e:
            print(f"Error in pipeline: {e}")
            await self.stop()
            
    async def stop(self):
        """Stop the voice pipeline"""
        print("Stopping pipeline components...")
        
        self.is_running = False
        
        # Stop components
        await self.stt_service.stop_listening()
        self.audio_capture.stop_recording()
        
        # Cleanup
        self.audio_capture.cleanup()
        self.audio_player.cleanup()
        
        print("Pipeline stopped.")
        
    async def _audio_processing_loop(self):
        """Main loop for processing audio input"""
        audio_buffer = b""
        silence_detected = False
        
        while self.is_running:
            try:
                # Get audio chunk
                audio_chunk = self.audio_capture.get_audio_chunk()
                
                if audio_chunk:
                    # Send to STT service immediately for real-time processing
                    await self.stt_service.send_audio(audio_chunk)
                    
                    # Add to buffer for silence detection
                    audio_buffer += audio_chunk
                    
                    # Detect silence to know when user stopped speaking
                    if self.audio_capture.detect_silence(audio_chunk):
                        if not silence_detected and len(audio_buffer) > 0:
                            silence_detected = True
                            print("Silence detected - processing speech...")
                    else:
                        silence_detected = False
                        
                    # Keep buffer manageable
                    if len(audio_buffer) > Config.SAMPLE_RATE * 5 * 2:  # 5 seconds of audio
                        audio_buffer = audio_buffer[-Config.SAMPLE_RATE * 3 * 2:]  # Keep last 3 seconds
                        
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"Error in audio processing loop: {e}")
                await asyncio.sleep(0.1)
                
    async def _response_processing_loop(self):
        """Loop for processing LLM responses and generating TTS"""
        while self.is_running:
            try:
                # Check for new transcripts
                transcript = self.stt_service.get_transcript()
                
                if transcript and not self.is_processing:
                    self.is_processing = True
                    self.response_start_time = time.time()
                    
                    print(f"Processing transcript: {transcript}")
                    
                    # Generate LLM response
                    response = await self.llm_service.generate_response(transcript)
                    
                    if response:
                        print(f"Generated response: {response}")
                        
                        # Generate TTS audio
                        audio_data = await self.tts_service.synthesize_speech_fast(response)
                        
                        if audio_data:
                            # Add to audio playback queue
                            self.response_queue.put(audio_data)
                            
                            # Calculate and log latency
                            if self.response_start_time:
                                latency = time.time() - self.response_start_time
                                print(f"Total response latency: {latency:.2f} seconds")
                                
                    self.is_processing = False
                    
                await asyncio.sleep(0.05)  # Check every 50ms
                
            except Exception as e:
                print(f"Error in response processing loop: {e}")
                self.is_processing = False
                await asyncio.sleep(0.1)
                
    async def _audio_playback_loop(self):
        """Loop for playing audio responses"""
        while self.is_running:
            try:
                # Check for audio to play
                try:
                    audio_data = self.response_queue.get_nowait()
                    if audio_data:
                        print("Playing response audio...")
                        # Play audio in a separate thread to avoid blocking
                        playback_thread = threading.Thread(
                            target=self.audio_player.play_audio,
                            args=(audio_data,)
                        )
                        playback_thread.daemon = True
                        playback_thread.start()
                except queue.Empty:
                    pass
                    
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error in audio playback loop: {e}")
                await asyncio.sleep(0.1)
                
    def _on_transcript(self, transcript):
        """Callback for when transcript is received"""
        self.current_transcript = transcript
        self.last_speech_time = time.time()
        
    async def process_single_request(self, text_input):
        """Process a single text request (for testing)"""
        try:
            print(f"Processing text input: {text_input}")
            
            # Generate LLM response
            response = await self.llm_service.generate_response(text_input)
            
            if response:
                print(f"Generated response: {response}")
                
                # Generate TTS audio
                audio_data = await self.tts_service.synthesize_speech(response)
                
                if audio_data:
                    # Play audio
                    self.audio_player.play_audio(audio_data)
                    return response
                    
        except Exception as e:
            print(f"Error processing single request: {e}")
            
        return None
        
    def get_pipeline_status(self):
        """Get current pipeline status"""
        return {
            "is_running": self.is_running,
            "is_processing": self.is_processing,
            "stt_listening": self.stt_service.is_listening,
            "current_transcript": self.current_transcript,
            "last_speech_time": self.last_speech_time,
            "conversation_summary": self.llm_service.get_conversation_summary()
        }