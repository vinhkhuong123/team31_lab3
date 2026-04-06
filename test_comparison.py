#!/usr/bin/env python3
"""
Test Runner: Chatbot vs ReAct Agent Comparison.
Runs both systems on the same E-commerce test cases and compares results.
"""

import os
import json
import time
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools.ecommerce_tools import get_tool_definitions
from src.telemetry.logger import logger

# Load environment
load_dotenv()

# Test cases for E-commerce scenario
TEST_CASES = [
    {
        "id": 1,
        "name": "Simple Product Query",
        "query": "What is the price of an iPhone?",
        "complexity": "simple",
        "requires_tools": False
    },
    {
        "id": 2,
        "name": "Multi-step Reasoning",
        "query": "I want to buy 2 iPhones using coupon code WINNER and ship to Hanoi. What is the total price?",
        "complexity": "complex",
        "requires_tools": True
    },
    {
        "id": 3,
        "name": "Stock Check with Discount",
        "query": "Check if MacBook is in stock and calculate the price with STUDENT discount code",
        "complexity": "complex",
        "requires_tools": True
    },
    {
        "id": 4,
        "name": "Invalid Coupon Handling",
        "query": "What's the final cost for 5 AirPods with code INVALID shipped to USA?",
        "complexity": "complex",
        "requires_tools": True
    }
]

class ComparisonRunner:
    """Runs chatbot and agent on same queries and compares."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        
        # Initialize systems
        self.chatbot = SimpleChatbot(model_name=self.model, api_key=self.api_key)
        
        llm = OpenAIProvider(model_name=self.model, api_key=self.api_key)
        tools = get_tool_definitions()
        self.agent = ReActAgent(llm=llm, tools=tools, max_steps=5)
        
        self.results = []
    
    def run_test(self, test_case: dict) -> dict:
        """Run a test case on both systems."""
        
        print(f"\n{'='*70}")
        print(f"Test {test_case['id']}: {test_case['name']}")
        print(f"Complexity: {test_case['complexity']}")
        print(f"Query: {test_case['query']}")
        print(f"{'='*70}")
        
        query = test_case['query']
        
        # Run Chatbot
        print("\n[Chatbot Baseline]")
        print("-" * 70)
        try:
            chatbot_start = time.time()
            chatbot_answer = self.chatbot.chat(query)
            chatbot_time = (time.time() - chatbot_start) * 1000
            
            print(f"Answer: {chatbot_answer[:200]}...")
            print(f"Time: {chatbot_time:.0f}ms")
            chatbot_result = {
                "status": "success",
                "answer": chatbot_answer,
                "time_ms": chatbot_time,
                "tool_calls": 0
            }
        except Exception as e:
            print(f"Error: {str(e)}")
            chatbot_result = {
                "status": "error",
                "error": str(e),
                "time_ms": 0,
                "tool_calls": 0
            }
        
        # Run Agent
        print("\n[ReAct Agent]")
        print("-" * 70)
        try:
            agent_start = time.time()
            agent_answer = self.agent.run(query)
            agent_time = (time.time() - agent_start) * 1000
            
            print(f"Answer: {agent_answer[:200]}...")
            print(f"Time: {agent_time:.0f}ms")
            agent_result = {
                "status": "success",
                "answer": agent_answer,
                "time_ms": agent_time,
                "tool_calls": 1  # Simplified - count as 1 if tools were used
            }
        except Exception as e:
            print(f"Error: {str(e)}")
            agent_result = {
                "status": "error",
                "error": str(e),
                "time_ms": 0,
                "tool_calls": 0
            }
        
        result = {
            "test_id": test_case['id'],
            "test_name": test_case['name'],
            "complexity": test_case['complexity'],
            "requires_tools": test_case['requires_tools'],
            "chatbot": chatbot_result,
            "agent": agent_result
        }
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """Run all test cases."""
        print("\n" + "="*70)
        print("🤖 CHATBOT vs ReAct AGENT - E-COMMERCE SCENARIO")
        print("="*70)
        
        for test_case in TEST_CASES:
            try:
                self.run_test(test_case)
            except Exception as e:
                logger.error(f"Test {test_case['id']} failed: {str(e)}")
                print(f"\n⚠️ Test {test_case['id']} failed: {str(e)}")
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print comparison summary."""
        print("\n" + "="*70)
        print("📊 SUMMARY COMPARISON")
        print("="*70)
        
        if not self.results:
            print("No results to summarize")
            return
        
        print(f"{'Test':<20} {'Complexity':<15} {'Chatbot Time':<15} {'Agent Time':<15} {'Winner':<10}")
        print("-"*70)
        
        total_chatbot_time = 0
        total_agent_time = 0
        chatbot_wins = 0
        agent_wins = 0
        
        for result in self.results:
            if result['chatbot']['status'] == 'success' and result['agent']['status'] == 'success':
                cb_time = result['chatbot']['time_ms']
                ag_time = result['agent']['time_ms']
                total_chatbot_time += cb_time
                total_agent_time += ag_time
                
                winner = "Chatbot" if cb_time < ag_time else "Agent"
                if winner == "Chatbot":
                    chatbot_wins += 1
                else:
                    agent_wins += 1
                
                print(f"{result['test_name']:<20} {result['complexity']:<15} {cb_time:<15.0f} {ag_time:<15.0f} {winner:<10}")
            else:
                print(f"{result['test_name']:<20} {result['complexity']:<15} {'ERROR':<15} {'ERROR':<15}")
        
        print("-"*70)
        if self.results:
            avg_chatbot = total_chatbot_time / len([r for r in self.results if r['chatbot']['status'] == 'success']) if total_chatbot_time > 0 else 0
            avg_agent = total_agent_time / len([r for r in self.results if r['agent']['status'] == 'success']) if total_agent_time > 0 else 0
            print(f"{'AVERAGE':<20} {'N/A':<15} {avg_chatbot:<15.0f} {avg_agent:<15.0f}")
            print(f"\nChatbot Wins: {chatbot_wins}")
            print(f"Agent Wins: {agent_wins}")
        
        print("\n✅ Test completed. Check logs/ for detailed execution logs.\n")
    
    def save_results(self):
        """Save results to JSON for later analysis."""
        output_file = "test_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ Results saved to {output_file}")


def main():
    """Main entry point."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return
    
    runner = ComparisonRunner(api_key=api_key)
    runner.run_all_tests()


if __name__ == "__main__":
    main()