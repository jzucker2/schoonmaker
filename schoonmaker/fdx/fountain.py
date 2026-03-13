from __future__ import annotations

from .models import (
    Action,
    DialogueBlock,
    General,
    Lyric,
    Screenplay,
    Shot,
    Transition,
)


def screenplay_to_fountain(screenplay: Screenplay) -> str:
    lines: list[str] = []

    for field in screenplay.title_page:
        if field.label:
            lines.append(f"{field.label}: {field.text}")
        else:
            lines.append(field.text)
    if screenplay.title_page:
        lines.append("")

    for el in screenplay.preamble:
        lines.extend(_element_to_fountain_lines(el))
        lines.append("")

    for scene in screenplay.scenes:
        heading = scene.heading.raw
        if scene.heading.scene_number:
            heading = f"{heading} #{scene.heading.scene_number}#"
        lines.append(heading)
        lines.append("")
        for el in scene.elements:
            lines.extend(_element_to_fountain_lines(el))
            lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines) + "\n"


def _element_to_fountain_lines(el: object) -> list[str]:
    if isinstance(el, Action):
        return [el.text]

    if isinstance(el, Transition):
        text = el.text
        if not text.startswith(">"):
            text = f"> {text}"
        return [text]

    if isinstance(el, Shot):
        return [el.text]

    if isinstance(el, General):
        return [el.text]

    if isinstance(el, Lyric):
        return [f"~{el.text}"]

    if isinstance(el, DialogueBlock):
        out = [el.character]
        for part in el.parts:
            if part.type == "parenthetical":
                out.append(
                    f"({part.text})"
                    if not (
                        part.text.startswith("(") and part.text.endswith(")")
                    )
                    else part.text
                )
            else:
                out.append(part.text)
        return out

    raise TypeError(f"Unsupported element type: {type(el)!r}")
