"""
Enhanced response handler that wraps tool outputs with AI-processed Markdown

This module provides decorators and utilities to enhance MCP tool responses
with AI-generated Markdown summaries and structured formatting.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List
from functools import wraps
import logging
from .json_markdown_processor import (
    ProcessingResult,
    get_processor,
)

logger = logging.getLogger(__name__)


class EnhancedResponse:
    """
    Enhanced response object that contains both raw JSON and AI-processed Markdown
    """

    def __init__(
        self,
        raw_data: Union[Dict[str, Any], List[Any], str, int, float, bool],
        processing_result: Optional[ProcessingResult] = None,
        tool_name: str = "unknown",
    ):
        self.raw_data = raw_data
        self.processing_result = processing_result
        self.tool_name = tool_name

    @property
    def success(self) -> bool:
        """Check if the original operation was successful"""
        if isinstance(self.raw_data, dict):
            # Check common success indicators
            if "success" in self.raw_data:
                return bool(self.raw_data["success"])
            if "error" in self.raw_data:
                return False
            if "detail" in self.raw_data and isinstance(self.raw_data["detail"], str):
                # FastAPI validation errors
                return False
        return True  # Assume success if no clear indicators

    @property
    def markdown(self) -> str:
        """Get the AI-processed Markdown representation"""
        if self.processing_result:
            return self.processing_result.markdown

        # Fallback to formatted JSON
        return f"```json\n{json.dumps(self.raw_data, indent=2)}\n```"

    @property
    def summary(self) -> str:
        """Get a brief summary of the response"""
        if self.processing_result and self.processing_result.success:
            # Extract first line or paragraph as summary
            lines = self.processing_result.markdown.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("```"):
                    return line

        # Fallback summary
        if isinstance(self.raw_data, dict):
            if "message" in self.raw_data:
                return str(self.raw_data["message"])[:100] + "..."
            if self.success:
                return f"✅ {self.tool_name} completed successfully"
            else:
                return f"❌ {self.tool_name} failed"

        return f"Response from {self.tool_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "tool_name": self.tool_name,
            "success": self.success,
            "summary": self.summary,
            "markdown": self.markdown,
            "raw_data": self.raw_data,
        }

        if self.processing_result:
            result["processing_info"] = {
                "success": self.processing_result.success,
                "processing_time": self.processing_result.processing_time,
                "model_used": self.processing_result.model_used,
                "timestamp": self.processing_result.timestamp,
                "error": self.processing_result.error,
            }

        return result

    def __str__(self) -> str:
        """String representation returns the Markdown"""
        return self.markdown

    def __repr__(self) -> str:
        """Developer representation"""
        return f"<EnhancedResponse tool={self.tool_name} success={self.success}>"


def enhance_response(tool_name: str = None):
    """
    Decorator to enhance tool responses with AI-processed Markdown

    Usage:
        @enhance_response("list_agents")
        async def my_tool_function():
            return {"agents": [...]}
    """

    def decorator(func: Callable) -> Callable:
        actual_tool_name = tool_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> EnhancedResponse:
            try:
                # Call the original function
                raw_result = await func(*args, **kwargs)

                # Process with AI
                processor = get_processor()
                processing_result = await processor.process_json(
                    raw_result, actual_tool_name
                )

                return EnhancedResponse(
                    raw_data=raw_result,
                    processing_result=processing_result,
                    tool_name=actual_tool_name,
                )

            except Exception as e:
                logger.error(f"Error enhancing response for {actual_tool_name}: {e}")
                # Return error as enhanced response
                error_data = {"error": str(e), "tool": actual_tool_name}
                return EnhancedResponse(
                    raw_data=error_data,
                    processing_result=None,
                    tool_name=actual_tool_name,
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> EnhancedResponse:
            try:
                # Call the original function
                raw_result = func(*args, **kwargs)

                # Process with AI (sync)
                processor = get_processor()
                processing_result = processor.process_json_sync(
                    raw_result, actual_tool_name
                )

                return EnhancedResponse(
                    raw_data=raw_result,
                    processing_result=processing_result,
                    tool_name=actual_tool_name,
                )

            except Exception as e:
                logger.error(f"Error enhancing response for {actual_tool_name}: {e}")
                # Return error as enhanced response
                error_data = {"error": str(e), "tool": actual_tool_name}
                return EnhancedResponse(
                    raw_data=error_data,
                    processing_result=None,
                    tool_name=actual_tool_name,
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def enhance_existing_response(
    raw_data: Union[Dict[str, Any], List[Any], str, int, float, bool],
    tool_name: str,
    context: Optional[str] = None,
) -> EnhancedResponse:
    """
    Enhance an existing response with AI processing

    Usage:
        enhanced = await enhance_existing_response(api_response, "list_agents")
        print(enhanced.markdown)
    """
    processor = get_processor()
    processing_result = await processor.process_json(raw_data, tool_name, context)

    return EnhancedResponse(
        raw_data=raw_data, processing_result=processing_result, tool_name=tool_name
    )


class ResponseFormatter:
    """Utility class for formatting responses in different ways"""

    @staticmethod
    def to_slack(response: EnhancedResponse) -> Dict[str, Any]:
        """Format response for Slack"""
        color = "good" if response.success else "danger"

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"{response.tool_name} Result",
                    "text": response.summary,
                    "fields": [
                        {
                            "title": "Details",
                            "value": response.markdown[:1000]
                            + ("..." if len(response.markdown) > 1000 else ""),
                            "short": False,
                        }
                    ],
                    "footer": "Automagik Tools",
                    "ts": (
                        response.processing_result.timestamp
                        if response.processing_result
                        else None
                    ),
                }
            ]
        }

    @staticmethod
    def to_discord(response: EnhancedResponse) -> Dict[str, Any]:
        """Format response for Discord"""
        color = 0x00FF00 if response.success else 0xFF0000  # Green or Red

        return {
            "embeds": [
                {
                    "title": f"{response.tool_name} Result",
                    "description": response.summary,
                    "color": color,
                    "fields": [
                        {
                            "name": "Details",
                            "value": response.markdown[:1000]
                            + ("..." if len(response.markdown) > 1000 else ""),
                            "inline": False,
                        }
                    ],
                    "footer": {"text": "Automagik Tools"},
                    "timestamp": (
                        response.processing_result.timestamp
                        if response.processing_result
                        else None
                    ),
                }
            ]
        }

    @staticmethod
    def to_html(response: EnhancedResponse) -> str:
        """Convert response to HTML"""
        import markdown

        # Convert Markdown to HTML
        md = markdown.Markdown(extensions=["tables", "fenced_code"])
        html_content = md.convert(response.markdown)

        status_class = "success" if response.success else "error"

        return f"""
        <div class="automagik-response {status_class}">
            <h2>{response.tool_name} Result</h2>
            <div class="summary">{response.summary}</div>
            <div class="content">
                {html_content}
            </div>
        </div>
        """


# Example usage
if __name__ == "__main__":

    async def test_enhancement():
        """Test the response enhancement system"""

        # Mock tool response
        mock_response = {
            "agents": [
                {"id": 8, "name": "claude-code", "description": "Code analysis agent"},
                {"id": 20, "name": "simple", "description": "General purpose agent"},
            ],
            "total": 2,
            "success": True,
        }

        # Enhance the response
        enhanced = await enhance_existing_response(mock_response, "list_agents")

        print("Enhanced Response:")
        print("=" * 50)
        print(f"Success: {enhanced.success}")
        print(f"Summary: {enhanced.summary}")
        print("\nMarkdown:")
        print(enhanced.markdown)
        print("=" * 50)

        # Test formatting
        slack_format = ResponseFormatter.to_slack(enhanced)
        print(f"Slack format: {slack_format}")

    # Run test
    asyncio.run(test_enhancement())
