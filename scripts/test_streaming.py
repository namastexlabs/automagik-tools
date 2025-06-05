#!/usr/bin/env python3
"""Test script to verify agno streaming works"""

import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

print("Testing agno streaming...")
print(f"API Key: {'Set' if api_key else 'Not set'}")

# Create a simple agent
agent = Agent(
    model=OpenAIChat(id="gpt-4.1", api_key=api_key),
    description="You are a helpful assistant",
    instructions="Be concise and clear",
)

# Test 1: Using print_response (should definitely stream)
print("\n=== Test 1: Using print_response ===")
agent.print_response("Count from 1 to 10 slowly", stream=True)

# Test 2: Manual streaming
print("\n\n=== Test 2: Manual streaming ===")
response_stream = agent.run("List 5 colors one by one", stream=True)

chunk_count = 0
for chunk in response_stream:
    chunk_count += 1
    print(f"\nChunk {chunk_count}:")
    print(f"  Type: {type(chunk).__name__}")
    if hasattr(chunk, 'content') and chunk.content:
        print(f"  Content: '{chunk.content}'")
    if hasattr(chunk, 'thinking') and chunk.thinking:
        print(f"  Thinking: '{chunk.thinking[:50]}...'")
    if hasattr(chunk, 'event'):
        print(f"  Event: {chunk.event}")

print(f"\nTotal chunks received: {chunk_count}")