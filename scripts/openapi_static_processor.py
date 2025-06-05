"""
AI-powered OpenAPI processor for static tool generation.

This module processes OpenAPI specifications to generate human-friendly
function names and descriptions for static Python code generation.
"""

from typing import Dict, List, Any, Optional, Tuple
from textwrap import dedent
import json
import re

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field


class FunctionInfo(BaseModel):
    """Information for a single generated function."""
    
    operation_id: str = Field(
        ...,
        description="The original operationId from OpenAPI spec"
    )
    
    function_name: str = Field(
        ...,
        description="Python function name (snake_case, max 40 chars). Examples: 'create_user', 'get_messages', 'update_config'"
    )
    
    tool_description: str = Field(
        ...,
        description="MCP tool description for the function (one line, max 100 chars). Focus on what it does and why."
    )
    
    docstring: str = Field(
        ...,
        description="Full Python docstring for the function including description, args, and returns sections"
    )
    
    category: str = Field(
        ...,
        description="Category for grouping related functions. Examples: 'user_management', 'messaging', 'configuration'"
    )
    
    parameter_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Enhanced descriptions for each parameter (param_name -> description)"
    )


class ProcessedOpenAPIFunctions(BaseModel):
    """Complete processed output for static code generation."""
    
    functions: List[FunctionInfo] = Field(
        ...,
        description="List of all processed functions with enhanced naming and documentation"
    )
    
    function_mappings: Dict[str, str] = Field(
        ...,
        description="Mapping of operationId to function_name for easy lookup"
    )
    
    categories: List[str] = Field(
        ...,
        description="List of discovered categories for organizing functions"
    )
    
    tool_description: str = Field(
        ...,
        description="Overall description for the entire tool (one paragraph)"
    )
    
    tool_instructions: str = Field(
        ...,
        description="Usage instructions for the MCP tool"
    )


class StaticOpenAPIProcessor:
    """Process OpenAPI specs for static Python code generation."""
    
    def __init__(self, model_id: str = "gpt-4.1", api_key: Optional[str] = None):
        """Initialize the processor with specified model."""
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=api_key),
            description=dedent("""
                # Role & Objective
                You are a Python Code Generation Agent specializing in transforming OpenAPI specifications
                into beautiful, production-ready Python code for MCP tools. You create code that is not
                just functional, but a pleasure to read and use.
                
                # Core Competencies
                - Master of Pythonic code patterns and PEP 8 compliance
                - Expert in creating comprehensive Google-style docstrings
                - Skilled at translating REST APIs into intuitive Python interfaces
                - Experienced in organizing large codebases into logical modules
            """),
            instructions=dedent("""
                # Agent Reminders
                - You are an agent—keep processing until all operations are transformed into Python functions
                - If uncertain about parameter types or behaviors, use the OpenAPI spec as the source of truth
                - Plan the overall code structure before generating individual functions
                
                # Instructions
                
                ## 1. Function Naming Standards
                - Maximum 40 characters, strictly snake_case
                - Action verb prefixes based on HTTP method:
                  - GET (single): get_<resource>
                  - GET (collection): list_<resources>
                  - POST: create_<resource> or <action>_<resource>
                  - PUT/PATCH: update_<resource>
                  - DELETE: delete_<resource> or remove_<resource>
                - Special patterns:
                  - Searches: search_<resources>
                  - Actions: <verb>_<resource> (e.g., approve_request, send_notification)
                - Examples:
                  - GET /users/{id} → get_user
                  - GET /users → list_users
                  - POST /users/{id}/activate → activate_user
                
                ## 2. MCP Tool Descriptions
                - Maximum 100 characters
                - Structure: <Action> <what> [<key benefit>]
                - Use present tense, active voice
                - Examples:
                  - "Retrieve user profile with complete details including preferences"
                  - "Send notification to multiple recipients with delivery tracking"
                  - "Generate analytics report for specified date range"
                
                ## 3. Docstring Requirements
                ```python
                def function_name(param1: str, param2: int = 10) -> Dict[str, Any]:
                    \"\"\"Brief one-line description of what the function does.
                    
                    Longer description if needed, explaining important details,
                    business logic, or special behaviors.
                    
                    Args:
                        param1: Clear description of parameter purpose and format
                        param2: Description including valid range (1-100, default: 10)
                        
                    Returns:
                        Dict containing:
                        - key1: Description of this field
                        - key2: Description of this field
                        
                    Raises:
                        ValueError: When param1 is empty
                        APIError: When the API request fails
                        
                    Example:
                        >>> result = function_name("test", param2=20)
                        >>> print(result['status'])
                        'success'
                    \"\"\"
                ```
                
                ## 4. Category Organization
                - Group by business domain, not technical implementation
                - Standard categories with descriptions:
                  - authentication: User login, logout, token management
                  - user_management: User CRUD and profile operations  
                  - messaging: Notifications, emails, chat features
                  - workflow: Automation, pipelines, batch operations
                  - analytics: Reports, metrics, data analysis
                  - configuration: Settings, preferences, system config
                  - monitoring: Health, logs, performance metrics
                
                ## 5. Parameter Documentation
                - Every parameter must have a description
                - Include ALL of the following when applicable:
                  - Purpose and expected format
                  - Valid values or ranges  
                  - Default values
                  - Examples for complex formats
                - Template: "<purpose> (<constraints>, default: <value>)"
                - Examples:
                  - "User's email address (must be valid email format)"
                  - "Page size for results (1-100, default: 20)"
                  - "ISO 8601 timestamp (e.g., '2024-01-01T00:00:00Z')"
                
                ## 6. Code Quality Standards
                - Type hints for ALL parameters and return values
                - Use Optional[T] for nullable parameters
                - Import all types at module level
                - Consistent error handling patterns
                - Follow Python naming conventions strictly
                
                # Reasoning Steps
                <thinking>
                1. Analyze the API structure to identify resource patterns
                2. Determine the primary business domains and categories
                3. Create a naming convention mapping for this specific API
                4. For each operation:
                   a. Identify the resource and action
                   b. Generate a Pythonic function name
                   c. Create comprehensive documentation
                   d. Enhance all parameter descriptions
                   e. Write a complete docstring with examples
                5. Review all functions for consistency and completeness
                </thinking>
                
                # Output Format
                Generate a ProcessedOpenAPIFunctions object containing:
                - functions: List of FunctionInfo objects with all fields populated
                - function_mappings: Complete operationId to function_name mapping
                - categories: Organized list of categories used
                - tool_description: Overall tool description (one paragraph)
                - tool_instructions: Clear usage instructions for developers
                
                # Examples
                
                ## Example 1: User Management Function
                Input:
                ```json
                {
                  "operationId": "get_user_by_id_api_v1_users__user_id__get",
                  "method": "GET",
                  "path": "/api/v1/users/{user_id}",
                  "summary": "Get user by ID",
                  "parameters": [
                    {"name": "user_id", "in": "path", "required": true, "schema": {"type": "string"}}
                  ]
                }
                ```
                
                Output:
                ```python
                function_name: "get_user"
                tool_description: "Retrieve complete user profile including preferences and settings"
                docstring: \"\"\"Retrieve detailed information for a specific user.
                
                Fetches the user profile including personal information, preferences,
                settings, and associated metadata. Requires appropriate permissions.
                
                Args:
                    user_id: Unique identifier for the user (UUID format)
                    
                Returns:
                    Dict containing:
                    - id: User's unique identifier
                    - email: User's email address
                    - profile: Nested dict with profile information
                    - created_at: Account creation timestamp
                    
                Raises:
                    NotFoundError: When user_id doesn't exist
                    PermissionError: When lacking permission to view user
                    
                Example:
                    >>> user = get_user("123e4567-e89b-12d3-a456-426614174000")
                    >>> print(user['email'])
                    'user@example.com'
                \"\"\"
                category: "user_management"
                parameter_descriptions: {
                    "user_id": "Unique user identifier (UUID format, e.g., '123e4567-e89b-12d3-a456-426614174000')"
                }
                ```
                
                ## Example 2: Batch Operation Function  
                Input:
                ```json
                {
                  "operationId": "batch_send_notifications_api_v1_notifications_batch_post",
                  "method": "POST",
                  "path": "/api/v1/notifications/batch",
                  "summary": "Send notifications to multiple users",
                  "requestBody": {
                    "required": true,
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "object",
                          "properties": {
                            "user_ids": {"type": "array", "items": {"type": "string"}},
                            "message": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                          }
                        }
                      }
                    }
                  }
                }
                ```
                
                Output:
                ```python
                function_name: "send_batch_notifications"
                tool_description: "Send notifications to multiple users with priority and delivery tracking"
                docstring: \"\"\"Send notifications to multiple users in a single batch operation.
                
                Efficiently delivers the same notification to multiple recipients with
                configurable priority levels. Returns delivery status for each recipient.
                
                Args:
                    data: Notification batch configuration containing:
                        - user_ids: List of recipient user IDs
                        - message: Notification message content
                        - priority: Delivery priority level
                        
                Returns:
                    Dict containing:
                    - batch_id: Unique identifier for this batch
                    - total: Total number of notifications queued
                    - status: Overall batch status
                    - results: List of individual delivery results
                    
                Example:
                    >>> result = send_batch_notifications({
                    ...     "user_ids": ["user1", "user2"],
                    ...     "message": "System maintenance at 2 AM",
                    ...     "priority": "high"
                    ... })
                    >>> print(f"Sent {result['total']} notifications")
                    Sent 2 notifications
                \"\"\"
                category: "messaging"
                parameter_descriptions: {
                    "user_ids": "List of recipient user IDs (each must be valid UUID)",
                    "message": "Notification message content (max 500 characters)",
                    "priority": "Delivery priority ('low', 'medium', 'high', default: 'medium')"
                }
                ```
                
                # Edge Case Handling
                - Missing operationId: Generate from HTTP method + path
                - Empty descriptions: Create meaningful ones from path/method
                - Complex nested schemas: Flatten into clear parameter descriptions
                - Path parameters with underscores: Convert to camelCase in function
                - Very long operation lists: Maintain consistency throughout
                - Ambiguous operations: Use path context to disambiguate
                
                # Final Instructions
                First, analyze the entire API to understand its domain and structure.
                Then, create a consistent naming scheme that will work across all operations.
                Finally, generate comprehensive documentation that makes the code self-explanatory.
                Remember: The code you generate will be used by other developers—make it exceptional.
            """),
            response_model=ProcessedOpenAPIFunctions,
        )
    
    def process_for_static_generation(
        self, 
        openapi_spec: Dict[str, Any],
        tool_name: str,
        base_description: Optional[str] = None
    ) -> ProcessedOpenAPIFunctions:
        """
        Process OpenAPI spec for static Python code generation.
        
        Args:
            openapi_spec: The OpenAPI specification
            tool_name: Name of the tool being generated
            base_description: Optional base description for the tool
            
        Returns:
            ProcessedOpenAPIFunctions with all enhanced information
        """
        # Extract operations with full context
        operations = []
        
        for path, path_item in openapi_spec.get("paths", {}).items():
            # Common parameters for the path
            common_params = path_item.get('parameters', [])
            
            for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                if method in path_item:
                    operation = path_item[method]
                    
                    # Merge common parameters
                    all_params = common_params + operation.get('parameters', [])
                    
                    # Extract parameter details
                    param_details = []
                    for param in all_params:
                        param_details.append({
                            "name": param.get('name'),
                            "in": param.get('in'),
                            "required": param.get('required', False),
                            "description": param.get('description', ''),
                            "schema": param.get('schema', {})
                        })
                    
                    # Extract request body info
                    request_body = None
                    if 'requestBody' in operation:
                        content = operation['requestBody'].get('content', {})
                        if 'application/json' in content:
                            schema = content['application/json'].get('schema', {})
                            request_body = {
                                "required": operation['requestBody'].get('required', False),
                                "description": operation['requestBody'].get('description', ''),
                                "schema": schema
                            }
                    
                    operations.append({
                        "operationId": operation.get('operationId', f"{method}_{path.replace('/', '_')}"),
                        "method": method.upper(),
                        "path": path,
                        "summary": operation.get('summary', ''),
                        "description": operation.get('description', ''),
                        "tags": operation.get('tags', []),
                        "parameters": param_details,
                        "requestBody": request_body,
                        "responses": operation.get('responses', {})
                    })
        
        # Create comprehensive prompt following GPT-4.1 guidelines
        api_info = openapi_spec.get('info', {})
        
        prompt = f"""
        # Task Context
        Generate Python function definitions and documentation for a static MCP tool.
        
        # API Information
        - Tool Name: {tool_name}
        - API Title: {api_info.get('title', tool_name)}
        - API Version: {api_info.get('version', '1.0.0')}
        - Description: {base_description or api_info.get('description', 'No description provided')}
        - Total Operations: {len(operations)}
        
        # Operations to Process
        <operations>
        {json.dumps(operations, indent=2)}
        </operations>
        
        # Your Mission
        Transform these {len(operations)} operations into a cohesive Python module with:
        1. Clean, intuitive function names that follow Python conventions
        2. Comprehensive Google-style docstrings with examples
        3. Enhanced parameter descriptions with constraints and defaults
        4. Logical categorization for code organization
        5. Overall tool documentation and usage instructions
        
        # Critical Requirements
        - Every function name must be under 40 characters
        - Every tool description must be under 100 characters  
        - All parameters must have type hints
        - All docstrings must include Args, Returns, and Example sections
        - Group related functions into categories
        
        # Step-by-Step Process
        First, analyze the API structure to identify patterns and resource types.
        Second, create a consistent naming strategy that works for all operations.
        Third, process each operation to generate complete function information.
        Fourth, organize functions into logical categories.
        Finally, create overall tool documentation.
        
        Remember: You're creating code that other developers will use and maintain.
        Make it exceptional—clear, consistent, and a joy to work with.
        """
        
        # Print progress
        print(f"\n[AI Processing] Sending {len(operations)} operations to AI model...")
        print(f"[AI Processing] This may take 30-60 seconds...")
        
        try:
            # Note: Streaming is disabled when using response_model (structured output)
            print(f"[AI Processing] Using structured output mode (streaming disabled)")
            print(f"[AI Processing] Processing {len(operations)} operations into structured format...")
            print(f"[AI Processing] This typically takes 30-60 seconds for large APIs")
            
            # Show a simple progress indicator
            import time
            start_time = time.time()
            
            # Run the agent (blocking call due to response_model)
            response = self.agent.run(prompt)
            
            elapsed = time.time() - start_time
            print(f"[AI Processing] Completed in {elapsed:.1f} seconds")
            print(f"[AI Processing] Successfully processed {len(response.content.functions)} functions")
            print(f"[AI Processing] Categories: {', '.join(response.content.categories)}")
            
            return response.content
                
        except Exception as e:
            print(f"[AI Processing] Error: {str(e)}")
            print(f"[AI Processing] Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_docstring(
        self,
        function_name: str,
        summary: str,
        parameters: List[Dict[str, Any]],
        request_body: Optional[Dict[str, Any]],
        responses: Dict[str, Any]
    ) -> str:
        """
        Generate a comprehensive Python docstring for a function.
        
        This is a helper method that can be used independently.
        """
        prompt = f"""
        Generate a Google-style Python docstring for this function:
        
        Function: {function_name}
        Summary: {summary}
        Parameters: {json.dumps(parameters, indent=2)}
        Request Body: {json.dumps(request_body, indent=2) if request_body else "None"}
        Responses: {json.dumps(responses, indent=2)}
        
        Create a comprehensive docstring that includes:
        - Brief description
        - Detailed parameter documentation with types
        - Return value description
        - Usage example if helpful
        - Any important notes or warnings
        """
        
        # Use a simpler agent for docstring generation
        docstring_agent = Agent(
            model=self.agent.model,
            description="You are a Python documentation expert who writes clear, helpful docstrings.",
            instructions="Generate Google-style Python docstrings that are comprehensive yet concise.",
        )
        
        response = docstring_agent.run(prompt)
        return response.content


def sanitize_python_name(name: str, max_length: int = 40) -> str:
    """
    Sanitize a string to be a valid Python function name.
    
    Args:
        name: The name to sanitize
        max_length: Maximum length for the name
        
    Returns:
        Valid Python function name
    """
    # Convert to lowercase and replace non-alphanumeric with underscores
    name = re.sub(r'[^\w]', '_', name.lower())
    
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"op_{name}"
    
    # Truncate if necessary
    if len(name) > max_length:
        name = name[:max_length].rstrip('_')
    
    # Ensure we have a valid name
    if not name:
        name = "operation"
    
    return name


def enhance_parameter_description(
    param_name: str,
    original_desc: str,
    param_schema: Dict[str, Any],
    required: bool
) -> str:
    """
    Enhance a parameter description with type and constraint information.
    
    Args:
        param_name: Name of the parameter
        original_desc: Original description from OpenAPI
        param_schema: Schema definition for the parameter
        required: Whether the parameter is required
        
    Returns:
        Enhanced description string
    """
    desc_parts = []
    
    # Start with original description
    if original_desc:
        desc_parts.append(original_desc)
    
    # Add type information
    param_type = param_schema.get('type', 'string')
    if param_type == 'array':
        items_type = param_schema.get('items', {}).get('type', 'string')
        desc_parts.append(f"(array of {items_type}s)")
    elif param_type != 'string':
        desc_parts.append(f"({param_type})")
    
    # Add constraints
    constraints = []
    if 'enum' in param_schema:
        constraints.append(f"Valid values: {', '.join(map(str, param_schema['enum']))}")
    if 'minimum' in param_schema:
        constraints.append(f"Min: {param_schema['minimum']}")
    if 'maximum' in param_schema:
        constraints.append(f"Max: {param_schema['maximum']}")
    if 'minLength' in param_schema:
        constraints.append(f"Min length: {param_schema['minLength']}")
    if 'maxLength' in param_schema:
        constraints.append(f"Max length: {param_schema['maxLength']}")
    if 'pattern' in param_schema:
        constraints.append(f"Pattern: {param_schema['pattern']}")
    
    if constraints:
        desc_parts.append(f"[{'; '.join(constraints)}]")
    
    # Add required/optional
    if not required:
        desc_parts.append("(optional)")
    
    return ' '.join(desc_parts).strip()


if __name__ == "__main__":
    # Example usage
    import os
    import httpx
    
    api_key = os.getenv("OPENAI_API_KEY")
    processor = StaticOpenAPIProcessor(api_key=api_key)
    
    # Example: Process an OpenAPI spec
    openapi_url = "https://api.example.com/openapi.json"
    
    try:
        response = httpx.get(openapi_url)
        response.raise_for_status()
        spec = response.json()
        
        result = processor.process_for_static_generation(
            openapi_spec=spec,
            tool_name="Example API",
            base_description="A comprehensive API integration tool"
        )
        
        print("Generated Function Mappings:")
        for op_id, func_name in result.function_mappings.items():
            print(f"  {op_id} -> {func_name}")
            
    except Exception as e:
        print(f"Error: {e}")