"""MCP music generation tool registrations."""

from __future__ import annotations

from typing import Any

from .music_generation import generate_music_minimax, MINIMAX_MODELS
from .server_app import _result, _safe_tool, mcp


@mcp.tool()
@_safe_tool
def video_generate_music(
    prompt: str,
    output_path: str,
    model: str = "music-2.6-free",
    lyrics: str | None = None,
    is_instrumental: bool = True,
    duration: int | None = None,
) -> dict[str, Any]:
    """Generate music from a text prompt using the MiniMax API.

    Requires the MINIMAX_API_KEY environment variable.

    Args:
        prompt: Text description of the music style, mood, and scenario.
                Example: "Cinematic orchestral trailer, epic drums, brass, 120bpm".
        output_path: Absolute path to save the generated audio file.
        model: MiniMax model to use. "music-2.6-free" for free tier,
               "music-2.6" for paid (higher quality and RPM).
        lyrics: Song lyrics with structure tags like [Verse], [Chorus].
                Required when is_instrumental=False.
        is_instrumental: If True (default), generates instrumental music with no vocals.
        duration: Target duration in seconds. Note: the API determines final length;
                  this is used to guide generation.
    """
    if model not in MINIMAX_MODELS:
        return {
            "success": False,
            "error": {
                "type": "validation_error",
                "code": "unknown_model",
                "message": f"Unknown model: {model}. Available: {sorted(MINIMAX_MODELS)}",
            },
        }

    result = generate_music_minimax(
        prompt=prompt,
        output_path=output_path,
        model=model,
        lyrics=lyrics,
        is_instrumental=is_instrumental,
    )
    return _result(result)
