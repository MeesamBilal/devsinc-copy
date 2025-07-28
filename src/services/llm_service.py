import asyncio
import logging
from typing import Optional, Callable, AsyncGenerator
from openai import AsyncOpenAI
from ..config import Config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, on_response_chunk: Optional[Callable[[str], None]] = None):
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.on_response_chunk = on_response_chunk
        self.system_prompt = self._get_system_prompt()
        self.conversation_history = []
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the customer support agent"""
        return """You are a helpful and friendly customer support agent. 
        Your responses should be:
        - Concise and clear (aim for 1-2 sentences)
        - Professional but warm
        - Focused on solving the customer's problem
        - Quick to understand and easy to follow
        
        Keep your responses brief since this is a voice conversation.
        If you need more information, ask one specific question at a time."""
    
    async def generate_response(self, user_input: str) -> AsyncGenerator[str, None]:
        """Generate streaming response from the LLM"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare messages for API call
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-10:])  # Keep last 10 messages for context
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=Config.OPENAI_SETTINGS["model"],
                messages=messages,
                temperature=Config.OPENAI_SETTINGS["temperature"],
                max_tokens=Config.OPENAI_SETTINGS["max_tokens"],
                stream=True
            )
            
            response_text = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    
                    # Call the callback if provided
                    if self.on_response_chunk:
                        self.on_response_chunk(content)
                    
                    yield content
            
            # Add assistant response to conversation history
            if response_text:
                self.conversation_history.append({"role": "assistant", "content": response_text})
                logger.debug(f"Generated response: {response_text}")
            
        except Exception as e:
            error_msg = f"Error generating LLM response: {e}"
            logger.error(error_msg)
            yield "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
    
    async def generate_response_complete(self, user_input: str) -> str:
        """Generate complete response (non-streaming) for testing"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare messages for API call
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-10:])
            
            # Create completion
            response = await self.client.chat.completions.create(
                model=Config.OPENAI_SETTINGS["model"],
                messages=messages,
                temperature=Config.OPENAI_SETTINGS["temperature"],
                max_tokens=Config.OPENAI_SETTINGS["max_tokens"],
                stream=False
            )
            
            response_text = response.choices[0].message.content
            
            # Add assistant response to conversation history
            if response_text:
                self.conversation_history.append({"role": "assistant", "content": response_text})
                logger.debug(f"Generated complete response: {response_text}")
            
            return response_text or "I'm sorry, I couldn't generate a response."
            
        except Exception as e:
            error_msg = f"Error generating LLM response: {e}"
            logger.error(error_msg)
            return "I apologize, but I'm having trouble processing your request right now. Could you please try again?"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history"
        
        summary = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            role = "User" if msg["role"] == "user" else "Agent"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary.append(f"{role}: {content}")
        
        return "\n".join(summary)