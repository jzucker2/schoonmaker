# FDX tags

The parser reads:

- `FinalDraft` (root attributes)
- `TitlePage > Content > Paragraph` (title page lines)
- `Content > Paragraph` (script body: scenes, dialogue, action, etc.)
- **Revisions** – revision definitions (ID, Name, Mark, etc.) → `screenplay.revisions`
- **SmartType** – characters, extensions, scene_intros, locations, times_of_day, transitions → `screenplay.smart_type`
- **Characters** (top-level) – from CharacterTraitData/Holders or Character list → `screenplay.characters`
- **ScriptNotes** – note entries (Name, Range, Type, WriterName, text) → `screenplay.script_notes`
- **DocumentRef** – ref entries (e.g. DateTime, id; optional in FDX 13+) → `screenplay.document_ref`
- **AltCollection** – alternate dialogue/lines (Alt with Id + Paragraph/Text) → `screenplay.alt_collection`
- **TargetScriptLength** – target length text (e.g. page count) → `screenplay.target_script_length`

The following FDX tags are **not** yet parsed.

## Other tags (do later)

| Tag | Description |
|-----|-------------|
| MoresAndContinueds | (MORE) / (CONT'D) / CONTINUED formatting |
| LockedPages | Locked page definitions |
| SplitState | Split view / script panel state |
| Macros | Keyboard shortcuts and macro text |
| TagData | Tag categories and colors |
| CastList | Cast list sort option |
| Cast | Cast member definitions |
| Actors | Actor definitions |
| HeaderAndFooter | Header/footer content and visibility |
| PageLayout | Margins, colors, document leading |
| Watermarking | Watermark opacity and position |
| WindowState | Window size and mode |
| TextState | Scaling, selection, invisibles |
| ElementSettings | Paragraph type settings |
| SceneNumberOptions | Scene number display options |
| Writers | Writer list (for ScriptNotes) |
| WriterMarkup | Writer markup state |

## Final Draft 13 (FDX 13)

- **Root version:** FDX 12 uses `Version="5"`, FDX 13 uses `Version="6"` on `<FinalDraft>`.
- **DocumentRef:** Optional; appears in FDX 13+ as a direct child of `FinalDraft` (e.g. `DateTime`, `id`). Not present in FDX 12 files. Parsed → `screenplay.document_ref`.
- **Samples:** `samples/final_draft_12_sample.fdx` (no DocumentRef), `samples/final_draft_13_sample.fdx` (has DocumentRef). Tests `test_parse_document_ref_fdx13_has_ref` and `test_parse_document_ref_fdx12_empty` confirm this.

## Tests

- **Smoke:** `test_parse_fdx_with_unparsed_tags_succeeds` – parse an FDX with Revisions, SmartType, etc.; assert no crash.
- **Full:** `test_parse_revisions`, `test_parse_smart_type`, `test_parse_characters`, `test_parse_script_notes` – assert parsed content (see `tests/test_fdx_unparsed_tags.py` and fixture `sample_with_starter_tags.fdx`).
- **DocumentRef / FDX 13:** `test_parse_document_ref_fdx13_has_ref`, `test_parse_document_ref_fdx12_empty` – FDX 13 sample has `document_ref`; FDX 12 sample has none. `test_parse_fdx13_sample` parses `samples/final_draft_13_sample.fdx`.
- **AltCollection / TargetScriptLength:** `test_parse_alt_collection`, `test_parse_target_script_length` – samples have AltCollection (Alt entries with Id + text) and TargetScriptLength (e.g. "30").
