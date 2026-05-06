"""Tests for PUSHING CREATION style-pack and storyboard helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_video.creation_engine import (
    create_video_project,
    read_storyboard,
    read_style_pack,
    render_shot_prompt,
)
from mcp_video.errors import MCPVideoError


def test_create_video_project_scaffolds_pushing_creation_layout(tmp_path: Path):
    result = create_video_project("editorial-portrait", output_dir=str(tmp_path))

    project = tmp_path / "projects" / "editorial-portrait"
    assert result["project_path"] == str(project)
    assert (project / "style.md").is_file()
    assert (project / "storyboard.md").is_file()
    assert (project / "refs" / ".gitkeep").is_file()
    assert result["next_steps"][0].startswith("Drop reference stills")


def test_create_video_project_rejects_unsafe_slug(tmp_path: Path):
    with pytest.raises(MCPVideoError) as exc_info:
        create_video_project("../nope", output_dir=str(tmp_path))

    assert exc_info.value.code == "invalid_parameter"


def test_read_style_pack_parses_style_and_negative_blocks(tmp_path: Path):
    style_path = tmp_path / "style.md"
    style_path.write_text(
        """
## STYLE_GOLDEN_HOUR
late afternoon rim light, warm key

## NEG_AI_LIGHTING
flat noon, fake lens flare
""".strip()
    )

    result = read_style_pack(str(style_path))

    assert result["block_count"] == 2
    assert result["style_blocks"][0]["name"] == "STYLE_GOLDEN_HOUR"
    assert result["negative_blocks"][0]["body"] == "flat noon, fake lens flare"


def test_read_storyboard_parses_markdown_table(tmp_path: Path):
    storyboard_path = tmp_path / "storyboard.md"
    storyboard_path.write_text(
        """
| Shot | Provider | Model | Camera | Lens | Aspect | Action | Refs | Style | Neg | Mode | Duration |
|------|----------|-------|--------|------|--------|--------|------|-------|-----|------|----------|
| opener | runway | gen3 | ARRI Alexa 35 | 50mm T1.5 | 16:9 | Shot on ARRI, slow push. | hero.jpg | STYLE_GOLDEN_HOUR | NEG_AI_LIGHTING | video | 5s |
""".strip()
    )

    result = read_storyboard(str(storyboard_path))

    assert result["shot_count"] == 1
    assert result["shots"][0]["shot"] == "opener"
    assert result["shots"][0]["style"] == ["STYLE_GOLDEN_HOUR"]


def test_render_shot_prompt_expands_referenced_blocks(tmp_path: Path):
    project = tmp_path / "projects" / "launch"
    project.mkdir(parents=True)
    (project / "style.md").write_text(
        """
## STYLE_GOLDEN_HOUR
late afternoon rim light, warm key

## NEG_AI_LIGHTING
flat noon, fake lens flare
""".strip()
    )
    (project / "storyboard.md").write_text(
        """
| Shot | Provider | Model | Camera | Lens | Aspect | Action | Refs | Style | Neg | Mode | Duration |
|------|----------|-------|--------|------|--------|--------|------|-------|-----|------|----------|
| opener | runway | gen3 | ARRI Alexa 35 | 50mm T1.5 | 16:9 | Shot on ARRI Alexa 35, slow push. | hero.jpg | STYLE_GOLDEN_HOUR | NEG_AI_LIGHTING | video | 5s |
""".strip()
    )

    result = render_shot_prompt(str(project), shot="opener")

    assert result["shot"] == "opener"
    assert result["provider"] == "runway"
    assert "Shot on ARRI Alexa 35" in result["prompt"]
    assert "late afternoon rim light" in result["prompt"]
    assert result["negative_prompt"] == "flat noon, fake lens flare"
