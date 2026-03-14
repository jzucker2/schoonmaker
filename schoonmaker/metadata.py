"""Screenplay metadata/stats computed from a parsed Screenplay (FDX AST)."""

from __future__ import annotations

from typing import Any

from .fdx.models import (
    Action,
    DialogueBlock,
    General,
    Lyric,
    ScreenElement,
    Screenplay,
    Shot,
    Transition,
)


def _element_type(el: ScreenElement) -> str:
    """Return element type name for counting."""
    if isinstance(el, Action):
        return "action"
    if isinstance(el, DialogueBlock):
        return "dialogue_block"
    if isinstance(el, Transition):
        return "transition"
    if isinstance(el, Shot):
        return "shot"
    if isinstance(el, General):
        return "general"
    if isinstance(el, Lyric):
        return "lyric"
    return "other"


def _word_count(text: str) -> int:
    """Count space-separated words (non-empty tokens)."""
    return len([t for t in (text or "").split() if t])


def _heading_to_location(raw: str) -> str:
    """Normalize heading to location (strip after last ' - ')."""
    raw = (raw or "").strip()
    if " - " in raw:
        return raw.rsplit(" - ", 1)[0].strip() or raw
    return raw


def _location_int_ext(loc: str) -> str:
    """Classify as indoor/outdoor/other by INT./EXT. prefix."""
    u = (loc or "").strip().upper()
    if u.startswith("INT.") or u.startswith("INT "):
        return "indoor"
    if u.startswith("EXT.") or u.startswith("EXT "):
        return "outdoor"
    return "other"


def _dialogue_line_count(el: DialogueBlock) -> int:
    """Number of spoken lines (DialoguePart type 'line') in a block."""
    return sum(1 for p in el.parts if getattr(p, "type", None) == "line")


def _dialogue_word_count(el: DialogueBlock) -> int:
    """Word count of spoken lines only (DialoguePart type 'line')."""
    return sum(
        _word_count(getattr(p, "text", "") or "")
        for p in el.parts
        if getattr(p, "type", None) == "line"
    )


def _parenthetical_count(el: DialogueBlock) -> int:
    """Number of parenthetical parts in a block."""
    return sum(
        1 for p in el.parts if getattr(p, "type", None) == "parenthetical"
    )


def _parenthetical_word_count(el: DialogueBlock) -> int:
    """Word count of parenthetical parts only."""
    return sum(
        _word_count(getattr(p, "text", "") or "")
        for p in el.parts
        if getattr(p, "type", None) == "parenthetical"
    )


def compute_screenplay_metadata(screenplay: Screenplay) -> dict[str, Any]:
    """
    Compute stats/metadata from a Screenplay for JSON output.

    Includes: scene count, element counts by type (action, dialogue_block,
    dialogue_line, transition, etc.), characters per scene, lines per scene
    per character, and aggregate counts. Only generated when CLI --metadata
    is passed.
    """
    elements_by_type: dict[str, int] = {
        "action": 0,
        "dialogue_block": 0,
        "dialogue_line": 0,
        "transition": 0,
        "shot": 0,
        "general": 0,
        "lyric": 0,
    }
    # Per-scene: scene_id, action/dialogue counts, characters[], lines_count
    scenes_detail: list[dict[str, Any]] = []
    # By character: scenes_count, dialogue_lines_count, scene_ids[]
    by_character: dict[str, dict[str, Any]] = {}

    def process_elements(
        elements: list[ScreenElement],
        scene_characters: set[str],
        scene_action: int,
        scene_dialogue_block: int,
        scene_dialogue_line: int,
    ) -> tuple[int, int, int]:
        for el in elements:
            t = _element_type(el)
            if t in elements_by_type:
                elements_by_type[t] += 1
            if t == "action":
                scene_action += 1
            elif t == "dialogue_block":
                scene_dialogue_block += 1
                assert isinstance(el, DialogueBlock)
                lines = _dialogue_line_count(el)
                elements_by_type["dialogue_line"] += lines
                scene_dialogue_line += lines
                name = (el.character or "").strip()
                if name:
                    scene_characters.add(name)
                    if name not in by_character:
                        by_character[name] = {
                            "scenes_count": 0,
                            "dialogue_lines_count": 0,
                            "scene_ids": [],
                        }
                    by_character[name]["dialogue_lines_count"] += lines
            elif t == "transition":
                pass  # already counted in elements_by_type
            elif t in ("shot", "general", "lyric"):
                pass
        return scene_action, scene_dialogue_block, scene_dialogue_line

    # Preamble (counts go into elements_by_type and by_character)
    process_elements(
        screenplay.preamble,
        set(),
        0,
        0,
        0,
    )

    for scene in screenplay.scenes:
        scene_characters = set()
        scene_action = 0
        scene_dialogue_block = 0
        scene_dialogue_line = 0
        scene_action, scene_dialogue_block, scene_dialogue_line = (
            process_elements(
                scene.elements,
                scene_characters,
                scene_action,
                scene_dialogue_block,
                scene_dialogue_line,
            )
        )
        for name in scene_characters:
            if name not in by_character:
                by_character[name] = {
                    "scenes_count": 0,
                    "dialogue_lines_count": 0,
                    "scene_ids": [],
                }
            by_character[name]["scenes_count"] += 1
            by_character[name]["scene_ids"].append(scene.id)
        # Lines per character in this scene
        character_line_count: dict[str, int] = {}
        for el in scene.elements:
            if _element_type(el) == "dialogue_block":
                assert isinstance(el, DialogueBlock)
                name = (el.character or "").strip()
                if name:
                    character_line_count[name] = character_line_count.get(
                        name, 0
                    ) + _dialogue_line_count(el)
        lines_count = (
            scene_action
            + scene_dialogue_block
            + sum(
                1
                for el in scene.elements
                if _element_type(el)
                in ("transition", "shot", "general", "lyric")
            )
        )
        scenes_detail.append(
            {
                "scene_id": scene.id,
                "action_count": scene_action,
                "dialogue_block_count": scene_dialogue_block,
                "dialogue_line_count": scene_dialogue_line,
                "characters": sorted(scene_characters),
                "character_line_count": character_line_count,
                "lines_count": lines_count,
            }
        )

    # Word counts: dialogue (spoken lines only), action, and whole script
    total_action_words = 0
    total_dialogue_words = 0
    total_transition_words = 0
    total_shot_words = 0
    total_general_words = 0
    total_lyric_words = 0

    def count_words(elements: list[ScreenElement]) -> None:
        nonlocal total_action_words, total_dialogue_words
        nonlocal total_transition_words, total_shot_words
        nonlocal total_general_words, total_lyric_words
        for el in elements:
            t = _element_type(el)
            if t == "action":
                total_action_words += _word_count(
                    getattr(el, "text", "") or ""
                )
            elif t == "dialogue_block":
                assert isinstance(el, DialogueBlock)
                total_dialogue_words += _dialogue_word_count(el)
            elif t == "transition":
                total_transition_words += _word_count(
                    getattr(el, "text", "") or ""
                )
            elif t == "shot":
                total_shot_words += _word_count(getattr(el, "text", "") or "")
            elif t == "general":
                total_general_words += _word_count(
                    getattr(el, "text", "") or ""
                )
            elif t == "lyric":
                total_lyric_words += _word_count(getattr(el, "text", "") or "")

    count_words(screenplay.preamble)
    for scene in screenplay.scenes:
        count_words(scene.elements)

    total_scene_heading_count = len(screenplay.scenes)
    total_scene_heading_words = sum(
        _word_count(s.heading.raw or "") for s in screenplay.scenes
    )

    location_counts: dict[str, int] = {}
    indoor_counts: dict[str, int] = {}
    outdoor_counts: dict[str, int] = {}
    other_location_counts: dict[str, int] = {}
    indoor_scenes_count = 0
    outdoor_scenes_count = 0
    other_scenes_count = 0
    for scene in screenplay.scenes:
        loc = _heading_to_location(scene.heading.raw or "")
        if loc:
            location_counts[loc] = location_counts.get(loc, 0) + 1
            kind = _location_int_ext(loc)
            if kind == "indoor":
                indoor_counts[loc] = indoor_counts.get(loc, 0) + 1
                indoor_scenes_count += 1
            elif kind == "outdoor":
                outdoor_counts[loc] = outdoor_counts.get(loc, 0) + 1
                outdoor_scenes_count += 1
            else:
                n = other_location_counts.get(loc, 0) + 1
                other_location_counts[loc] = n
                other_scenes_count += 1
    total_locations_count = len(location_counts)
    locations = [
        {"location": loc, "count": count}
        for loc, count in sorted(location_counts.items())
    ]
    indoor_locations = [
        {"location": loc, "count": count}
        for loc, count in sorted(indoor_counts.items())
    ]
    outdoor_locations = [
        {"location": loc, "count": count}
        for loc, count in sorted(outdoor_counts.items())
    ]
    other_locations = [
        {"location": loc, "count": count}
        for loc, count in sorted(other_location_counts.items())
    ]

    total_parenthetical_count = 0
    total_parenthetical_words = 0
    for el in screenplay.preamble + [
        e for s in screenplay.scenes for e in s.elements
    ]:
        if _element_type(el) == "dialogue_block":
            assert isinstance(el, DialogueBlock)
            total_parenthetical_count += _parenthetical_count(el)
            total_parenthetical_words += _parenthetical_word_count(el)

    total_words = (
        total_action_words
        + total_dialogue_words
        + total_parenthetical_words
        + total_scene_heading_words
        + total_transition_words
        + total_shot_words
        + total_general_words
        + total_lyric_words
    )

    total_paragraphs = (
        elements_by_type["action"]
        + elements_by_type["dialogue_block"]
        + elements_by_type["transition"]
        + elements_by_type["shot"]
        + elements_by_type["general"]
        + elements_by_type["lyric"]
    )

    return {
        "scenes_count": len(screenplay.scenes),
        "elements": elements_by_type,
        "characters": by_character,
        "scenes": scenes_detail,
        "total_action_count": elements_by_type["action"],
        "total_dialogue_block_count": elements_by_type["dialogue_block"],
        "total_dialogue_line_count": elements_by_type["dialogue_line"],
        "total_paragraphs_count": total_paragraphs,
        "total_action_words": total_action_words,
        "total_dialogue_words": total_dialogue_words,
        "total_scene_heading_count": total_scene_heading_count,
        "total_scene_heading_words": total_scene_heading_words,
        "total_locations_count": total_locations_count,
        "locations": locations,
        "indoor_locations_count": len(indoor_counts),
        "outdoor_locations_count": len(outdoor_counts),
        "indoor_locations": indoor_locations,
        "outdoor_locations": outdoor_locations,
        "indoor_scenes_count": indoor_scenes_count,
        "outdoor_scenes_count": outdoor_scenes_count,
        "other_locations_count": len(other_location_counts),
        "other_locations": other_locations,
        "other_scenes_count": other_scenes_count,
        "total_parenthetical_count": total_parenthetical_count,
        "total_parenthetical_words": total_parenthetical_words,
        "total_words": total_words,
    }
