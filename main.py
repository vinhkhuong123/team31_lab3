#!/usr/bin/env python3
"""
Main entry point for Lab 3: Chatbot vs ReAct Agent.
Demonstrates ReAct Agent with OpenAI.
"""

import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

# Load environment variables
load_dotenv()

def define_tools():
    """
    Define available tools for the agent.
    Each tool is a dict with name, description, and optional function.
    """
    tools = [
        {
            "name": "calculator",
            "description": "Performs basic arithmetic operations. Usage: calculator(expression)",
            "func": lambda x: eval(x) if x else 0  # Simple eval for demo
        },
        {
            "name": "search",
            "description": "Searches for information. Usage: search(query)",
            "func": lambda x: f"Search results for '{x}'"
        },
        {
            "name": "weather",
            "description": "Gets weather information. Usage: weather(city)",
            "func": lambda x: f"Weather in {x}: 25°C, Sunny"
        }
    ]
    return tools

def main():
    """Main function to run the ReAct Agent."""
    
    # Step 1: Initialize OpenAI Provider
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")
    
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env file!")
        return
    
    logger.info(f"Initializing OpenAI Provider with model: {model}")
    llm = OpenAIProvider(model_name=model, api_key=api_key)
    
    # Step 2: Define tools
    tools = define_tools()
    logger.info(f"Loaded {len(tools)} tools: {[t['name'] for t in tools]}")
    
    # Step 3: Create ReAct Agent
    agent = ReActAgent(llm=llm, tools=tools, max_steps=5)
    
    # Step 4: Test queries
    test_queries = [
        "What is 2 + 2 * 5?",
        "Search for information about Python programming",
        "What's the weather in Tokyo?"
    ]
    
    print("\n" + "="*60)
    print("🤖 ReAct Agent with OpenAI")
    print("="*60 + "\n")
    
    for query in test_queries:
        print(f"User: {query}")
        print("-" * 60)
        
        try:
            response = agent.run(query)
            print(f"Agent: {response}")
        except Exception as e:
            logger.error(f"Error during agent execution: {str(e)}")
            print(f"Error: {str(e)}")
        
        print("\n")
    
    # Step 5: Print metrics summary
    print("="*60)
    print("📊 Execution Metrics")
    print("="*60)
    print(f"Total requests: {len(tracker.session_metrics)}")
    
    if tracker.session_metrics:
        total_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
        total_latency = sum(m.get("latency_ms", 0) for m in tracker.session_metrics)
        avg_latency = total_latency / len(tracker.session_metrics) if tracker.session_metrics else 0
    print(f"Total tokens used: {total_tokens}")
    print(f"Average latency: {avg_latency:.0f}ms")
    print(f"Provider: {tracker.session_metrics[0].get('provider', 'unknown')}")
    
    print("\n✅ Test completed. Check logs/ folder for detailed logs.\n")

    if __name__ == "__main__":
        main()