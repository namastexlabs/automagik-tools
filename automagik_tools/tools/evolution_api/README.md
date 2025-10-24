# Evolution API MCP Tool

Complete WhatsApp messaging suite for Evolution API v2  an MCP tool that lets AI agents and automation workflows send text, media, audio, reactions, locations, contacts and presence (typing/recording) indicators via Evolution API instances.

This README documents configuration, available tools, usage examples, MCP integration blocks for Claude Desktop and Cursor, the fixed-recipient security feature, and common troubleshooting steps.

## Contents

- Overview
- Features
- Configuration (environment variables)
- Quick start (standalone)
- Claude Desktop & Cursor MCP config
- Public tools (functions)
- Usage examples (text, media, audio)
- Fixed-recipient security feature
- Troubleshooting
- Tests & sources

---

## Overview

The Evolution API tool exposes a set of MCP tools that wrap Evolution API v2 endpoints. It is designed for WhatsApp automation and supports:

- Sending text messages (with optional link preview and mentions)
- Sending media (images, videos, documents) with captions and filenames
- Sending audio messages / voice notes
- Sending emoji reactions to messages
- Sending geolocation pins (latitude/longitude)
- Sending contacts (vCard-like payloads)
- Sending presence indicators (typing / recording)

Each MCP tool is implemented in `automagik_tools.tools.evolution_api` and uses `EvolutionAPIClient` (see `client.py`) to perform HTTP requests.

Start here: read `__init__.py` and `client.py` in the same folder to see the exact parameters and behavior.

## Features

- Full coverage of common WhatsApp message types
- Automatic presence/typing support (used for audio messages)
- Retries and exponential backoff in the HTTP client
- Fixed-recipient mode for secure, locked-down deployments
- Simple integration with Claude Desktop and Cursor via MCP transport

## Configuration

Set these environment variables to configure the tool:

```bash
# Required
EVOLUTION_API_API_KEY=your-evolution-api-key     # API key used to authenticate with Evolution API

# Recommended
EVOLUTION_API_BASE_URL=https://evolution.example.com  # Base URL for Evolution API (no trailing slash required)

# Optional security feature
EVOLUTION_API_FIXED_RECIPIENT=+12345678901   # When set, all outgoing messages go to this number and tools ignore any 'number' parameter

# Optional client tuning (defaults set in code)
EVOLUTION_API_TIMEOUT=30       # HTTP request timeout in seconds
EVOLUTION_API_MAX_RETRIES=3    # Max retries for HTTP requests
```

Notes:
- `EVOLUTION_API_API_KEY` is required for normal operation; tools will respond with an error if it is missing.
- `EVOLUTION_API_FIXED_RECIPIENT` is a safety feature (documented below). When set, any `number` parameter passed to tools is ignored and the fixed number is used instead.

## Quick start (standalone)

Start the MCP server for Evolution API (stdio mode, good for Claude Desktop) using the project CLI:

```powershell
# Run the tool in stdio mode (Claude Desktop / local testing)
uvx automagik-tools tool evolution_api
```

For SSE/web usage, run with the `--transport sse` flag and `--port` to bind to a port.

## Claude Desktop configuration

Add an MCP server entry to your Claude Desktop config (`claude_desktop_config.json`) similar to this:

```json
{
  "mcpServers": {
    "evolution_api": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "evolution_api"],
      "env": {
        "EVOLUTION_API_API_KEY": "your-api-key",
        "EVOLUTION_API_BASE_URL": "http://localhost:8882",
        "EVOLUTION_API_FIXED_RECIPIENT": "+12345678901"
      }
    }
  }
}
```

## Cursor configuration

Cursor MCP entries follow the same shape. Example (add to your Cursor MCP config):

```json
{
  "mcpServers": {
    "evolution_api": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "evolution_api"],
      "env": {
        "EVOLUTION_API_API_KEY": "your-api-key",
        "EVOLUTION_API_BASE_URL": "http://localhost:8882"
      }
    }
  }
}
```

## Public tools (MCP functions)

The tool exposes the following MCP functions. (These names match the functions in `__init__.py`.)

- send_text_message
  - Parameters: instance (str), message (str), number (optional str), delay (int ms), linkPreview (bool), mentions (list)

- send_media (often described as send_media_message)
  - Parameters: instance, media (base64 or URL), mediatype (image|video|document), mimetype, number (optional), caption, fileName, delay, linkPreview, mentions

- send_audio (send_audio_message)
  - Parameters: instance, audio (base64 or URL), number (optional), delay, linkPreview, mentions, quoted (optional dict)

- send_reaction
  - Parameters: instance, remote_jid, from_me (bool), message_id, reaction (emoji)

- send_location
  - Parameters: instance, latitude (float), longitude (float), number (optional), name (str), address (str), delay, mentions

- send_contact
  - Parameters: instance, contact (list of contact dicts), number (optional), delay, mentions

- send_presence
  - Parameters: instance, number (optional), presence (composing|recording|paused), delay (ms)

Also available via the client are management helpers:
- create_instance
- get_instance_info

See the function docstrings in `__init__.py` for more detail on each parameter and the example return shapes.

## Usage examples (Python, async)

These examples use `EvolutionAPIClient` directly (async). They are runnable once `EVOLUTION_API_API_KEY` and `EVOLUTION_API_BASE_URL` are set.

1) Send a text message

```python
import asyncio
from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

async def send_text():
    cfg = EvolutionAPIConfig()  # will read env vars
    client = EvolutionAPIClient(cfg)

    res = await client.send_text_message(
        instance="my-instance",
        number="+15551234567",
        message="Hello from Evolution API!",
        delay=0,
        linkPreview=True,
    )
    print(res)

asyncio.run(send_text())
```

2) Send an image (media) by URL

```python
import asyncio
from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

async def send_image():
    cfg = EvolutionAPIConfig()
    client = EvolutionAPIClient(cfg)

    res = await client.send_media(
        instance="my-instance",
        number="+15551234567",
        media="https://example.com/photo.jpg",
        mediatype="image",
        mimetype="image/jpeg",
        caption="Here is a photo",
        fileName="photo.jpg",
    )
    print(res)

asyncio.run(send_image())
```

3) Send an audio message (base64 or URL)

```python
import asyncio
from automagik_tools.tools.evolution_api.client import EvolutionAPIClient
from automagik_tools.tools.evolution_api.config import EvolutionAPIConfig

async def send_audio():
    cfg = EvolutionAPIConfig()
    client = EvolutionAPIClient(cfg)

    # audio can be a base64 string or a direct URL
    res = await client.send_audio(
        instance="my-instance",
        number="+15551234567",
        audio="https://example.com/voice.mp3",
        delay=0,
    )
    print(res)

asyncio.run(send_audio())
```

Notes on examples:
- When `EVOLUTION_API_FIXED_RECIPIENT` is set, the `number` values above will be ignored and the fixed recipient will be used instead.
- If you prefer MCP-level examples, run the tool with `uvx automagik-tools tool evolution_api` and then call the MCP function from your agent or an MCP client.

## Fixed-recipient security feature

`EVOLUTION_API_FIXED_RECIPIENT` is provided to lock outgoing messages to a single, pre-approved number. When this environment variable is set:

- Any `number` parameter passed to MCP tools is ignored.
- All outgoing messages are routed to the fixed recipient.
- This is useful for public deployments, demos, and CI where you want to avoid accidental messaging to arbitrary numbers.

Security guidance:

- Use this in combination with a restricted API key and network-level controls.
- Do not check `EVOLUTION_API_API_KEY` or `EVOLUTION_API_FIXED_RECIPIENT` into source code or public repositories.

## Troubleshooting

Common errors and how to resolve them:

- Authentication failed (401):
  - Symptom: Error message "Evolution API authentication failed - check API key"
  - Fix: Verify `EVOLUTION_API_API_KEY` is correct and has required permissions.

- Access forbidden (403):
  - Symptom: Error "Evolution API access forbidden - check permissions"
  - Fix: Ensure the API key has access to the requested instance and that any IP/network allowlists permit requests.

- Endpoint not found (404):
  - Symptom: "Evolution API endpoint not found"
  - Fix: Verify `EVOLUTION_API_BASE_URL` and instance names; check for trailing slashes and correct endpoint paths.

- Server error (5xx):
  - Symptom: Errors returned from server; client will retry with exponential backoff
  - Fix: Check Evolution API server health and logs; consider increasing `EVOLUTION_API_MAX_RETRIES` temporarily.

- Timeout / Connection errors:
  - Symptom: TimeoutError or ConnectionError after retries
  - Fix: Confirm network connectivity to `EVOLUTION_API_BASE_URL`, adjust `EVOLUTION_API_TIMEOUT`, and ensure DNS resolves.

- Missing API key / client not configured:
  - Symptom: Tools respond with "Evolution API client not configured - missing API key"
  - Fix: Set `EVOLUTION_API_API_KEY` in the environment where the MCP server runs.

- Fixed recipient not set but `number` missing:
  - Symptom: ValueError: "No recipient number provided and EVOLUTION_API_FIXED_RECIPIENT not set"
  - Fix: Provide `number` in tool calls or set `EVOLUTION_API_FIXED_RECIPIENT`.

If you still have issues, consult the Evolution API server logs and the `tests/tools/test_evolution_api.py` for example test cases that show correct call patterns.

## Tests & sources

- Tool implementation: `automagik_tools/tools/evolution_api/__init__.py`
- HTTP client: `automagik_tools/tools/evolution_api/client.py`
- Tests: `tests/tools/test_evolution_api.py` (contains usage patterns and expectations for registered tools)

## Notes & next steps

- This README follows the structure and style used by the Omni and Wait tool READMEs in this repository.
- If you want I can add more example snippets showing MCP JSON payloads and a short guide for running the tool with SSE (web) transport.

---

Maintainers: Namastex Labs  part of the automagik-tools project
