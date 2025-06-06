#!/usr/bin/env python3
"""
Test script to verify the SSE hanging fix for Genie with Linear MCP server.
This script will simulate the scenario that was causing the ASGI errors.
"""

import asyncio
import httpx
import json
import time
import os

async def test_sse_genie_with_linear():
    """Test the Genie SSE endpoint with Linear MCP server"""
    
    # Configuration - Use the correct SSE endpoint
    base_url = "http://localhost:8885"
    test_message = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "ask_genie",
            "arguments": {
                "query": "hi, can you tell me about yourself?",
                "user_id": "test_user"
            }
        },
        "id": 1
    }
    
    print("🧪 Testing Genie SSE endpoint with Linear MCP server...")
    print(f"📡 Base URL: {base_url}")
    print(f"💬 Test message: {test_message['params']['arguments']['query']}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 Sending test message to SSE endpoint...")
            start_time = time.time()
            
            # Use POST to the root endpoint (/) for FastMCP SSE
            response = await client.post(f"{base_url}/", json=test_message)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"📥 Response received in {duration:.2f} seconds")
            print(f"🔢 Status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✅ Response JSON:")
                    print(json.dumps(result, indent=2))
                    
                    # Check if we got a proper response structure
                    if "result" in result:
                        print("✅ Got proper MCP response structure")
                        return True
                    else:
                        print("⚠️ Response missing 'result' field")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {e}")
                    print(f"Raw response: {response.text[:500]}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("⏰ Request timed out - this might indicate the hanging issue")
        return False
    except httpx.ConnectError:
        print("🔌 Connection failed - is the SSE server running on port 8885?")
        print("💡 Start it with: ./scripts/start_linear_genie_sse.sh")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_multiple_requests():
    """Test multiple consecutive requests to check for hanging"""
    print("\n🔄 Testing multiple consecutive requests...")
    
    success_count = 0
    total_requests = 3
    
    for i in range(total_requests):
        print(f"\n--- Request {i+1}/{total_requests} ---")
        success = await test_sse_genie_with_linear()
        if success:
            success_count += 1
        
        # Small delay between requests
        if i < total_requests - 1:
            print("⏳ Waiting 2 seconds before next request...")
            await asyncio.sleep(2)
    
    print(f"\n📊 Results: {success_count}/{total_requests} requests successful")
    
    if success_count == total_requests:
        print("🎉 All tests passed! SSE hanging issue appears to be fixed.")
    elif success_count > 0:
        print("⚠️ Some tests passed, but there may still be intermittent issues.")
    else:
        print("❌ All tests failed. The hanging issue may persist.")
    
    return success_count == total_requests

def check_server_running():
    """Check if the SSE server is running"""
    print("🔍 Checking if Genie SSE server is running...")
    
    # Check if process is running
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "automagik-tools.*genie.*sse"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Found Genie SSE server process(es): {', '.join(pids)}")
            return True
        else:
            print("❌ Genie SSE server not found")
            return False
            
    except FileNotFoundError:
        print("⚠️ pgrep command not found (non-Unix system?)")
        return None

async def main():
    """Main test function"""
    print("🧞 Genie SSE Hanging Fix Test")
    print("=" * 40)
    
    # Check if server is running
    server_running = check_server_running()
    
    if server_running is False:
        print("\n💡 To start the server, run:")
        print("   cd automagik-tools")
        print("   ./scripts/start_linear_genie_sse.sh")
        print("\nThen run this test again.")
        return
    
    print()
    
    # Run tests
    all_passed = await test_multiple_requests()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 SUCCESS: SSE hanging issue appears to be resolved!")
    else:
        print("❌ FAILURE: Issues detected. Check the logs for details.")
        print("📁 Check logs at: logs/genie_linear_sse.log")

if __name__ == "__main__":
    asyncio.run(main()) 