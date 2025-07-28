import openai
import asyncio
from config import Config
import queue
import threading

class LLMService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.conversation_history = [
            {"role": "system", "content": Config.SYSTEM_PROMPT}
        ]
        self.response_queue = queue.Queue()
        
    async def generate_response(self, user_input):
        """Generate a response using OpenAI's streaming API"""
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history) > 11:  # 1 system + 10 messages
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            print(f"Generating response for: {user_input}")
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=self.conversation_history,
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=Config.LLM_TEMPERATURE,
                stream=True
            )
            
            response_text = ""
            
            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    
            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            print(f"Generated response: {response_text}")
            return response_text.strip()
            
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
            
    async def generate_response_streaming(self, user_input, callback=None):
        """Generate a response with streaming callback for real-time processing"""
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 11:
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            print(f"Generating streaming response for: {user_input}")
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=self.conversation_history,
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=Config.LLM_TEMPERATURE,
                stream=True
            )
            
            response_text = ""
            
            # Process streaming response
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    
                    # Call callback with incremental text if provided
                    if callback:
                        callback(content)
                        
            # Add complete response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            return response_text.strip()
            
        except Exception as e:
            print(f"Error generating streaming LLM response: {e}")
            error_response = "I apologize, but I'm having trouble processing your request right now."
            if callback:
                callback(error_response)
            return error_response
            
    def clear_history(self):
        """Clear conversation history except system prompt"""
        self.conversation_history = [self.conversation_history[0]]
        
    def get_conversation_summary(self):
        """Get a summary of the current conversation"""
        return {
            "message_count": len(self.conversation_history) - 1,  # Exclude system prompt
            "last_user_message": next((msg["content"] for msg in reversed(self.conversation_history) if msg["role"] == "user"), None),
            "last_assistant_message": next((msg["content"] for msg in reversed(self.conversation_history) if msg["role"] == "assistant"), None)
        }