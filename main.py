#!/usr/bin/env python3
"""
Voice Agent - Low Latency Customer Support Agent
===============================================

A real-time voice agent that acts as a customer support representative
using Deepgram for STT/TTS and OpenAI for LLM processing.

Usage:
    python main.py
    
Make sure to set up your .env file with:
    DEEPGRAM_API_KEY=your_key_here
    OPENAI_API_KEY=your_key_here
"""

import asyncio
import sys
import os
from voice_pipeline import VoicePipeline
from config import Config

def check_dependencies():
    """Check if required API keys are configured"""
    missing_keys = []
    
    if not Config.DEEPGRAM_API_KEY:
        missing_keys.append("DEEPGRAM_API_KEY")
        
    if not Config.OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
        
    if missing_keys:
        print("❌ Missing required API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease set these in your .env file or environment variables.")
        print("See .env.example for the format.")
        return False
        
    return True

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🎤 Voice Agent - Customer Support Bot")
    print("=" * 60)
    print("Configuration:")
    print(f"  📞 STT Model: {Config.STT_MODEL}")
    print(f"  🗣️  TTS Model: {Config.TTS_MODEL}")
    print(f"  🧠 LLM Model: {Config.LLM_MODEL}")
    print(f"  🎯 Target Latency: < 1 second")
    print("=" * 60)

async def main():
    """Main application entry point"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
        
    # Create and start the voice pipeline
    pipeline = VoicePipeline()
    
    try:
        print("\n🚀 Starting Voice Agent...")
        print("💬 Speak naturally - I'm here to help!")
        print("⏹️  Press Ctrl+C to stop\n")
        
        await pipeline.start()
        
    except KeyboardInterrupt:
        print("\n👋 Thanks for using Voice Agent!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
        
    # Run the application
    asyncio.run(main())