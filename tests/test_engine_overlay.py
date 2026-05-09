"""Tests for overlay filtergraph behavior."""

from types import SimpleNamespace

from mcp_video.engine_overlay import overlay_video


def test_overlay_converts_base_and_output_to_stable_pixel_formats(tmp_path, monkeypatch):
    background = tmp_path / "background.mp4"
    overlay = tmp_path / "overlay.mp4"
    output = tmp_path / "output.mp4"
    background.write_bytes(b"background")
    overlay.write_bytes(b"overlay")
    calls = []

    def fake_run_ffmpeg(cmd):
        calls.append(cmd.copy())
        output.write_bytes(b"output")

    monkeypatch.setattr("mcp_video.engine_overlay._run_ffmpeg", fake_run_ffmpeg)
    monkeypatch.setattr(
        "mcp_video.engine_overlay._build_edit_result",
        lambda output_path, operation, timing: SimpleNamespace(output_path=output_path, operation=operation),
    )

    result = overlay_video(str(background), str(overlay), position="center", opacity=0.5, output_path=str(output))

    assert result.output_path == str(output)
    assert len(calls) == 1
    filter_graph = calls[0][calls[0].index("-filter_complex") + 1]
    assert "[0:v]format=rgba[base]" in filter_graph
    assert "colorchannelmixer=aa=0.50" in filter_graph
    assert "overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2" in filter_graph
    assert filter_graph.endswith(",format=yuv420p")
