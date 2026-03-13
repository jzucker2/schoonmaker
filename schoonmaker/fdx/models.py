from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, TypeAlias

PartType = Literal["line", "parenthetical"]


@dataclass
class InlineRun:
    text: str
    style: Optional[str] = None
    font: Optional[str] = None
    size: Optional[str] = None
    revision_id: Optional[str] = None
    raw_attrib: dict[str, str] = field(default_factory=dict)


@dataclass
class ParagraphInfo:
    type: str
    raw_text: str
    runs: list[InlineRun] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    scene_properties: dict[str, Any] = field(default_factory=dict)
    script_notes: list[str] = field(default_factory=list)


@dataclass
class DialoguePart:
    type: PartType
    text: str


@dataclass
class DialogueBlock:
    type: Literal["dialogue_block"] = "dialogue_block"
    character: str = ""
    parts: list[DialoguePart] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    dual: bool = False
    dual_group: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    type: Literal["action"] = "action"
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    type: Literal["transition"] = "transition"
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Shot:
    type: Literal["shot"] = "shot"
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class General:
    type: Literal["general"] = "general"
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Lyric:
    type: Literal["lyric"] = "lyric"
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


ScreenElement: TypeAlias = (
    Action | DialogueBlock | Transition | Shot | General | Lyric
)


@dataclass
class SceneHeading:
    raw: str
    scene_number: Optional[str] = None
    title: Optional[str] = None
    page_hint: Optional[str] = None
    length_hint: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    id: str
    heading: SceneHeading
    elements: list[ScreenElement] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TitlePageField:
    label: Optional[str]
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Screenplay:
    document_type: Optional[str] = None
    version: Optional[str] = None
    title_page: list[TitlePageField] = field(default_factory=list)
    scenes: list[Scene] = field(default_factory=list)
    preamble: list[ScreenElement] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
