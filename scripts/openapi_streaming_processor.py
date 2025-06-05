"""
Streaming OpenAPI processor that provides real-time visibility into processing.

This processor uses agno without structured output to enable streaming,
then parses the results into the expected format.
"""

from typing import Dict, List, Any, Optional
from textwrap import dedent
import json
import time
import re

from agno.agent import Agent
from agno.models.openai import OpenAIChat


class StreamingOpenAPIProcessor:
    """Process OpenAPI specs with real-time streaming feedback."""
    
    def __init__(self, model_id: str = "gpt-4.1", api_key: Optional[str] = None):
        """Initialize the processor with specified model."""
        # Don't use response_model to enable streaming
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=api_key),
            description=dedent("""
                You are an OpenAPI-to-MCP Tool Transformer Agent that outputs JSON.
                Transform verbose OpenAPI operations into human-friendly tool definitions.
            """),
            markdown=False,  # We want raw JSON, not markdown
            instructions=dedent("""
                Process OpenAPI operations and output a JSON object with this structure:
                {
                    "functions": [
                        {
                            "operation_id": "original_operation_id",
                            "function_name": "short_name_under_40_chars",
                            "tool_description": "One line description under 100 chars",
                            "category": "category_name",
                            "parameter_descriptions": {
                                "param_name": "Enhanced description"
                            }
                        }
                    ],
                    "function_mappings": {
                        "operation_id": "function_name"
                    },
                    "categories": ["category1", "category2"]
                }
                
                Rules:
                - Function names: max 40 chars, snake_case, start with verbs
                - Descriptions: max 100 chars, focus on action and value
                - Remove redundant prefixes/suffixes from operation IDs
                - Group operations logically into categories
                
                Output ONLY valid JSON, no markdown formatting.
            """)
        )
    
    def process_for_static_generation(
        self, 
        openapi_spec: Dict[str, Any],
        tool_name: str,
        base_description: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Process with streaming feedback."""
        
        # Extract operations
        operations = self._extract_operations(openapi_spec)
        
        print(f"\n[Streaming AI] Processing {len(operations)} operations...")
        print(f"[Streaming AI] Model: {self.agent.model.id}")
        print(f"[Streaming AI] Starting real-time processing...\n")
        
        # Create prompt
        prompt = f"""
        Process these {len(operations)} OpenAPI operations for the "{tool_name}" tool.
        
        Operations:
        {json.dumps(operations, indent=2)}
        
        Transform each operation into a human-friendly function following the rules provided.
        Output only valid JSON.
        """
        
        # Stream the response
        start_time = time.time()
        accumulated_content = ""
        thinking_content = ""
        
        try:
            # Run with streaming enabled
            response_stream = self.agent.run(prompt, stream=True)
            
            # Process each chunk as it arrives
            chunk_count = 0
            for chunk in response_stream:
                chunk_count += 1
                
                if debug and chunk_count <= 5:  # Only show first 5 chunks in debug
                    print(f"\n[DEBUG] Chunk {chunk_count}: type={type(chunk).__name__}", flush=True)
                    if hasattr(chunk, 'content'):
                        print(f"[DEBUG] Content preview: {repr(chunk.content[:50]) if chunk.content else 'None'}", flush=True)
                
                # Check if chunk has content
                if hasattr(chunk, 'content') and chunk.content:
                    new_content = chunk.content
                    accumulated_content += new_content
                    
                    # Show progress based on content
                    if len(new_content) > 0:
                        # Look for specific JSON structures in accumulated content
                        # Check for completed function entries
                        func_matches = re.findall(r'"function_name":\s*"([^"]+)"', accumulated_content)
                        new_func_count = len(func_matches)
                        
                        # Show function names as we discover them
                        if new_func_count > 0 and new_func_count % 5 == 0:
                            print(f"\n[Progress] Processed {new_func_count} functions...", flush=True)
                        
                        # Visual progress indicator
                        if chunk_count % 10 == 0:
                            print("●", end="", flush=True)
                        elif chunk_count % 5 == 0:
                            print("○", end="", flush=True)
                        else:
                            print(".", end="", flush=True)
                
                # Check for thinking
                if hasattr(chunk, 'thinking') and chunk.thinking:
                    thinking_content += chunk.thinking
                    # Only show first line of thinking
                    first_line = chunk.thinking.strip().split('\n')[0]
                    if first_line:
                        print(f"\n[Thinking] {first_line[:80]}...", flush=True)
                
                # Check for tool calls
                if hasattr(chunk, 'tools') and chunk.tools:
                    for tool in chunk.tools:
                        print(f"\n[Tool] {tool}", flush=True)
            
            print()  # New line after dots
            elapsed = time.time() - start_time
            print(f"\n[Streaming AI] Completed in {elapsed:.1f} seconds")
            
            # Show the final accumulated content for debugging
            if accumulated_content:
                print(f"\n[Streaming AI] Final output length: {len(accumulated_content)} characters")
                if len(accumulated_content) < 1000:
                    print(f"[Streaming AI] Output preview:\n{accumulated_content}")
                else:
                    print(f"[Streaming AI] Output preview (first 500 chars):\n{accumulated_content[:500]}...")
                    print(f"[Streaming AI] Output preview (last 500 chars):\n...{accumulated_content[-500:]}")
            
            # Parse the accumulated JSON
            try:
                # Clean up the content - remove any markdown formatting
                json_content = accumulated_content.strip()
                
                # Remove markdown formatting if present
                if json_content.startswith("```json"):
                    json_content = json_content[7:]
                if json_content.endswith("```"):
                    json_content = json_content[:-3]
                json_content = json_content.strip()
                
                result = json.loads(json_content)
                
                print(f"[Streaming AI] Successfully parsed {len(result.get('functions', []))} functions")
                print(f"[Streaming AI] Categories: {', '.join(result.get('categories', []))}")
                
                # Convert to expected format
                from openapi_static_processor import ProcessedOpenAPIFunctions, FunctionInfo
                
                functions = []
                for func_data in result.get('functions', []):
                    # Generate a simple docstring
                    docstring = f'"""\n    {func_data["tool_description"]}\n    """'
                    
                    functions.append(FunctionInfo(
                        operation_id=func_data['operation_id'],
                        function_name=func_data['function_name'],
                        tool_description=func_data['tool_description'],
                        docstring=docstring,
                        category=func_data.get('category', 'general'),
                        parameter_descriptions=func_data.get('parameter_descriptions', {})
                    ))
                
                return ProcessedOpenAPIFunctions(
                    functions=functions,
                    function_mappings=result.get('function_mappings', {}),
                    categories=result.get('categories', []),
                    tool_description=base_description or f"{tool_name} API integration",
                    tool_instructions=f"Use these functions to interact with {tool_name}"
                )
                
            except json.JSONDecodeError as e:
                print(f"[Streaming AI] Failed to parse JSON: {e}")
                print(f"[Streaming AI] Content preview: {accumulated_content[:200]}...")
                raise
                
        except Exception as e:
            print(f"[Streaming AI] Error: {str(e)}")
            raise
    
    def _extract_operations(self, openapi_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from OpenAPI spec."""
        operations = []
        
        for path, path_item in openapi_spec.get("paths", {}).items():
            for method in ['get', 'post', 'put', 'patch', 'delete']:
                if method in path_item:
                    operation = path_item[method]
                    operations.append({
                        "operationId": operation.get('operationId', f"{method}_{path}"),
                        "method": method.upper(),
                        "path": path,
                        "summary": operation.get('summary', ''),
                        "description": operation.get('description', ''),
                        "tags": operation.get('tags', [])
                    })
        
        return operations