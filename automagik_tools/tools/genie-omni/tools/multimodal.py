"""Multimodal tools - Audio, voice, and multimedia capabilities."""

import logging
import os
from pathlib import Path
from typing import Callable, Optional
import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

def register_tools(mcp: FastMCP, get_client: Callable, get_config: Callable):
    """Register multimodal tools with the MCP server."""

    # ==========================================================================
    # CATEGORY: Voice-to-WhatsApp (ElevenLabs TTS + Evolution API)
    # ==========================================================================

    @mcp.tool()
    async def talk(
        to: str,
        text: str,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_v3",
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        instance_name: str = "genie",
        quoted_message_id: Optional[str] = None,
        delay: Optional[int] = None,
        mentioned: Optional[list] = None,
        mentions_every_one: bool = False,
    ) -> str:
        """Talk to someone via WhatsApp - generate speech and send automatically.

        This is YOUR voice assistant mode - speak naturally to contacts via WhatsApp.
        Combines speech generation + automatic WhatsApp delivery with presence.

        🎙️ HOW IT WORKS:
        1. Generates natural speech from your text using ElevenLabs
        2. Shows "recording" presence on WhatsApp
        3. Automatically sends the audio message
        4. All in one seamless action!

        🎭 AUDIO TAGS (Eleven v3):
        Use square brackets to add expression:
        - Emotions: [happy], [sad], [excited], [angry], [whispers], [sarcastic]
        - Sounds: [laughs], [sighs], [clears throat], [exhales]
        - Delivery: [strong French accent], [singing], [mischievously]

        📝 PROMPTING TIPS:
        - Use CAPS for emphasis: "That was VERY funny"
        - Add punctuation for rhythm: "Well... [sighs] I don't know"
        - Combine tags: "[laughing] That's amazing! [excited]"

        Args:
            to: Phone number to send to (e.g., "5511999999999" or contact ID)
            text: What you want to say (supports audio tags in [brackets])
                 Example: "[excited] I can't believe it! [laughs]"
            voice_id: Voice to use (default: from XI_VOICE_ID env var)
                     Choose voices with emotional range for best results
            model_id: TTS model (default: eleven_v3 - Eleven v3 alpha)
                     Most expressive model with 70+ language support
            stability: Voice delivery style 0-1 (default: 0.5 - Natural)
                      0.0-0.3 = Creative (very expressive, responds to tags)
                      0.4-0.6 = Natural (balanced, good tag response)
                      0.7-1.0 = Robust (stable, less responsive to tags)
            similarity_boost: Voice clarity 0-1 (default: 0.75)
                             Higher = closer to original voice
            instance_name: WhatsApp instance (default: "genie")
            quoted_message_id: Message ID to reply to (optional)
            delay: Delay in milliseconds before sending (optional)
            mentioned: List of phone numbers to mention (optional)
            mentions_every_one: Whether to mention everyone in group (default: False)

        Returns:
            Confirmation of speech generation and WhatsApp delivery

        Examples:
            # Simple voice message
            talk(to="5511999999999", text="Hey! Just wanted to say hi!")

            # Expressive delivery
            talk(
                to="5511999999999",
                text="[excited] You won't BELIEVE what just happened! [laughs]",
                stability=0.3  # More expressive
            )

            # Professional message
            talk(
                to="group_id",
                text="Good morning team. Here's today's update.",
                stability=0.7  # More stable
            )
        """
        config = get_config()
        client = get_client()

        # Get API key
        api_key = os.getenv("XI_API_KEY")
        if not api_key:
            return "❌ ElevenLabs API key not found. Set XI_API_KEY environment variable."

        # Get voice ID from environment or use provided
        if voice_id is None:
            voice_id = os.getenv("XI_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

        # Set default voice settings if not provided
        if stability is None:
            stability = 0.5
        if similarity_boost is None:
            similarity_boost = 0.75

        # Create output directory (use configured folder + voice-messages subdirectory)
        output_dir = Path(config.media_download_folder) / "voice-messages"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate temporary filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talk_{timestamp}.mp3"
        output_path = output_dir / filename

        # Step 1: Generate speech using ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

        body = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        params = {"output_format": "mp3_44100_128"}

        try:
            # Generate audio
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    url,
                    headers=headers,
                    json=body,
                    params=params,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    return f"❌ ElevenLabs API error: {response.status_code}\n{response.text}"

                # Save audio file and prepare for sending
                audio_content = response.content
                with open(output_path, "wb") as f:
                    f.write(audio_content)

                file_size = len(audio_content) / 1024

            # Step 2: Send to WhatsApp with automatic presence (recording)
            # Show "recording" presence before sending
            try:
                await client.evolution_send_presence(
                    instance_name=instance_name,
                    remote_jid=to,
                    presence="recording",
                    delay=1200  # ~1 second
                )
            except Exception as e:
                logger.warning(f"Failed to send presence: {e}")

            # Send audio via Evolution API directly (bypassing Omni server)
            try:
                # Get Evolution API credentials
                instance = await client.get_instance(instance_name, include_status=False)

                if not instance.evolution_url or not instance.evolution_key:
                    return (
                        f"✅ Speech generated ({file_size:.2f} KB)\n"
                        f"❌ Evolution API not configured for instance '{instance_name}'\n"
                        f"Audio saved at: {output_path}"
                    )

                # Convert MP3 to OGG/Opus for WhatsApp voice notes
                from pydub import AudioSegment
                import base64

                # Convert to OGG/Opus format (WhatsApp native voice note format)
                ogg_path = output_path.with_suffix(".ogg")
                audio = AudioSegment.from_mp3(str(output_path))
                audio.export(
                    str(ogg_path),
                    format="ogg",
                    codec="libopus",
                    parameters=["-ar", "16000", "-ac", "1", "-b:a", "32k"]  # WhatsApp optimal settings
                )

                # Read the converted audio
                with open(ogg_path, "rb") as f:
                    audio_content = f.read()

                # Encode audio as base64
                audio_base64 = base64.b64encode(audio_content).decode("utf-8")

                # Call Evolution API directly
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    evolution_url = f"{instance.evolution_url}/message/sendMedia/{instance_name}"

                    # Build payload with required fields
                    payload = {
                        "number": to,
                        "mediatype": "audio",
                        "media": audio_base64,
                        "mimetype": "audio/ogg; codecs=opus",  # WhatsApp voice note format
                        "ptt": True
                    }

                    # Add optional WhatsApp features
                    if delay is not None:
                        payload["delay"] = delay

                    if quoted_message_id:
                        payload["quoted"] = {
                            "key": {
                                "id": quoted_message_id
                            }
                        }

                    if mentions_every_one:
                        payload["mentionsEveryOne"] = True

                    if mentioned and len(mentioned) > 0:
                        payload["mentioned"] = mentioned

                    headers = {
                        "apikey": instance.evolution_key,
                        "Content-Type": "application/json"
                    }

                    logger.info(f"Sending audio to Evolution API: {evolution_url}")

                    response = await http_client.post(
                        evolution_url,
                        headers=headers,
                        json=payload
                    )

                    response.raise_for_status()
                    result = response.json()

                    logger.info(f"Evolution API response: {result}")

                    # Extract message ID from Evolution API response
                    message_id = result.get("key", {}).get("id") if isinstance(result, dict) else None

                    if message_id:
                        return (
                            f"🎙️ Talked to {to} successfully!\n"
                            f"Speech: {text[:80]}{'...' if len(text) > 80 else ''}\n"
                            f"Audio size: {file_size:.2f} KB\n"
                            f"Presence shown: Recording\n"
                            f"Message ID: {message_id}\n"
                            f"Status: Delivered ✅"
                        )
                    else:
                        return (
                            f"✅ Speech generated ({file_size:.2f} KB)\n"
                            f"✅ Sent via Evolution API\n"
                            f"Response: {result}\n"
                            f"Audio saved at: {output_path}"
                        )

            except httpx.HTTPStatusError as http_error:
                logger.error(f"Evolution API HTTP error: {http_error.response.status_code} - {http_error.response.text}")
                return (
                    f"✅ Speech generated ({file_size:.2f} KB)\n"
                    f"❌ Evolution API error: {http_error.response.status_code}\n"
                    f"Response: {http_error.response.text}\n"
                    f"Audio saved at: {output_path}"
                )
            except Exception as send_error:
                logger.error(f"Exception during WhatsApp send: {send_error}", exc_info=True)
                return (
                    f"✅ Speech generated ({file_size:.2f} KB)\n"
                    f"❌ WhatsApp send error: {str(send_error)}\n"
                    f"Audio saved at: {output_path}"
                )

        except Exception as e:
            logger.error(f"Error in talk: {e}")
            return f"❌ Failed to talk: {str(e)}"
