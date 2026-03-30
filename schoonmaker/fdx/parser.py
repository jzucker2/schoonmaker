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
    TitlePageField,
    Transition,
)


class FDXParser:
    """
    Streaming-ish FDX parser focused on screenplay body content.

    Design choices:
    - parse /FinalDraft/Content/Paragraph for screenplay semantics
    - parse /FinalDraft/TitlePage/Content/Paragraph for title page
    - preserve paragraph attributes and scene properties as metadata
    - group Character + Parenthetical + Dialogue into DialogueBlock
    - treat unknown paragraph types as General
    - treat page/layout hints as metadata, not as structure

    Also parses Revisions, SmartType, Characters (top-level), ScriptNotes,
    DocumentRef, AltCollection, TargetScriptLength. Optional: ``ListItems``
    and ``DisplayBoards`` when enabled — stored on the screenplay but not
    merged into scenes or metadata totals. Other tags: see notes/FDX_TODO.md.
    """

    def __init__(
        self,
        *,
        include_list_items: bool = False,
        include_display_boards: bool = False,
    ) -> None:
        self._include_list_items = include_list_items
        self._include_display_boards = include_display_boards
        # Per-<ListItem>; iterparse clears inner nodes before Paragraph end.
        self._list_item_buf: dict[str, list[Any]] = {
            "subordinates": [],
            "paragraphs": [],
        }
        self._list_item_text_parts: list[str] = []
        self._display_board_item_buf: list[dict[str, str]] = []

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
        in_title_page = False
        stack: list[str] = []

        context = ET.iterparse(path, events=("start", "end"))
        for event, elem in context:
            tag = self._local_name(elem.tag)

            if event == "start":
                if self._include_list_items and tag == "ListItem":
                    self._list_item_buf = {
                        "subordinates": [],
                        "paragraphs": [],
                    }
                    self._list_item_text_parts = []
                if self._include_display_boards and tag == "DisplayBoard":
                    self._display_board_item_buf = []
                if tag == "Content":
                    parent = stack[-1] if stack else None
                    if parent == "FinalDraft":
                        in_content = True
                        content_depth += 1
                    elif parent == "TitlePage":
                        in_title_page = True
                stack.append(tag)
                if tag == "Content":
                    continue

            if event == "end":
                if tag == "Content":
                    content_parent = stack[-2] if len(stack) >= 2 else None
                    if in_title_page and content_parent == "TitlePage":
                        in_title_page = False
                    elif content_parent != "TitlePage":
                        # Only decrement for Content that we incremented:
                        # direct child of FinalDraft (nested Content e.g. under
                        # ListItem never incremented).
                        if content_parent == "FinalDraft":
                            content_depth -= 1
                            assert (
                                content_depth >= 0
                            ), "Content depth went negative"
                            if content_depth <= 0:
                                in_content = False
                    elem.clear()
                    stack.pop()
                    continue

                parent_is_final_draft = (
                    len(stack) >= 2 and stack[-2] == "FinalDraft"
                )
                if tag == "Revisions" and parent_is_final_draft:
                    screenplay.revisions = self._parse_revisions_elem(elem)
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "SmartType" and parent_is_final_draft:
                    screenplay.smart_type = self._parse_smart_type_elem(elem)
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "Characters" and parent_is_final_draft:
                    screenplay.characters = self._parse_characters_elem(elem)
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "ScriptNotes" and parent_is_final_draft:
                    screenplay.script_notes = self._parse_script_notes_elem(
                        elem
                    )
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "DocumentRef" and parent_is_final_draft:
                    screenplay.document_ref.append(
                        self._parse_document_ref_elem(elem)
                    )
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "AltCollection" and parent_is_final_draft:
                    screenplay.alt_collection = (
                        self._parse_alt_collection_elem(elem)
                    )
                    elem.clear()
                    stack.pop()
                    continue
                if tag == "TargetScriptLength" and parent_is_final_draft:
                    screenplay.target_script_length = (
                        self._parse_target_script_length_elem(elem)
                    )
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_display_boards
                    and tag == "DisplayBoard"
                    and len(stack) >= 3
                    and stack[-2] == "DisplayBoards"
                    and stack[-3] == "FinalDraft"
                ):
                    board: dict[str, Any] = {
                        "attrs": dict(elem.attrib),
                        "items": list(self._display_board_item_buf),
                    }
                    screenplay.display_boards.append(board)
                    self._display_board_item_buf = []
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_display_boards
                    and tag == "Item"
                    and len(stack) >= 3
                    and stack[-1] == "Item"
                    and stack[-2] == "DisplayBoard"
                    and stack[-3] == "DisplayBoards"
                ):
                    self._display_board_item_buf.append(dict(elem.attrib))
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_list_items
                    and tag == "ListItem"
                    and len(stack) >= 3
                    and stack[-2] == "ListItems"
                    and stack[-3] == "FinalDraft"
                ):
                    item: dict[str, Any] = {"attrs": dict(elem.attrib)}
                    if self._list_item_buf["subordinates"]:
                        item["subordinate_to"] = [
                            dict(x)
                            for x in self._list_item_buf["subordinates"]
                        ]
                    if self._list_item_buf["paragraphs"]:
                        item["content_paragraphs"] = self._list_item_buf[
                            "paragraphs"
                        ]
                    screenplay.list_items.append(item)
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_list_items
                    and tag == "SubordinateTo"
                    and len(stack) >= 2
                    and stack[-2] == "ListItem"
                    and "ListItems" in stack
                ):
                    self._list_item_buf["subordinates"].append(
                        dict(elem.attrib)
                    )
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_list_items
                    and tag == "Text"
                    and len(stack) >= 5
                    and stack[-1] == "Text"
                    and stack[-2] == "Paragraph"
                    and stack[-3] == "Content"
                    and stack[-4] == "ListItem"
                    and stack[-5] == "ListItems"
                ):
                    self._list_item_text_parts.append(elem.text or "")
                    elem.clear()
                    stack.pop()
                    continue

                if (
                    self._include_list_items
                    and tag == "Paragraph"
                    and len(stack) >= 4
                    and stack[-1] == "Paragraph"
                    and stack[-2] == "Content"
                    and stack[-3] == "ListItem"
                    and stack[-4] == "ListItems"
                ):
                    raw = "".join(self._list_item_text_parts).strip()
                    self._list_item_text_parts = []
                    para = ParagraphInfo(
                        type=elem.attrib.get("Type", "Unknown"),
                        raw_text=raw,
                        runs=[],
                        attrs=dict(elem.attrib),
                        scene_properties={},
                        script_notes=[],
                        alts=None,
                    )
                    self._list_item_buf["paragraphs"].append(asdict(para))
                    elem.clear()
                    stack.pop()
                    continue

                if not in_content and not in_title_page:
                    collectible = (
                        "Revisions",
                        "SmartType",
                        "Characters",
                        "ScriptNotes",
                        "DocumentRef",
                        "AltCollection",
                        "TargetScriptLength",
                    )
                    in_collectible = any(s in stack for s in collectible)
                    if not in_collectible:
                        elem.clear()
                    stack.pop()
                    continue

                if in_title_page and tag == "Paragraph":
                    p = self._parse_paragraph(elem)
                    if p.raw_text.strip():
                        screenplay.title_page.append(
                            TitlePageField(label=None, text=p.raw_text.strip())
                        )
                    elem.clear()
                    stack.pop()
                    continue

                if in_title_page:
                    stack.pop()
                    continue

            if not in_content:
                if event == "end":
                    elem.clear()
                    stack.pop()
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

            if event == "end":
                stack.pop()

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
        alts: Optional[dict[str, Any]] = None

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
            elif ctag == "Alts":
                alt_ids = [
                    (c.text or "").strip()
                    for c in child
                    if self._local_name(c.tag) == "AltId"
                    and (c.text or "").strip()
                ]
                alts = {
                    "Current": child.attrib.get("Current"),
                    "AltIds": alt_ids,
                }

        return ParagraphInfo(
            type=attrs.get("Type", "Unknown"),
            raw_text="".join(text_parts).strip(),
            runs=runs,
            attrs=attrs,
            scene_properties=scene_properties,
            script_notes=script_notes,
            alts=alts,
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

    def _parse_revisions_elem(self, elem: ET.Element) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for child in elem:
            if self._local_name(child.tag) == "Revision":
                out.append(dict(child.attrib))
        return out

    def _parse_document_ref_elem(self, elem: ET.Element) -> dict[str, Any]:
        """Parse a single DocumentRef element under FinalDraft (attribs)."""
        return dict(elem.attrib)

    def _parse_alt_collection_elem(
        self, elem: ET.Element
    ) -> list[dict[str, Any]]:
        """Parse AltCollection: list of Alt entries (Id + text from Paragraph)."""  # noqa: E501
        out: list[dict[str, Any]] = []
        for child in elem:
            if self._local_name(child.tag) != "Alt":
                continue
            entry: dict[str, Any] = dict(child.attrib)
            texts: list[str] = []
            for p in child.iter():
                if self._local_name(p.tag) == "Text" and p.text:
                    texts.append(p.text)
            if texts:
                entry["text"] = "".join(texts).strip()
            out.append(entry)
        return out

    def _parse_target_script_length_elem(
        self, elem: ET.Element
    ) -> Optional[str]:
        """Parse TargetScriptLength: element text (e.g. page count)."""
        text = (elem.text or "").strip()
        return text if text else None

    def _parse_smart_type_elem(self, elem: ET.Element) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for section in elem:
            stag = self._local_name(section.tag)
            if stag == "Characters":
                result["characters"] = []
                for c in section.iter():
                    if self._local_name(c.tag) != "Character":
                        continue
                    text = (c.text or "").strip()
                    if not text and len(c):
                        text = "".join(
                            t.text or ""
                            for t in c
                            if self._local_name(t.tag) == "Text"
                        ).strip()
                    if text:
                        result["characters"].append(text)
            elif stag == "Extensions":
                result["extensions"] = []
                for e in section.iter():
                    if self._local_name(e.tag) != "Extension":
                        continue
                    text = (e.text or "").strip()
                    if not text and len(e):
                        text = "".join(
                            t.text or ""
                            for t in e
                            if self._local_name(t.tag) == "Text"
                        ).strip()
                    if text:
                        result["extensions"].append(text)
            elif stag == "SceneIntros":
                result["scene_intros"] = [
                    (s.text or "").strip()
                    for s in section
                    if self._local_name(s.tag) == "SceneIntro"
                    and (s.text or "").strip()
                ]
            elif stag == "Locations":
                result["locations"] = [
                    (loc.text or "").strip()
                    for loc in section
                    if self._local_name(loc.tag) == "Location"
                    and (loc.text or "").strip()
                ]
            elif stag == "TimesOfDay":
                result["times_of_day"] = [
                    (t.text or "").strip()
                    for t in section
                    if self._local_name(t.tag) == "TimeOfDay"
                    and (t.text or "").strip()
                ]
            elif stag == "Transitions":
                result["transitions"] = [
                    (tr.text or "").strip()
                    for tr in section
                    if self._local_name(tr.tag) == "Transition"
                    and (tr.text or "").strip()
                ]
        return result

    def _parse_characters_elem(self, elem: ET.Element) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for child in elem:
            if self._local_name(child.tag) != "CharacterTraitData":
                continue
            for holders in child:
                if self._local_name(holders.tag) != "Holders":
                    continue
                for h in holders:
                    if self._local_name(h.tag) == "Holder":
                        entry = dict(h.attrib)
                        if entry:
                            out.append(entry)
                break
            break
        if not out:
            for char_elem in elem:
                if self._local_name(char_elem.tag) == "Character":
                    name = (char_elem.text or "").strip()
                    if name:
                        out.append({"Name": name})
        return out

    def _parse_script_notes_elem(
        self, elem: ET.Element
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for note in elem:
            if self._local_name(note.tag) != "ScriptNote":
                continue
            entry = dict(note.attrib)
            texts: list[str] = []
            for p in note.iter():
                if self._local_name(p.tag) == "Text" and p.text:
                    texts.append(p.text)
            entry["text"] = " ".join(texts).strip()
            out.append(entry)
        return out

    def _local_name(self, tag: str) -> str:
        return tag.split("}", 1)[-1]
