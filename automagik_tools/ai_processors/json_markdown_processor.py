"""
AI-powered JSON to Markdown processor using GPT-4.1-nano

This module processes noisy JSON outputs from MCP tools and converts them
into clean, structured Markdown for better human readability.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import openai
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import logging

# Configure logging
logger = logging.getLogger(__name__)


class JsonMarkdownConfig(BaseSettings):
    """Configuration for JSON-to-Markdown processing"""

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT-4.1-nano",
        alias="OPENAI_API_KEY",
    )

    model_name: str = Field(
        default="gpt-4.1-nano",
        description="OpenAI model to use for processing",
        alias="JSON_PROCESSOR_MODEL",
    )

    max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for AI response",
        alias="JSON_PROCESSOR_MAX_TOKENS",
    )

    temperature: float = Field(
        default=0.1,
        description="Temperature for AI responses (lower = more focused)",
        alias="JSON_PROCESSOR_TEMPERATURE",
    )

    enable_processing: bool = Field(
        default=True,
        description="Enable/disable AI processing",
        alias="ENABLE_JSON_PROCESSING",
    )

    debug_mode: bool = Field(
        default=False,
        description="Enable debug logging and raw output preservation",
        alias="JSON_PROCESSOR_DEBUG",
    )

    model_config = {
        "env_prefix": "JSON_PROCESSOR_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


class ProcessingResult(BaseModel):
    """Result of JSON-to-Markdown processing"""

    success: bool = Field(description="Whether processing was successful")
    markdown: str = Field(description="Generated Markdown content")
    raw_json: Union[Dict[str, Any], List[Any], str, int, float, bool] = Field(
        description="Original JSON data"
    )
    processing_time: float = Field(description="Time taken to process (seconds)")
    model_used: str = Field(description="AI model used for processing")
    error: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class JsonMarkdownProcessor:
    """AI-powered processor for converting JSON to structured Markdown"""

    def __init__(self, config: Optional[JsonMarkdownConfig] = None):
        self.config = config or JsonMarkdownConfig()
        self.client = None

        if self.config.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
        else:
            logger.warning(
                "No OpenAI API key provided. JSON processing will be disabled."
            )

    def _detect_error_response(
        self, json_data: Union[Dict[str, Any], List[Any], str, int, float, bool]
    ) -> bool:
        """Detect if the JSON response indicates an error condition"""
        if not isinstance(json_data, dict):
            return False

        # Check for explicit error indicators
        error_indicators = [
            json_data.get("error") is not None,
            json_data.get("detail") is not None,
            json_data.get("message", "").lower().find("error") != -1,
            json_data.get("status") in ["error", "failed", "failure"],
            isinstance(json_data.get("success"), bool) and not json_data["success"],
            json_data.get("status_code", 0) >= 400,
            "exception" in str(json_data).lower(),
            "traceback" in str(json_data).lower(),
        ]

        return any(error_indicators)

    def _has_complex_structure(
        self, json_data: Union[Dict[str, Any], List[Any], str, int, float, bool]
    ) -> bool:
        """Determine if the JSON has complex nested structures"""
        if isinstance(json_data, dict):
            # Check for nested objects, arrays, or large number of keys
            return (
                len(json_data) > 10  # Many top-level keys
                or any(
                    isinstance(v, (dict, list)) for v in json_data.values()
                )  # Nested structures
                or any(
                    isinstance(v, list) and len(v) > 5 for v in json_data.values()
                )  # Large arrays
            )
        elif isinstance(json_data, list):
            return len(json_data) > 5 or any(
                isinstance(item, (dict, list)) for item in json_data
            )

        return False

    def _get_processing_prompt(self, tool_name: str, json_data: Dict[str, Any]) -> str:
        """Generate a concise processing prompt for informative responses"""

        # Detect response characteristics
        is_error = self._detect_error_response(json_data)

        # Minimal, focused prompt
        base_prompt = """Transform this JSON response into concise, informative Markdown.

# Output Requirements:
- Be extremely concise and token-efficient
- Focus only on essential information
- Use minimal formatting and sections
- Avoid verbose explanations or preambles

For successful responses:
- List key data in simple format
- Highlight only critical information
- Omit technical details unless essential

For errors:
- State error clearly and briefly
- Provide only essential fix steps

# Format:
Use simple headings and bullet points. Keep total output under 200 tokens when possible."""

        # Simple tool-specific guidance
        if tool_name == "list_agents":
            context = (
                "For agent lists: show agent names, IDs, and brief descriptions only."
            )
        elif "error" in tool_name.lower() or is_error:
            context = "For errors: state the problem and solution briefly."
        else:
            context = "Show key results concisely."

        # Final assembly with JSON data
        final_prompt = f"""{base_prompt}

{context}

# JSON Data:
```json
{json.dumps(json_data, indent=2)}
```

Transform this into minimal, informative Markdown."""

        return final_prompt

    async def process_json(
        self,
        json_data: Union[Dict[str, Any], List[Any], str, int, float, bool],
        tool_name: str = "unknown",
        context: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Process JSON data and convert to structured Markdown

        Args:
            json_data: The JSON data to process (dict, list, or other JSON-serializable type)
            tool_name: Name of the tool that generated this data
            context: Additional context for processing

        Returns:
            ProcessingResult with success status and generated Markdown
        """
        start_time = asyncio.get_event_loop().time()

        # If processing is disabled, return formatted JSON
        if not self.config.enable_processing or not self.client:
            markdown = f"```json\n{json.dumps(json_data, indent=2)}\n```"
            return ProcessingResult(
                success=True,
                markdown=markdown,
                raw_json=json_data,
                processing_time=0.0,
                model_used="none",
                error="Processing disabled or no API key",
            )

        try:
            # Detect if this is an error response
            is_error = isinstance(json_data, dict) and (
                "error" in json_data
                or "detail" in json_data
                or (
                    isinstance(json_data.get("success"), bool)
                    and not json_data["success"]
                )
            )

            actual_tool_name = "error_response" if is_error else tool_name

            # Generate processing prompt
            prompt = self._get_processing_prompt(actual_tool_name, json_data)

            if context:
                prompt += f"\n\nAdditional Context: {context}"

            # Call GPT-4.1-nano for processing
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an Elite API Response Interpreter. Follow the provided instructions exactly and literally. Your responses must strictly adhere to the specified format and structure. Generate comprehensive, actionable Markdown that serves both end users and developers. Think step-by-step through your analysis before producing the final output.""",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Extract generated Markdown
            markdown = response.choices[0].message.content.strip()
            processing_time = asyncio.get_event_loop().time() - start_time

            # Add processing time footer to all responses
            processing_time_ms = int(processing_time * 1000)
            time_footer = f"\n\n---\n*Generated in {processing_time_ms}ms*"
            markdown += time_footer

            # Add debug information if enabled
            if self.config.debug_mode:
                debug_section = f"""
---

<details>
<summary>🔧 Debug Information</summary>

**Tool:** `{tool_name}`  
**Processing Time:** {processing_time:.2f}s  
**Model:** {self.config.model_name}  
**Timestamp:** {datetime.now().isoformat()}

**Raw JSON:**
```json
{json.dumps(json_data, indent=2)}
```
</details>
"""
                markdown += debug_section

            return ProcessingResult(
                success=True,
                markdown=markdown,
                raw_json=json_data,
                processing_time=processing_time,
                model_used=self.config.model_name,
            )

        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"AI processing failed: {str(e)}"

            logger.error(f"JSON processing error for tool '{tool_name}': {error_msg}")

            # Fallback to formatted JSON
            fallback_markdown = f"""## ⚠️ Processing Error

The AI processor encountered an error. Here's the raw response:

```json
{json.dumps(json_data, indent=2)}
```

**Error:** {error_msg}
"""

            return ProcessingResult(
                success=False,
                markdown=fallback_markdown,
                raw_json=json_data,
                processing_time=processing_time,
                model_used=self.config.model_name,
                error=error_msg,
            )

    async def process_multiple(
        self, data_list: List[Dict[str, Any]], tool_name: str = "batch_operation"
    ) -> List[ProcessingResult]:
        """Process multiple JSON responses concurrently"""

        tasks = [
            self.process_json(
                data, f"{tool_name}_{i}", f"Item {i+1} of {len(data_list)}"
            )
            for i, data in enumerate(data_list)
        ]

        return await asyncio.gather(*tasks)

    def process_json_sync(
        self,
        json_data: Dict[str, Any],
        tool_name: str = "unknown",
        context: Optional[str] = None,
    ) -> ProcessingResult:
        """Synchronous wrapper for process_json"""
        return asyncio.run(self.process_json(json_data, tool_name, context))


# Global processor instance
_global_processor: Optional[JsonMarkdownProcessor] = None


def get_processor() -> JsonMarkdownProcessor:
    """Get or create the global JSON processor instance"""
    global _global_processor
    if _global_processor is None:
        _global_processor = JsonMarkdownProcessor()
    return _global_processor


async def process_tool_output(
    json_data: Dict[str, Any], tool_name: str = "unknown", context: Optional[str] = None
) -> ProcessingResult:
    """
    Convenience function to process tool output with the global processor

    Usage:
        result = await process_tool_output(response_data, "list_agents")
        print(result.markdown)
    """
    processor = get_processor()
    return await processor.process_json(json_data, tool_name, context)


# Example usage and testing
if __name__ == "__main__":

    async def test_processor():
        """Test the JSON-to-Markdown processor"""

        # Test data
        test_data = {
            "agents": [
                {
                    "id": 8,
                    "name": "claude-code",
                    "description": "Advanced code analysis",
                },
                {"id": 20, "name": "simple", "description": "General purpose agent"},
            ],
            "total": 2,
            "timestamp": "2025-06-05T22:53:00Z",
        }

        processor = JsonMarkdownProcessor()
        result = await processor.process_json(test_data, "list_agents")

        print("Generated Markdown:")
        print("=" * 50)
        print(result.markdown)
        print("=" * 50)
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Success: {result.success}")

    # Run test
    asyncio.run(test_processor())
