from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional
import uuid
import xml.etree.ElementTree as ET

from .models import (
    Action,
    DialogueBlock,
    DialoguePart,
    General,
    InlineRun,
    Lyric,
    ParagraphInfo,
    Scene,
    SceneHeading,
    ScreenElement,
    Screenplay,
    Shot,
    Transition,
)


class FDXParser:
    """
    Streaming-ish FDX parser focused on screenplay body content.

    Design choices:
    - parse /FinalDraft/Content/Paragraph for screenplay semantics
    - preserve paragraph attributes and scene properties as metadata
    - group Character + Parenthetical + Dialogue into DialogueBlock
    - treat unknown paragraph types as General
    - treat page/layout hints as metadata, not as structure
    """

    def parse(self, path: str) -> Screenplay:
        root_meta = self._read_root_metadata(path)
        screenplay = Screenplay(
            document_type=root_meta.get("DocumentType"),
            version=root_meta.get("Version"),
            meta={"root_attrs": root_meta},
        )

        current_scene: Optional[Scene] = None
        pending_character: Optional[str] = None
        pending_modifiers: list[str] = []
        pending_parts: list[DialoguePart] = []
        pending_para_meta: list[ParagraphInfo] = []
        pending_dual_mode = False
        pending_dual_group: Optional[str] = None

        in_content = False
        content_depth = 0

        context = ET.iterparse(path, events=("start", "end"))
        for event, elem in context:
            tag = self._local_name(elem.tag)

            if event == "start" and tag == "Content":
                in_content = True
                content_depth += 1
                continue

            if event == "end" and tag == "Content":
                content_depth -= 1
                if content_depth <= 0:
                    in_content = False
                elem.clear()
                continue

            if not in_content:
                if event == "end":
                    elem.clear()
                continue

            if event == "end" and tag == "Paragraph":
                p = self._parse_paragraph(elem)
                ptype = p.type

                if ptype == "Scene Heading":
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    heading = SceneHeading(
                        raw=p.raw_text,
                        scene_number=p.attrs.get("Number")
                        or p.attrs.get("SceneNumber"),
                        title=p.scene_properties.get("Title"),
                        page_hint=p.scene_properties.get("Page"),
                        length_hint=p.scene_properties.get("Length"),
                        meta={
                            "paragraph_attrs": p.attrs,
                            "scene_properties": p.scene_properties,
                            "script_notes": p.script_notes,
                        },
                    )
                    current_scene = Scene(
                        id=self._new_id("scene"), heading=heading, meta={}
                    )
                    screenplay.scenes.append(current_scene)

                elif ptype == "Character":
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    name, modifiers = self._split_character_and_modifiers(
                        p.raw_text
                    )
                    pending_character = name
                    pending_modifiers = modifiers
                    pending_para_meta = [p]
                    if self._detect_dual_dialogue(p):
                        pending_dual_mode = True
                        pending_dual_group = self._new_id("dd")

                elif ptype == "Parenthetical":
                    if pending_character:
                        pending_parts.append(
                            DialoguePart(type="parenthetical", text=p.raw_text)
                        )
                        pending_para_meta.append(p)
                    else:
                        self._append_element(
                            screenplay,
                            current_scene,
                            General(
                                text=p.raw_text,
                                meta={
                                    "source_paragraph": asdict(p),
                                    "orphan_parenthetical": True,
                                },
                            ),
                        )

                elif ptype == "Dialogue":
                    if pending_character:
                        pending_parts.append(
                            DialoguePart(type="line", text=p.raw_text)
                        )
                        pending_para_meta.append(p)
                    else:
                        self._append_element(
                            screenplay,
                            current_scene,
                            General(
                                text=p.raw_text,
                                meta={
                                    "source_paragraph": asdict(p),
                                    "orphan_dialogue": True,
                                },
                            ),
                        )

                elif ptype == "Action":
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    self._append_element(
                        screenplay,
                        current_scene,
                        Action(
                            text=p.raw_text,
                            meta={"source_paragraph": asdict(p)},
                        ),
                    )

                elif ptype == "Transition":
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    self._append_element(
                        screenplay,
                        current_scene,
                        Transition(
                            text=p.raw_text,
                            meta={"source_paragraph": asdict(p)},
                        ),
                    )

                elif ptype == "Shot":
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    self._append_element(
                        screenplay,
                        current_scene,
                        Shot(
                            text=p.raw_text,
                            meta={"source_paragraph": asdict(p)},
                        ),
                    )

                elif ptype in {"Lyrics", "Lyric"}:
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    self._append_element(
                        screenplay,
                        current_scene,
                        Lyric(
                            text=p.raw_text,
                            meta={"source_paragraph": asdict(p)},
                        ),
                    )

                else:
                    (
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    ) = self._flush_pending_dialogue(
                        screenplay,
                        current_scene,
                        pending_character,
                        pending_modifiers,
                        pending_parts,
                        pending_para_meta,
                        pending_dual_mode,
                        pending_dual_group,
                    )
                    self._append_element(
                        screenplay,
                        current_scene,
                        General(
                            text=p.raw_text,
                            meta={
                                "source_paragraph": asdict(p),
                                "unknown_paragraph_type": ptype,
                            },
                        ),
                    )

                elem.clear()

        self._flush_pending_dialogue(
            screenplay,
            current_scene,
            pending_character,
            pending_modifiers,
            pending_parts,
            pending_para_meta,
            pending_dual_mode,
            pending_dual_group,
        )

        return self._group_adjacent_dual_dialogue(screenplay)

    def _read_root_metadata(self, path: str) -> dict[str, str]:
        for event, elem in ET.iterparse(path, events=("start",)):
            if self._local_name(elem.tag) == "FinalDraft":
                return dict(elem.attrib)
        return {}

    def _parse_paragraph(self, elem: ET.Element) -> ParagraphInfo:
        attrs = dict(elem.attrib)
        runs: list[InlineRun] = []
        text_parts: list[str] = []
        scene_properties: dict[str, Any] = {}
        script_notes: list[str] = []

        for child in elem:
            ctag = self._local_name(child.tag)
            if ctag == "Text":
                txt = child.text or ""
                runs.append(
                    InlineRun(
                        text=txt,
                        style=child.attrib.get("Style"),
                        font=child.attrib.get("Font"),
                        size=child.attrib.get("Size"),
                        revision_id=child.attrib.get("RevisionID"),
                        raw_attrib=dict(child.attrib),
                    )
                )
                text_parts.append(txt)
            elif ctag == "SceneProperties":
                scene_properties = dict(child.attrib)
            elif ctag == "ScriptNote":
                note_text = "".join(
                    (t.text or "")
                    for t in child.iter()
                    if self._local_name(t.tag) == "Text"
                )
                if note_text.strip():
                    script_notes.append(note_text.strip())

        return ParagraphInfo(
            type=attrs.get("Type", "Unknown"),
            raw_text="".join(text_parts).strip(),
            runs=runs,
            attrs=attrs,
            scene_properties=scene_properties,
            script_notes=script_notes,
        )

    def _split_character_and_modifiers(
        self, raw: str
    ) -> tuple[str, list[str]]:
        raw = raw.strip()
        modifiers: list[str] = []
        first_paren = raw.find("(")
        if first_paren == -1:
            return raw, modifiers
        name = raw[:first_paren].strip()
        pos = first_paren
        while pos < len(raw):
            open_paren = raw.find("(", pos)
            if open_paren == -1:
                break
            close_paren = raw.find(")", open_paren + 1)
            if close_paren == -1:
                break
            inside = raw[open_paren + 1 : close_paren].strip()
            if inside:
                modifiers.append(inside)
            pos = close_paren + 1
        return name, modifiers

    def _detect_dual_dialogue(self, p: ParagraphInfo) -> bool:
        attrs = {k.lower(): v.lower() for k, v in p.attrs.items()}
        for key, val in attrs.items():
            if "dual" in key and val in {"yes", "true", "1"}:
                return True
        return False

    def _flush_pending_dialogue(
        self,
        screenplay: Screenplay,
        current_scene: Optional[Scene],
        pending_character: Optional[str],
        pending_modifiers: list[str],
        pending_parts: list[DialoguePart],
        pending_para_meta: list[ParagraphInfo],
        pending_dual_mode: bool,
        pending_dual_group: Optional[str],
    ) -> tuple[
        Optional[str],
        list[str],
        list[DialoguePart],
        list[ParagraphInfo],
        bool,
        Optional[str],
    ]:
        """Append pending dialogue block if any; return cleared state."""
        if not pending_character:
            return (
                None,
                [],
                [],
                [],
                False,
                None,
            )
        block = DialogueBlock(
            character=pending_character,
            parts=pending_parts[:],
            modifiers=pending_modifiers[:],
            dual=pending_dual_mode,
            dual_group=pending_dual_group,
            meta={
                "source_paragraphs": [asdict(x) for x in pending_para_meta],
            },
        )
        if current_scene is None:
            screenplay.preamble.append(block)
        else:
            current_scene.elements.append(block)
        return (None, [], [], [], False, None)

    def _group_adjacent_dual_dialogue(
        self, screenplay: Screenplay
    ) -> Screenplay:
        return screenplay

    def _append_element(
        self,
        screenplay: Screenplay,
        current_scene: Optional[Scene],
        element: ScreenElement,
    ) -> None:
        if current_scene is None:
            screenplay.preamble.append(element)
        else:
            current_scene.elements.append(element)

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:10]}"

    def _local_name(self, tag: str) -> str:
        return tag.split("}", 1)[-1]
