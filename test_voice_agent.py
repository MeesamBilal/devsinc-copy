#!/usr/bin/env python3
"""
Test script for the Voice Agent

This script tests individual components and the full pipeline
to ensure everything works correctly before running the full voice agent.
"""

import asyncio
import logging
import sys
import time
from unittest.mock import AsyncMock, MagicMock

from src.config import Config
from src.services.stt_service import STTService
from src.services.llm_service import LLMService
from src.services.tts_service import TTSService
from src.pipeline.voice_pipeline import VoicePipeline

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class VoiceAgentTester:
    def __init__(self):
        self.test_results = {}
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        self.test_results[test_name] = success
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    async def test_config(self):
        """Test configuration loading"""
        try:
            # Test API key presence
            has_deepgram = bool(Config.DEEPGRAM_API_KEY)
            has_openai = bool(Config.OPENAI_API_KEY)
            
            self.log_test_result(
                "Config - Deepgram API Key", 
                has_deepgram,
                "Set DEEPGRAM_API_KEY in .env file" if not has_deepgram else ""
            )
            
            self.log_test_result(
                "Config - OpenAI API Key", 
                has_openai,
                "Set OPENAI_API_KEY in .env file" if not has_openai else ""
            )
            
            # Test audio configuration
            config_valid = all([
                Config.SAMPLE_RATE > 0,
                Config.CHUNK_SIZE > 0,
                Config.CHANNELS > 0,
                Config.STT_SETTINGS,
                Config.TTS_SETTINGS,
                Config.OPENAI_SETTINGS
            ])
            
            self.log_test_result(
                "Config - Audio & Model Settings", 
                config_valid,
                f"Sample Rate: {Config.SAMPLE_RATE}, Chunk Size: {Config.CHUNK_SIZE}"
            )
            
            return has_deepgram and has_openai and config_valid
            
        except Exception as e:
            self.log_test_result("Config Loading", False, str(e))
            return False
    
    async def test_llm_service(self):
        """Test LLM service"""
        try:
            if not Config.OPENAI_API_KEY:
                self.log_test_result("LLM Service", False, "OpenAI API key required")
                return False
            
            llm_service = LLMService()
            
            # Test streaming response
            print("    Testing LLM streaming response...")
            start_time = time.time()
            
            response_chunks = []
            async for chunk in llm_service.generate_response("Hello, how are you today?"):
                response_chunks.append(chunk)
                if len(response_chunks) == 1:  # First chunk
                    first_chunk_time = time.time() - start_time
                    print(f"    First chunk received in {first_chunk_time:.3f}s")
            
            total_time = time.time() - start_time
            full_response = "".join(response_chunks)
            
            success = len(response_chunks) > 0 and len(full_response.strip()) > 0
            
            self.log_test_result(
                "LLM Service - Streaming Response",
                success,
                f"Response time: {total_time:.3f}s, Chunks: {len(response_chunks)}"
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("LLM Service", False, str(e))
            return False
    
    async def test_tts_service(self):
        """Test TTS service"""
        try:
            if not Config.DEEPGRAM_API_KEY:
                self.log_test_result("TTS Service", False, "Deepgram API key required")
                return False
            
            tts_service = TTSService()
            
            print("    Testing TTS synthesis...")
            start_time = time.time()
            
            test_text = "Hello, this is a test of the text-to-speech service."
            audio_chunks = []
            
            async for chunk in tts_service.synthesize_speech(test_text):
                audio_chunks.append(chunk)
                if len(audio_chunks) == 1:  # First chunk
                    first_chunk_time = time.time() - start_time
                    print(f"    First audio chunk in {first_chunk_time:.3f}s")
            
            total_time = time.time() - start_time
            total_audio_size = sum(len(chunk) for chunk in audio_chunks)
            
            success = len(audio_chunks) > 0 and total_audio_size > 0
            
            self.log_test_result(
                "TTS Service - Speech Synthesis",
                success,
                f"Synthesis time: {total_time:.3f}s, Audio size: {total_audio_size} bytes"
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("TTS Service", False, str(e))
            return False
    
    async def test_stt_service(self):
        """Test STT service (connection only)"""
        try:
            if not Config.DEEPGRAM_API_KEY:
                self.log_test_result("STT Service", False, "Deepgram API key required")
                return False
            
            # Test callback
            transcript_received = False
            
            def on_transcript(transcript, is_final):
                nonlocal transcript_received
                transcript_received = True
                print(f"    Received transcript: '{transcript}' (final: {is_final})")
            
            stt_service = STTService(on_transcript=on_transcript)
            
            print("    Testing STT connection...")
            start_time = time.time()
            
            connection_success = await stt_service.start_connection()
            connection_time = time.time() - start_time
            
            if connection_success:
                # Test sending dummy audio data
                dummy_audio = b'\x00' * 1024  # Silence
                await stt_service.send_audio(dummy_audio)
                
                # Wait a moment for potential response
                await asyncio.sleep(1)
                
                await stt_service.stop_connection()
                
                self.log_test_result(
                    "STT Service - Connection",
                    True,
                    f"Connection time: {connection_time:.3f}s"
                )
                return True
            else:
                self.log_test_result("STT Service - Connection", False, "Failed to connect")
                return False
                
        except Exception as e:
            self.log_test_result("STT Service", False, str(e))
            return False
    
    async def test_audio_components(self):
        """Test audio components (basic initialization)"""
        try:
            # Test microphone (without actually starting recording)
            from src.audio.microphone import Microphone
            mic = Microphone()
            mic_success = mic.stream is not None
            mic.close()
            
            self.log_test_result("Audio - Microphone Init", mic_success)
            
            # Test speaker (without actually starting playback)
            from src.audio.speaker import Speaker
            speaker = Speaker()
            speaker_success = speaker.stream is not None
            speaker.close()
            
            self.log_test_result("Audio - Speaker Init", speaker_success)
            
            return mic_success and speaker_success
            
        except Exception as e:
            self.log_test_result("Audio Components", False, str(e))
            return False
    
    async def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        try:
            if not (Config.DEEPGRAM_API_KEY and Config.OPENAI_API_KEY):
                self.log_test_result("Pipeline Init", False, "API keys required")
                return False
            
            pipeline = VoicePipeline()
            
            print("    Initializing pipeline...")
            start_time = time.time()
            
            await pipeline.initialize()
            init_time = time.time() - start_time
            
            # Check status
            status = pipeline.get_status()
            
            success = all([
                pipeline.stt_service is not None,
                pipeline.llm_service is not None,
                pipeline.tts_service is not None,
                pipeline.microphone is not None,
                pipeline.speaker is not None,
                status["stt_connected"]
            ])
            
            await pipeline.stop()
            
            self.log_test_result(
                "Pipeline - Initialization",
                success,
                f"Init time: {init_time:.3f}s, STT connected: {status['stt_connected']}"
            )
            
            return success
            
        except Exception as e:
            self.log_test_result("Pipeline Initialization", False, str(e))
            return False
    
    async def test_end_to_end_simulation(self):
        """Test end-to-end pipeline with simulated data"""
        try:
            if not (Config.DEEPGRAM_API_KEY and Config.OPENAI_API_KEY):
                self.log_test_result("E2E Simulation", False, "API keys required")
                return False
            
            print("    Running end-to-end simulation...")
            
            # Mock a complete conversation flow
            llm_service = LLMService()
            tts_service = TTSService()
            
            # Simulate user input
            user_input = "Hello, I need help with my account"
            
            print(f"    Simulated user input: '{user_input}'")
            
            # Process through LLM
            start_time = time.time()
            response_text = ""
            
            async for chunk in llm_service.generate_response(user_input):
                response_text += chunk
            
            llm_time = time.time() - start_time
            
            # Process through TTS
            tts_start = time.time()
            audio_chunks = []
            
            async for audio_chunk in tts_service.synthesize_speech(response_text):
                audio_chunks.append(audio_chunk)
            
            tts_time = time.time() - tts_start
            total_time = time.time() - start_time
            
            success = len(response_text.strip()) > 0 and len(audio_chunks) > 0
            
            self.log_test_result(
                "E2E Simulation - LLM+TTS",
                success,
                f"Total: {total_time:.3f}s (LLM: {llm_time:.3f}s, TTS: {tts_time:.3f}s)"
            )
            
            if success:
                print(f"    AI Response: '{response_text[:100]}...'")
                print(f"    Audio chunks: {len(audio_chunks)}")
            
            return success
            
        except Exception as e:
            self.log_test_result("E2E Simulation", False, str(e))
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Voice Agent Test Suite")
        print("=" * 50)
        print("")
        
        tests = [
            ("Configuration", self.test_config),
            ("Audio Components", self.test_audio_components),
            ("LLM Service", self.test_llm_service),
            ("TTS Service", self.test_tts_service),
            ("STT Service", self.test_stt_service),
            ("Pipeline Init", self.test_pipeline_initialization),
            ("E2E Simulation", self.test_end_to_end_simulation),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name}...")
            await test_func()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your voice agent is ready to run.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return passed == total

async def main():
    """Main test entry point"""
    tester = VoiceAgentTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Ready to run: python main.py")
    else:
        print("\n🔧 Fix the issues above before running the voice agent")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test error: {e}")
        print(f"❌ Test error: {e}")
        sys.exit(1)