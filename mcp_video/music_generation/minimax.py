"""MiniMax music generation API client.

Docs: https://platform.minimax.io/docs/api-reference/music-generation
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from mcp_video.errors import MCPVideoError
from mcp_video.limits import DEFAULT_AI_TIMEOUT

MINIMAX_API_BASE = "https://api.minimax.io/v1/music_generation"
MINIMAX_API_KEY_ENV = "MINIMAX_API_KEY"

MINIMAX_MODELS = {
    "music-2.6",
    "music-2.6-free",
    "music-cover",
    "music-cover-free",
}


def _require_api_key() -> str:
    key = os.environ.get(MINIMAX_API_KEY_ENV)
    if not key:
        raise MCPVideoError(
            f"{MINIMAX_API_KEY_ENV} environment variable is required for MiniMax music generation.",
            error_type="auth_error",
            code="missing_api_key",
        )
    return key


def _post_json(url: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise MCPVideoError(
            f"MiniMax API error {exc.code}: {body}",
            error_type="api_error",
            code="minimax_http_error",
        ) from exc
    except urllib.error.URLError as exc:
        raise MCPVideoError(
            f"MiniMax API connection failed: {exc.reason}",
            error_type="api_error",
            code="minimax_connection_error",
        ) from exc


def _download_url(url: str, output_path: str, timeout: int) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-video/1.4.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(output_path, "wb") as f:
            f.write(resp.read())
    except urllib.error.URLError as exc:
        raise MCPVideoError(
            f"Failed to download audio from MiniMax URL: {exc.reason}",
            error_type="api_error",
            code="minimax_download_error",
        ) from exc


def generate_music_minimax(
    prompt: str,
    output_path: str,
    *,
    model: str = "music-2.6-free",
    lyrics: str | None = None,
    is_instrumental: bool = True,
    output_format: str = "url",
    audio_format: str = "mp3",
    sample_rate: int = 44100,
    bitrate: int = 256000,
    timeout: int = DEFAULT_AI_TIMEOUT,
) -> dict[str, Any]:
    """Generate music via the MiniMax API.

    Args:
        prompt: Text description of the music style, mood, and scenario.
        output_path: Local path to save the generated audio file.
        model: Model name. Use "music-2.6-free" for free tier,
               "music-2.6" for paid (higher quality/RPM).
        lyrics: Song lyrics with structure tags like [Verse], [Chorus].
                Required for vocal generation when is_instrumental=False.
        is_instrumental: If True, generates instrumental music (no vocals).
        output_format: "url" or "hex". URL links expire after 24 hours.
        audio_format: Output audio format: "mp3", "wav", etc.
        sample_rate: Sample rate of output audio.
        bitrate: Bitrate of output audio.
        timeout: HTTP timeout in seconds.

    Returns:
        dict with keys: output_path, music_duration_ms, music_sample_rate,
        music_channel, bitrate, music_size_bytes, trace_id.

    Raises:
        MCPVideoError: On auth, API, or download failures.
    """
    if model not in MINIMAX_MODELS:
        raise MCPVideoError(
            f"Unknown MiniMax model: {model}. Available: {sorted(MINIMAX_MODELS)}",
            error_type="validation_error",
            code="unknown_model",
        )

    api_key = _require_api_key()

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "output_format": output_format,
        "is_instrumental": is_instrumental,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
        },
    }

    if lyrics is not None:
        payload["lyrics"] = lyrics

    response = _post_json(MINIMAX_API_BASE, payload, api_key, timeout)

    base_resp = response.get("base_resp", {})
    status_code = base_resp.get("status_code")
    if status_code != 0:
        status_msg = base_resp.get("status_msg", "unknown error")
        raise MCPVideoError(
            f"MiniMax generation failed (status {status_code}): {status_msg}",
            error_type="api_error",
            code="minimax_generation_failed",
        )

    data = response.get("data", {})
    extra = response.get("extra_info", {})

    if output_format == "url":
        audio_url = data.get("audio")
        if not audio_url:
            raise MCPVideoError(
                "MiniMax response missing audio URL.",
                error_type="api_error",
                code="minimax_missing_audio",
            )
        _download_url(audio_url, output_path, timeout)
    elif output_format == "hex":
        import binascii

        hex_audio = data.get("audio", "")
        if not hex_audio:
            raise MCPVideoError(
                "MiniMax response missing hex audio data.",
                error_type="api_error",
                code="minimax_missing_audio",
            )
        with open(output_path, "wb") as f:
            f.write(binascii.unhexlify(hex_audio))
    else:
        raise MCPVideoError(
            f"Invalid output_format: {output_format}. Use 'url' or 'hex'.",
            error_type="validation_error",
            code="invalid_output_format",
        )

    return {
        "output_path": output_path,
        "music_duration_ms": extra.get("music_duration"),
        "music_sample_rate": extra.get("music_sample_rate"),
        "music_channel": extra.get("music_channel"),
        "bitrate": extra.get("bitrate"),
        "music_size_bytes": extra.get("music_size"),
        "trace_id": response.get("trace_id"),
    }
