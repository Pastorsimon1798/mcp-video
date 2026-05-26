"""Regression tests for the base install without optional NumPy extras."""

from __future__ import annotations

import subprocess
import sys

from mcp_video.defaults import DEFAULT_FFMPEG_TIMEOUT


def test_public_import_and_audio_fallback_without_numpy(tmp_path) -> None:
    script = """
import importlib
import importlib.abc
import pathlib
import sys


class BlockNumpy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "numpy" or fullname.startswith("numpy."):
            raise ImportError("blocked numpy for fallback regression test")
        return None


for module_name in [key for key in list(sys.modules) if key == "numpy" or key.startswith("numpy.")]:
    del sys.modules[module_name]
importlib.invalidate_caches()
sys.meta_path.insert(0, BlockNumpy())

import mcp_video
from mcp_video.audio_engine import audio_synthesize
from mcp_video.audio_engine.core import (
    apply_chorus,
    apply_flanger,
    apply_reverb,
    generate_fm,
    generate_pluck,
    generate_pulse,
    generate_sawtooth,
    generate_supersaw,
    generate_triangle,
)
from mcp_video.errors import MCPVideoError

out = pathlib.Path(sys.argv[1]) / "fallback.wav"
audio_synthesize(
    output=str(out),
    waveform="pulse",
    duration=0.02,
    sample_rate=8000,
    effects={"chorus": {"rate": 1.0, "depth": 0.001}},
)

assert mcp_video.__version__
assert callable(apply_chorus)
assert generate_pulse(440, 0.01, 8000)
assert apply_reverb([0.1, 0.2, 0.3], room_size=0.0)
assert apply_flanger([0.1, 0.2, 0.3], sample_rate=8000)

for bad_call in (
    lambda: generate_pulse(0, 0.01, 8000),
    lambda: generate_pluck(0, 0.01, 8000),
    lambda: generate_fm(0, 0.01, 8000),
    lambda: generate_sawtooth(0, 0.01, 8000),
    lambda: generate_triangle(0, 0.01, 8000),
    lambda: generate_supersaw(440, 0.01, 8000, detune=2.0, voices=3),
):
    try:
        bad_call()
    except MCPVideoError:
        pass
    else:
        raise AssertionError("expected MCPVideoError for invalid fallback synthesis input")

assert out.stat().st_size > 44
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_FFMPEG_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError("No-NumPy fallback subprocess timed out") from exc

    assert result.returncode == 0, result.stderr
