"""
Simple Baseline Chatbot (without tools).
This demonstrates the limitations of pure LLM conversation.
"""

import os
import time
from typing import Optional
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger

class SimpleChatbot:
    """
    A simple chatbot that uses only LLM for responses.
    No tool integration - pure conversation model.
    
    This is meant to show the limitations of chatbots for complex,
    multi-step reasoning tasks.
    """
    
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        self.llm = OpenAIProvider(model_name=model_name, api_key=api_key)
        self.conversation_history = []
    
    def get_system_prompt(self) -> str:
        """
        System prompt for the baseline chatbot.
        No tools, just pure conversation.
        """
        return """You are a helpful e-commerce assistant. 
Answer customer questions about products, prices, and orders.
Be concise and helpful.
If you don't know a specific price or stock information, make a reasonable estimate based on typical e-commerce values."""
    
    def chat(self, user_message: str) -> str:
        """
        Simple chat method - just call LLM without any tools.
        """
        logger.log_event("CHATBOT_START", {
            "input": user_message,
            "model": self.llm.model_name,
            "type": "chatbot_baseline"
        })
        
        # Build conversation context
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Call LLM
        start_time = time.time()
        result = self.llm.generate(
            prompt=user_message,
            system_prompt=self.get_system_prompt()
        )
        latency = result["latency_ms"]
        
        response_text = result["content"]
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        # Log metrics
        logger.log_event("CHATBOT_METRIC", {
            "prompt_tokens": result["usage"]["prompt_tokens"],
            "completion_tokens": result["usage"]["completion_tokens"],
            "total_tokens": result["usage"]["total_tokens"],
            "latency_ms": latency,
            "cost_estimate": latency / 1000 * 0.0001  # Mock cost
        })
        
        logger.log_event("CHATBOT_END", {
            "response": response_text,
            "latency_ms": latency
        })
        
        return response_text
