# Gemini Assistant Tool

Advanced Gemini consultation tool with session management and file attachments for complex coding problems.

## Overview

The Gemini Assistant tool allows Claude Code to consult Google's Gemini models for complex coding problems with full code context, file attachments, and conversation persistence across multiple queries.

## Features

- **Session Management**: Maintain conversation context across multiple queries
- **File Attachments**: Upload and include actual code files in conversations
- **Hybrid Context**: Combine text-based code context with file attachments
- **Follow-up Questions**: Ask follow-up questions without resending code context
- **Context Caching**: Code context and file content are cached per session
- **Multiple Sessions**: Run multiple parallel conversations for different problems
- **Session Expiry**: Automatic cleanup of inactive sessions after configurable timeout
- **Request Tracking**: Track file requests and search queries from Gemini responses

## Configuration

Set these environment variables in your `.env` file:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
GEMINI_MODEL=gemini-2.0-flash-exp           # Default model
GEMINI_SESSION_TIMEOUT=3600                 # Session timeout in seconds (1 hour)
GEMINI_MAX_TOKENS=8192                      # Maximum tokens per response
GEMINI_TEMPERATURE=0.2                      # Temperature for response generation
GEMINI_MAX_SESSIONS=10                      # Maximum concurrent sessions
```

## Available Tools

### `consult_gemini`
Start or continue a conversation with Gemini about complex coding problems.

**Parameters:**
- `specific_question` (required): The specific question you want answered
- `session_id` (optional): Continue a previous conversation
- `problem_description`: Description of the problem (required for new sessions)
- `code_context`: All relevant code (required for new sessions, cached afterward)
- `attached_files` (optional): Array of file paths to upload and include
- `file_descriptions` (optional): Object mapping file paths to descriptions
- `additional_context` (optional): Updates or changes since last question
- `preferred_approach`: Type of help needed (solution/review/debug/optimize/explain/follow-up)

### `list_sessions`
List all active Gemini consultation sessions with details.

### `end_session`
End a specific session to free up memory and clean up uploaded files.

**Parameters:**
- `session_id` (required): The session ID to end

### `get_gemini_requests`
Get the files and searches that Gemini has requested in a session.

**Parameters:**
- `session_id` (required): The session ID to check

## Usage Examples

### Starting a New Conversation (with text code)
```
consult_gemini(
  problem_description="I need to implement efficient caching for a React application",
  code_context="[paste entire relevant codebase]",
  specific_question="What's the best approach for implementing LRU cache with React Query?",
  preferred_approach="solution"
)
```

### Starting a New Conversation (with file attachments)
```
consult_gemini(
  problem_description="I need to optimize this React component for performance",
  attached_files=["/path/to/src/components/Dashboard.jsx", "/path/to/src/hooks/useData.js"],
  file_descriptions={
    "/path/to/src/components/Dashboard.jsx": "Main dashboard component with performance issues",
    "/path/to/src/hooks/useData.js": "Custom hook for data fetching"
  },
  specific_question="How can I improve the rendering performance of this dashboard?",
  preferred_approach="optimize"
)
```

### Follow-up Question
```
consult_gemini(
  session_id="abc123...",
  specific_question="I implemented your suggestion but getting stale data issues. How do I handle cache invalidation?",
  additional_context="Added the LRU cache as suggested, but users see old data after updates",
  preferred_approach="follow-up"
)
```

## Best Practices

1. **Initial Context**: Include ALL relevant code via `code_context` or `attached_files`
2. **File Organization**: Use `attached_files` for multiple files, `code_context` for snippets
3. **File Descriptions**: Provide clear descriptions for each attached file
4. **Follow-ups**: Use the session ID to continue conversations
5. **Additional Context**: When asking follow-ups, explain what changed
6. **Session Management**: End sessions when done to free memory and clean up files
7. **Multiple Problems**: Use different sessions for unrelated problems
8. **File Types**: Supports JavaScript, Python, TypeScript, JSON, and other text-based files

## System Prompt

The tool uses a sophisticated system prompt that positions Gemini as a technical advisor helping Claude solve complex programming problems through thoughtful analysis and genuine technical dialogue. The prompt encourages:

- Deep analysis and architectural insights
- Thoughtful discussions about implementation approaches
- Clarifying questions to understand requirements fully
- Constructive challenges to assumptions
- Context from comprehensive code analysis
- Alternative solutions with clear trade-offs

## Session Management

- Sessions automatically expire after the configured timeout (default: 1 hour)
- Uploaded files are automatically cleaned up when sessions expire
- Rate limiting prevents API abuse (1 second between requests)
- Session limits prevent resource exhaustion

## MCP Configuration

Add this to your `.mcp.json` file for Claude Desktop or Cursor:

```json
{
  "mcpServers": {
    "gemini-assistant": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "tool", 
        "gemini-assistant"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-2.0-flash-exp",
        "GEMINI_SESSION_TIMEOUT": "3600",
        "GEMINI_MAX_TOKENS": "8192",
        "GEMINI_TEMPERATURE": "0.2",
        "GEMINI_MAX_SESSIONS": "10"
      }
    }
  }
}
```

**Minimal Configuration (just the API key):**
```json
{
  "mcpServers": {
    "gemini-assistant": {
      "command": "uvx", 
      "args": ["automagik-tools@latest", "tool", "gemini-assistant"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

## Quick Start

1. **Get your Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **Add to your `.mcp.json`** (minimal config):
   ```json
   {
     "mcpServers": {
       "gemini-assistant": {
         "command": "uvx", 
         "args": ["automagik-tools@latest", "tool", "gemini-assistant"],
         "env": {
           "GEMINI_API_KEY": "your_gemini_api_key_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop/Cursor** - the tool will be available immediately!

## Installation

No installation required! The `uvx` command automatically handles dependencies.

For development or if you prefer manual installation:

```bash
pip install automagik-tools[gemini-assistant]
```

## Security

- API keys are never exposed in responses
- Rate limiting prevents abuse
- Sessions expire automatically
- No persistent storage of code
- Uploaded files are cleaned up automatically

## Error Handling

The tool handles common Gemini API errors gracefully:
- `RESOURCE_EXHAUSTED`: API quota exceeded
- `INVALID_ARGUMENT`: Request too large
- File upload timeouts and processing failures
- Network connectivity issues

## Performance

- Parallel file uploads for efficiency
- Exponential backoff for file processing
- Configurable session limits and timeouts
- Memory-efficient session management

## Original Attribution

This tool is adapted from the [mcp-gemini-assistant](https://github.com/peterkrueck/mcp-gemini-assistant) by Peter Krueck, enhanced for the automagik-tools framework.