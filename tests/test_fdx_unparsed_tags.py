"""FDX Revisions, SmartType, Characters, ScriptNotes, DocumentRef, AltCollection, TargetScriptLength tests."""  # noqa: E501

from pathlib import Path

from schoonmaker.fdx import FDXParser

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_WITH_STARTER_TAGS = (
    Path(__file__).parent / "fixtures" / "sample_with_starter_tags.fdx"
)
SAMPLE_FDX12 = REPO_ROOT / "samples" / "final_draft_12_sample.fdx"
SAMPLE_FDX13 = REPO_ROOT / "samples" / "final_draft_13_sample.fdx"


def test_parse_fdx_with_unparsed_tags_succeeds():
    """Smoke: FDX with Revisions, SmartType, etc. parses OK."""
    assert FIXTURE_WITH_STARTER_TAGS.exists(), "need fixture"
    screenplay = FDXParser().parse(str(FIXTURE_WITH_STARTER_TAGS))
    assert screenplay is not None
    assert screenplay.document_type == "Script"
    assert len(screenplay.scenes) >= 1
    assert screenplay.scenes[0].heading.raw == "INT. ROOM - DAY"


def test_parse_revisions():
    """screenplay.revisions is a list of revision defs (ID, Name, Mark)."""
    screenplay = FDXParser().parse(str(FIXTURE_WITH_STARTER_TAGS))
    assert len(screenplay.revisions) >= 1
    first = screenplay.revisions[0]
    assert "Name" in first or "name" in first
    name = first.get("Name") or first.get("name")
    assert name == "Blue Rev."


def test_parse_smart_type():
    """smart_type has characters, extensions (and optionally scene_intros)."""
    screenplay = FDXParser().parse(str(FIXTURE_WITH_STARTER_TAGS))
    st = screenplay.smart_type
    assert "characters" in st
    chars = st["characters"]
    assert "ALICE" in chars
    assert "BOB" in chars
    assert "extensions" in st
    assert "(V.O.)" in st["extensions"]


def test_parse_characters():
    """characters is list of entries (Name from Holder, optional attrs)."""
    screenplay = FDXParser().parse(str(FIXTURE_WITH_STARTER_TAGS))
    assert len(screenplay.characters) >= 1
    names = [c.get("Name") or c.get("name") for c in screenplay.characters]
    assert "ALICE" in names
    assert "BOB" in names


def test_parse_script_notes():
    """script_notes is list of note entries (Name, Range, Type, text)."""
    screenplay = FDXParser().parse(str(FIXTURE_WITH_STARTER_TAGS))
    assert len(screenplay.script_notes) >= 1
    first = screenplay.script_notes[0]
    assert first.get("Name") == "Note One" or first.get("name") == "Note One"
    text = first.get("text") or ""
    assert "First script note" in text


def test_parse_document_ref_fdx13_has_ref():
    """FDX 13 sample has DocumentRef (optional in FDX 13+, not in 12)."""
    assert SAMPLE_FDX13.exists(), "need samples/final_draft_13_sample.fdx"
    screenplay = FDXParser().parse(str(SAMPLE_FDX13))
    assert len(screenplay.document_ref) >= 1
    ref = screenplay.document_ref[0]
    assert ref.get("id") or ref.get("Id")
    assert ref.get("DateTime") or ref.get("datetime")


def test_parse_document_ref_fdx12_empty():
    """FDX 12 sample has no DocumentRef; list is empty."""
    assert SAMPLE_FDX12.exists(), "need samples/final_draft_12_sample.fdx"
    screenplay = FDXParser().parse(str(SAMPLE_FDX12))
    assert screenplay.document_ref == []


def test_parse_alt_collection():
    """alt_collection is list of Alt entries (Id + text from Paragraph/Text)."""  # noqa: E501
    assert SAMPLE_FDX12.exists(), "need samples/final_draft_12_sample.fdx"
    screenplay = FDXParser().parse(str(SAMPLE_FDX12))
    assert len(screenplay.alt_collection) >= 1
    first = screenplay.alt_collection[0]
    assert first.get("Id") or first.get("id")
    assert "text" in first
    assert "Better checkity-check yourself" in first["text"]


def test_parse_target_script_length():
    """target_script_length is element text (e.g. page count)."""
    assert SAMPLE_FDX12.exists(), "need samples/final_draft_12_sample.fdx"
    screenplay = FDXParser().parse(str(SAMPLE_FDX12))
    assert screenplay.target_script_length == "30"
