from __future__ import annotations

from pathlib import Path

from fdx_tooling.fountain import screenplay_to_fountain
from fdx_tooling.parser import FDXParser


FIXTURE = Path(__file__).parent / "fixtures" / "sample.fdx"


def test_parse_basic_structure() -> None:
    screenplay = FDXParser().parse(str(FIXTURE))

    assert screenplay.document_type == "Script"
    assert screenplay.version == "3"
    assert len(screenplay.scenes) == 2

    first = screenplay.scenes[0]
    assert first.heading.raw == "INT. APARTMENT - NIGHT"
    assert first.heading.scene_number == "1"
    assert first.heading.page_hint == "1"
    assert first.heading.length_hint == "2/8"

    assert first.elements[0].type == "action"
    assert first.elements[0].text == "John slams the door."

    assert first.elements[1].type == "dialogue_block"
    assert first.elements[1].character == "JOHN"
    assert first.elements[1].modifiers == ["V.O."]
    assert [p.type for p in first.elements[1].parts] == ["parenthetical", "line"]
    assert [p.text for p in first.elements[1].parts] == ["whispering", "Hello?"]

    assert first.elements[2].type == "transition"
    assert first.elements[2].text == "CUT TO:"


def test_convert_to_fountain() -> None:
    screenplay = FDXParser().parse(str(FIXTURE))
    fountain = screenplay_to_fountain(screenplay)

    assert "INT. APARTMENT - NIGHT #1#" in fountain
    assert "JOHN" in fountain
    assert "(whispering)" in fountain
    assert "Hello?" in fountain
    assert "> CUT TO:" in fountain
    assert "EXT. STREET - LATER #2#" in fountain
