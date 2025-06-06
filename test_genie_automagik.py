#!/usr/bin/env python3
"""
Test script to verify Genie + Automagik integration without double agent execution
"""

import os
import asyncio
import json
from automagik_tools.tools.genie import ask_genie, genie_memory_stats

async def test_genie_automagik():
    """Test Genie with Automagik MCP configuration"""
    
    print("🧪 Testing Genie + Automagik Integration")
    print("=" * 50)
    
    # Test 1: List agents through Genie
    print("\n📋 Test 1: Listing agents through Genie...")
    result = await ask_genie("list all available agents")
    print(f"Result:\n{result}\n")
    
    # Test 2: Check if raw JSON is returned (markdown disabled)
    print("\n🔍 Test 2: Checking if markdown enhancement is disabled...")
    # The response should contain raw agent data without AI enhancement
    if "```json" in result:
        print("✅ Raw JSON response detected - markdown enhancement is disabled")
    else:
        print("⚠️  Response appears to be enhanced - check AUTOMAGIK_AGENTS_ENABLE_MARKDOWN setting")
    
    # Test 3: Memory stats
    print("\n📊 Test 3: Checking Genie memory stats...")
    stats = await genie_memory_stats()
    print(f"Memory stats:\n{stats}\n")
    
    print("=" * 50)
    print("✅ Tests completed!")

if __name__ == "__main__":
    # Ensure required environment variables are set
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GENIE_AUTOMAGIK_API_KEY": os.getenv("GENIE_AUTOMAGIK_API_KEY"),
        "GENIE_AUTOMAGIK_BASE_URL": os.getenv("GENIE_AUTOMAGIK_BASE_URL")
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these variables or create a .env file with:")
        print("OPENAI_API_KEY=your-openai-key")
        print("GENIE_AUTOMAGIK_API_KEY=your-automagik-key")
        print("GENIE_AUTOMAGIK_BASE_URL=http://your-automagik-url")
        exit(1)
    
    # Run the tests
    asyncio.run(test_genie_automagik())