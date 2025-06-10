"""
AI-powered OpenAPI processor for generating human-friendly MCP tool names and descriptions.

This module uses structured output agents to transform complex OpenAPI specifications
into well-formatted, concise tool definitions for MCP.
"""

from typing import Dict, List, Any, Optional
from textwrap import dedent
import json

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field


class ToolInfo(BaseModel):
    """Structured information for a single MCP tool."""

    operation_id: str = Field(
        ..., description="The original operationId from OpenAPI spec"
    )

    tool_name: str = Field(
        ...,
        description="Short, descriptive name for MCP (max 40 chars). Use underscores for spaces. Examples: 'create_user', 'get_status', 'run_workflow'",
    )

    description: str = Field(
        ...,
        description="Clear, concise one-line description of what this tool does (max 80 chars). Focus on the action and purpose.",
    )

    category: str = Field(
        ...,
        description="Tool category for logical grouping. Examples: 'user_management', 'workflow', 'monitoring', 'configuration'",
    )

    human_readable_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of parameter names to human-friendly descriptions. Only include non-obvious parameters.",
    )


class ProcessedOpenAPITools(BaseModel):
    """Complete structured output for all tools in an OpenAPI spec."""

    tools: List[ToolInfo] = Field(
        ...,
        description="List of all processed tools with human-friendly names and descriptions",
    )

    name_mappings: Dict[str, str] = Field(
        ...,
        description="Direct mapping of operationId to tool_name for FastMCP integration",
    )

    categories: List[str] = Field(
        ..., description="List of unique categories discovered in the tools"
    )


class OpenAPIProcessor:
    """Agent-based processor for converting OpenAPI specs to human-friendly MCP tools."""

    def __init__(self, model_id: str = "gpt-4.1", api_key: Optional[str] = None):
        """Initialize the OpenAPI processor with the specified model."""
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=api_key),
            description=dedent(
                """
                # Role & Objective
                You are an OpenAPI-to-MCP Tool Transformer Agent. Your mission is to transform verbose, 
                auto-generated OpenAPI operation IDs and descriptions into human-friendly MCP tool 
                definitions that developers will love to use.
                
                # Core Competencies
                - Expert in REST API design patterns and conventions
                - Master of creating intuitive, self-documenting function names
                - Skilled at writing concise, actionable descriptions
                - Experienced in categorizing and organizing large API surfaces
            """
            ),
            instructions=dedent(
                """
                # Agent Reminders
                - You are an agent—keep going until all operations are fully processed
                - Never guess or make assumptions about functionality—base everything on the provided OpenAPI spec
                - Plan your naming strategy before processing to ensure consistency across all operations
                
                # Instructions
                
                ## 1. Tool Naming Rules
                - Maximum 40 characters, use snake_case
                - Start with action verbs: get_, list_, create_, update_, delete_, run_, start_, stop_
                - Remove redundant prefixes: api_v1_, api_v2_, endpoint_, route_, _endpoint, _route
                - Remove HTTP method suffixes: _get, _post, _put, _delete, _patch
                - Extract meaningful parts before double underscores (path parameters)
                - Examples:
                  - BAD: get_user_profile_api_v1_users__user_id__profile_get
                  - GOOD: get_user_profile
                
                ## 2. Description Writing
                - Maximum 80 characters per description
                - Focus on business value and action, not technical details
                - Use active voice and present tense
                - Don't repeat the function name
                - Examples:
                  - BAD: "This function gets the user profile"
                  - GOOD: "Retrieve detailed profile information for a specific user"
                
                ## 3. Categorization Strategy
                - Group operations by resource or functional area
                - Use lowercase with underscores for category names
                - Standard categories:
                  - authentication: Login, logout, token management
                  - user_management: User CRUD operations
                  - messaging: Communication features
                  - workflow: Process automation and pipelines
                  - monitoring: Health checks, metrics, logs
                  - configuration: Settings and preferences
                  - data_access: Reports, exports, queries
                
                ## 4. Parameter Enhancement
                - Enhance descriptions for all non-obvious parameters
                - Include format specifications and constraints
                - Mention default values if applicable
                - Example:
                  - Original: "limit"
                  - Enhanced: "Maximum items to return (1-1000, default: 100)"
                
                # Reasoning Steps
                <thinking>
                1. First, analyze all operations to identify patterns and resource groups
                2. Determine consistent naming conventions based on the API's domain
                3. Group operations into logical categories
                4. For each operation:
                   a. Extract the core action and resource
                   b. Create a concise, meaningful function name
                   c. Write a value-focused description
                   d. Enhance parameter documentation
                5. Review all names for consistency and clarity
                </thinking>
                
                # Output Format
                Your response must be a valid ProcessedOpenAPITools object with:
                - tools: List of ToolInfo objects
                - name_mappings: Dict mapping operationId to tool_name
                - categories: List of unique category strings
                
                # Examples
                
                ## Example 1: User Session Messages
                Input:
                - operationId: "get_user_session_messages_api_v1_users__user_id__sessions__session_id__messages_get"
                - path: "/api/v1/users/{user_id}/sessions/{session_id}/messages"
                - method: "GET"
                - summary: "Get messages for a user session"
                
                Output:
                - tool_name: "get_messages"
                - description: "Retrieve conversation messages from a specific user session"
                - category: "messaging"
                - parameter_descriptions: {
                    "user_id": "Unique identifier of the user",
                    "session_id": "Session ID for the conversation",
                    "limit": "Maximum messages to retrieve (1-1000, default: 100)"
                  }
                
                ## Example 2: Workflow Execution
                Input:
                - operationId: "run_claude_code_workflow_api_v1_agent_claude_code__workflow_name__run_post"
                - path: "/api/v1/agent/claude-code/{workflow_name}/run"
                - method: "POST"
                - summary: "Run a Claude Code workflow"
                
                Output:
                - tool_name: "run_workflow"
                - description: "Execute an automated workflow with optional parameters"
                - category: "workflow"
                - parameter_descriptions: {
                    "workflow_name": "Name of the workflow to execute (e.g., 'data-analysis')",
                    "parameters": "Workflow-specific configuration parameters",
                    "timeout": "Maximum execution time in seconds (optional)"
                  }
                
                # Edge Cases
                - If operationId is missing, generate from method + path
                - If description is empty, create from path and method
                - If parameters lack descriptions, infer from name and type
                - For very long operations lists (>100), maintain consistency throughout
                - Handle special characters in paths by converting to underscores
                
                # Final Instruction
                First, think step-by-step about the naming patterns and categories needed for this API.
                Then, process each operation systematically to create a cohesive, well-organized tool set.
                Ensure every tool name is intuitive and every description adds value.
            """
            ),
            response_model=ProcessedOpenAPITools,
        )

    def process_openapi_spec(
        self, openapi_spec: Dict[str, Any]
    ) -> ProcessedOpenAPITools:
        """
        Process an OpenAPI specification and generate human-friendly tool definitions.

        Args:
            openapi_spec: The complete OpenAPI specification dictionary

        Returns:
            ProcessedOpenAPITools with all tools properly named and described
        """
        # Extract relevant operation information
        operations = []

        for path, path_item in openapi_spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.lower() in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                ]:
                    operation_id = operation.get("operationId")
                    if operation_id:
                        operations.append(
                            {
                                "operationId": operation_id,
                                "method": method.upper(),
                                "path": path,
                                "summary": operation.get("summary", ""),
                                "description": operation.get("description", ""),
                                "parameters": operation.get("parameters", []),
                                "requestBody": operation.get("requestBody", {}),
                                "tags": operation.get("tags", []),
                            }
                        )

        # Create a structured prompt following GPT-4.1 guidelines
        prompt = f"""
        # Task Context
        You are processing an OpenAPI specification with {len(operations)} operations.
        
        # API Information
        - Title: {openapi_spec.get('info', {}).get('title', 'Unknown API')}
        - Description: {openapi_spec.get('info', {}).get('description', 'No description')}
        - Version: {openapi_spec.get('info', {}).get('version', '1.0.0')}
        
        # Operations Data
        <operations>
        {json.dumps(operations, indent=2)}
        </operations>
        
        # Your Task
        Transform each operation into a human-friendly MCP tool following the instructions provided.
        
        # Step-by-Step Process
        First, analyze all operations to identify naming patterns and logical groupings.
        Then, process each operation to create consistent, intuitive tool definitions.
        Finally, ensure all tool names are under 40 characters and descriptions under 80 characters.
        """

        # Use the agent to process the operations
        response = self.agent.run(prompt)
        return response.content

    def process_single_operation(
        self,
        operation_id: str,
        method: str,
        path: str,
        operation_details: Dict[str, Any],
    ) -> ToolInfo:
        """
        Process a single API operation into a tool definition.

        This is useful for incremental processing or testing.
        """
        prompt = f"""
        Convert this single API operation into a human-friendly MCP tool:
        
        Operation ID: {operation_id}
        Method: {method}
        Path: {path}
        Summary: {operation_details.get('summary', 'No summary')}
        Description: {operation_details.get('description', 'No description')}
        Tags: {operation_details.get('tags', [])}
        
        Create a concise tool name and description that clearly explains what this operation does.
        """

        # Use a modified agent for single tool processing
        single_tool_agent = Agent(
            model=self.agent.model,
            description=self.agent.description,
            instructions=self.agent.instructions,
            response_model=ToolInfo,
        )

        response = single_tool_agent.run(prompt)
        return response.content


def create_intelligent_name_mappings(
    openapi_url: str, model_id: str = "gpt-4.1", api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience function to fetch an OpenAPI spec and generate name mappings.

    Args:
        openapi_url: URL to fetch the OpenAPI specification
        model_id: OpenAI model to use for processing
        api_key: Optional API key for OpenAI

    Returns:
        Dictionary mapping operationId to human-friendly tool names
    """
    import httpx

    try:
        # Fetch the OpenAPI spec
        response = httpx.get(openapi_url, timeout=30)
        response.raise_for_status()
        openapi_spec = response.json()

        # Process with the agent
        processor = OpenAPIProcessor(model_id=model_id, api_key=api_key)
        result = processor.process_openapi_spec(openapi_spec)

        return result.name_mappings

    except Exception as e:
        print(f"Error processing OpenAPI spec: {e}")
        return {}


if __name__ == "__main__":
    # Example usage
    import os

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")

    # Example OpenAPI URL
    openapi_url = "http://192.168.112.148:8881/api/v1/openapi.json"

    # Generate intelligent name mappings
    mappings = create_intelligent_name_mappings(
        openapi_url=openapi_url, api_key=api_key
    )

    print("Generated name mappings:")
    for op_id, name in mappings.items():
        print(f"  {op_id} -> {name}")
