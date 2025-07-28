#!/usr/bin/env python3
"""
Voice Agent Main Application

A low-latency voice agent using Deepgram for STT/TTS and OpenAI for LLM.
Inspired by LiveKit's pipeline architecture for real-time processing.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from src.pipeline.voice_pipeline import VoicePipeline
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('voice_agent.log')
    ]
)

logger = logging.getLogger(__name__)

class VoiceAgent:
    def __init__(self):
        self.pipeline: Optional[VoicePipeline] = None
        self.running = False
        
    def on_status_change(self, status: str):
        """Handle pipeline status changes"""
        status_messages = {
            "initialized": "🔧 Voice agent initialized",
            "listening": "🎤 Listening for your voice...",
            "processing": "🤔 Processing your request...",
            "speaking": "🗣️  Responding...",
            "error": "❌ Error occurred",
            "stopped": "🛑 Voice agent stopped"
        }
        
        message = status_messages.get(status, f"Status: {status}")
        print(f"\r{message}")
        
        if status == "listening":
            print("💡 Speak now! (Press Ctrl+C to stop)")
        elif status == "error":
            print("⚠️  Please check your API keys and try again")
    
    async def start(self):
        """Start the voice agent"""
        try:
            # Validate configuration
            if not Config.DEEPGRAM_API_KEY:
                logger.error("DEEPGRAM_API_KEY not found in environment")
                print("❌ Please set DEEPGRAM_API_KEY in your .env file")
                return False
            
            if not Config.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY not found in environment")
                print("❌ Please set OPENAI_API_KEY in your .env file")
                return False
            
            print("🚀 Starting Voice Agent...")
            print("📋 Configuration:")
            print(f"   - Sample Rate: {Config.SAMPLE_RATE} Hz")
            print(f"   - Chunk Size: {Config.CHUNK_SIZE}")
            print(f"   - STT Model: {Config.DEEPGRAM_MODEL}")
            print(f"   - TTS Model: {Config.DEEPGRAM_TTS_MODEL}")
            print(f"   - LLM Model: {Config.OPENAI_MODEL}")
            print("")
            
            # Initialize pipeline
            self.pipeline = VoicePipeline(on_status_change=self.on_status_change)
            await self.pipeline.initialize()
            
            # Start the pipeline
            await self.pipeline.start()
            self.running = True
            
            print("✅ Voice agent is ready!")
            print("💬 You can now have a conversation with the AI assistant")
            print("")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice agent: {e}")
            print(f"❌ Failed to start: {e}")
            return False
    
    async def stop(self):
        """Stop the voice agent"""
        if self.pipeline and self.running:
            print("\n🛑 Stopping voice agent...")
            await self.pipeline.stop()
            self.running = False
            print("👋 Voice agent stopped. Goodbye!")
    
    async def run(self):
        """Run the voice agent"""
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the agent
        if not await self.start():
            return
        
        try:
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
                # Optional: Print status every 30 seconds
                if hasattr(self, '_last_status_time'):
                    if asyncio.get_event_loop().time() - self._last_status_time > 30:
                        if self.pipeline:
                            status = self.pipeline.get_status()
                            logger.debug(f"Pipeline status: {status}")
                        self._last_status_time = asyncio.get_event_loop().time()
                else:
                    self._last_status_time = asyncio.get_event_loop().time()
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()

async def main():
    """Main entry point"""
    print("🎙️  Voice Agent - Real-time AI Customer Support")
    print("=" * 50)
    print("")
    
    agent = VoiceAgent()
    await agent.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")
        sys.exit(1)