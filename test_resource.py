#!/usr/bin/env python3
from fastmcp import FastMCP

# Test 1: Simple resource (should work)
mcp1 = FastMCP("Test1")
@mcp1.resource("config")
async def test1():
    return "test1"

# Test 2: Resource with :// but no params (should fail)
mcp2 = FastMCP("Test2")
try:
    @mcp2.resource("test://config")
    async def test2():
        return "test2"
    print("Test 2: PASSED (unexpected)")
except ValueError as e:
    print(f"Test 2: FAILED as expected - {e}")

# Test 3: Resource with :// and params (should work)
mcp3 = FastMCP("Test3")
@mcp3.resource("test://{param}/config")
async def test3(param: str):
    return f"test3 with {param}"

print("All tests completed")