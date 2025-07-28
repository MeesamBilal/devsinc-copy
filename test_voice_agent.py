#!/usr/bin/env python3
"""
Test script for Voice Agent components
"""

import asyncio
import sys
import time
from voice_pipeline import VoicePipeline
from stt_service import STTService
from llm_service import LLMService
from tts_service import TTSService
from config import Config

async def test_llm_service():
    """Test LLM service with sample inputs"""
    print("🧠 Testing LLM Service...")
    
    llm = LLMService()
    
    test_inputs = [
        "Hello, I need help with my account",
        "I can't log into my account",
        "What are your business hours?",
        "I want to cancel my subscription"
    ]
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input: {input_text}")
        
        start_time = time.time()
        response = await llm.generate_response(input_text)
        latency = time.time() - start_time
        
        print(f"Response: {response}")
        print(f"Latency: {latency:.2f}s")
        
    print("\n✅ LLM Service test completed")

async def test_tts_service():
    """Test TTS service with sample text"""
    print("\n🗣️ Testing TTS Service...")
    
    tts = TTSService()
    
    test_texts = [
        "Hello! How can I help you today?",
        "I understand your concern. Let me assist you with that.",
        "Your account has been updated successfully."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Text: {text}")
        
        start_time = time.time()
        audio_data = await tts.synthesize_speech_fast(text)
        latency = time.time() - start_time
        
        if audio_data:
            print(f"Generated {len(audio_data)} bytes of audio")
            print(f"Latency: {latency:.2f}s")
        else:
            print("❌ Failed to generate audio")
            
    print("\n✅ TTS Service test completed")

async def test_end_to_end():
    """Test end-to-end pipeline with text input"""
    print("\n🔄 Testing End-to-End Pipeline...")
    
    pipeline = VoicePipeline()
    
    test_conversations = [
        "Hi, I need help with my billing",
        "I was charged twice this month",
        "Can you help me get a refund?",
        "Thank you for your help"
    ]
    
    for i, text in enumerate(test_conversations, 1):
        print(f"\n--- Conversation Turn {i} ---")
        print(f"User: {text}")
        
        start_time = time.time()
        response = await pipeline.process_single_request(text)
        total_latency = time.time() - start_time
        
        if response:
            print(f"Agent: {response}")
            print(f"Total Latency: {total_latency:.2f}s")
        else:
            print("❌ Failed to generate response")
            
        # Small delay between conversations
        await asyncio.sleep(1)
        
    print("\n✅ End-to-End test completed")

async def performance_test():
    """Test performance with multiple rapid requests"""
    print("\n⚡ Performance Test...")
    
    pipeline = VoicePipeline()
    
    rapid_requests = [
        "Hi",
        "Help",
        "Issue",
        "Thanks"
    ]
    
    print("Testing rapid-fire requests...")
    
    total_start = time.time()
    latencies = []
    
    for i, text in enumerate(rapid_requests, 1):
        start_time = time.time()
        response = await pipeline.process_single_request(text)
        latency = time.time() - start_time
        latencies.append(latency)
        
        print(f"Request {i}: {latency:.2f}s")
        
    total_time = time.time() - total_start
    avg_latency = sum(latencies) / len(latencies)
    
    print(f"\nPerformance Summary:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average latency: {avg_latency:.2f}s")
    print(f"  Min latency: {min(latencies):.2f}s")
    print(f"  Max latency: {max(latencies):.2f}s")
    
    if avg_latency <= 1.0:
        print("✅ Performance target met (< 1s average)")
    else:
        print("⚠️ Performance target not met")

def print_test_menu():
    """Print test menu options"""
    print("\n" + "=" * 50)
    print("🧪 Voice Agent Test Suite")
    print("=" * 50)
    print("1. Test LLM Service")
    print("2. Test TTS Service") 
    print("3. Test End-to-End Pipeline")
    print("4. Performance Test")
    print("5. Run All Tests")
    print("6. Exit")
    print("=" * 50)

async def run_all_tests():
    """Run all test suites"""
    print("🚀 Running All Tests...\n")
    
    try:
        await test_llm_service()
        await test_tts_service()
        await test_end_to_end()
        await performance_test()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

async def main():
    """Main test application"""
    
    # Check if API keys are configured
    if not Config.DEEPGRAM_API_KEY or not Config.OPENAI_API_KEY:
        print("❌ Please configure API keys in .env file before running tests")
        sys.exit(1)
    
    while True:
        print_test_menu()
        
        try:
            choice = input("\nSelect test (1-6): ").strip()
            
            if choice == "1":
                await test_llm_service()
            elif choice == "2":
                await test_tts_service()
            elif choice == "3":
                await test_end_to_end()
            elif choice == "4":
                await performance_test()
            elif choice == "5":
                await run_all_tests()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())