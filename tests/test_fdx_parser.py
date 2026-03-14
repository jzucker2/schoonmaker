"""Tests for schoonmaker.fdx parser and Fountain export."""

from pathlib import Path

from schoonmaker.fdx import FDXParser, screenplay_to_fountain


def test_split_character_and_modifiers_multiple_parentheticals():
    """Multiple (V.O.) (CONT'D) etc. are parsed as separate modifiers."""
    parser = FDXParser()
    name, modifiers = parser._split_character_and_modifiers(
        "JOHN (V.O.) (CONT'D)"
    )
    assert name == "JOHN"
    assert modifiers == ["V.O.", "CONT'D"]


def test_split_character_and_modifiers_single_modifier():
    parser = FDXParser()
    name, modifiers = parser._split_character_and_modifiers("JANE (O.S.)")
    assert name == "JANE"
    assert modifiers == ["O.S."]


def test_parse_title_page():
    """Title page (FinalDraft/TitlePage/Content) is parsed into title_page."""
    path = Path(__file__).parent / "fixtures" / "sample_with_title_page.fdx"
    screenplay = FDXParser().parse(str(path))
    assert len(screenplay.title_page) >= 3
    texts = [f.text for f in screenplay.title_page]
    assert "My Script Title" in texts
    assert "Written by" in texts
    assert "Jane Doe" in texts
    assert len(screenplay.scenes) == 1
    assert screenplay.scenes[0].heading.raw == "INT. ROOM - DAY"


def test_parse_basic_structure(sample_fdx_path):
    screenplay = FDXParser().parse(str(sample_fdx_path))

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
    assert [p.type for p in first.elements[1].parts] == [
        "parenthetical",
        "line",
    ]
    assert [p.text for p in first.elements[1].parts] == [
        "whispering",
        "Hello?",
    ]

    assert first.elements[2].type == "transition"
    assert first.elements[2].text == "CUT TO:"


def test_convert_to_fountain(sample_fdx_path):
    screenplay = FDXParser().parse(str(sample_fdx_path))
    fountain = screenplay_to_fountain(screenplay)

    assert "INT. APARTMENT - NIGHT #1#" in fountain
    assert "JOHN (V.O.)" in fountain
    assert "(whispering)" in fountain
    assert "Hello?" in fountain
    assert "> CUT TO:" in fountain
    assert "EXT. STREET - LATER #2#" in fountain


def test_parse_fdx13_sample(sample_fdx13_path):
    """Parse FDX 13 sample (samples/final_draft_13_sample.fdx)."""
    screenplay = FDXParser().parse(str(sample_fdx13_path))
    assert screenplay.document_type == "Script"
    assert screenplay.version == "6"
    assert len(screenplay.document_ref) >= 1
    assert len(screenplay.scenes) >= 1
