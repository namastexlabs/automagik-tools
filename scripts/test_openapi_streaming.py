#!/usr/bin/env python3
"""Test the OpenAPI streaming processor"""

import os
import json
from openapi_streaming_processor import StreamingOpenAPIProcessor

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

# Create a minimal OpenAPI spec for testing
test_spec = {
    "info": {
        "title": "Test API",
        "version": "1.0.0"
    },
    "paths": {
        "/users": {
            "get": {
                "operationId": "get_users_api_v1_users_list_get",
                "summary": "Get list of users"
            },
            "post": {
                "operationId": "create_user_api_v1_users_create_post",
                "summary": "Create a new user"
            }
        },
        "/users/{id}": {
            "get": {
                "operationId": "get_user_by_id_api_v1_users__id__get",
                "summary": "Get user by ID"
            }
        }
    }
}

print("Testing OpenAPI Streaming Processor...")
print(f"API Key: {'Set' if api_key else 'Not set'}")
print(f"Operations to process: 3")

# Create processor
processor = StreamingOpenAPIProcessor(model_id="gpt-4.1", api_key=api_key)

# Process with debug mode
try:
    result = processor.process_for_static_generation(
        openapi_spec=test_spec,
        tool_name="Test API",
        base_description="A test API for demonstration",
        debug=True
    )
    
    print("\n\nResult:")
    print(f"Functions processed: {len(result.functions)}")
    for func in result.functions:
        print(f"  - {func.function_name}: {func.tool_description}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()