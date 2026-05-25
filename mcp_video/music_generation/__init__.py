"""Music generation integrations for mcp-video.

Supported providers:
  - MiniMax (music-2.6, music-2.6-free, music-cover)
"""

from .minimax import generate_music_minimax, MINIMAX_MODELS

__all__ = ["MINIMAX_MODELS", "generate_music_minimax"]
