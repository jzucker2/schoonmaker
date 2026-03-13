# FDX tags

The parser reads:

- `FinalDraft` (root attributes)
- `TitlePage > Content > Paragraph` (title page lines)
- `Content > Paragraph` (script body: scenes, dialogue, action, etc.)
- **Revisions** – revision definitions (ID, Name, Mark, etc.) → `screenplay.revisions`
- **SmartType** – characters, extensions, scene_intros, locations, times_of_day, transitions → `screenplay.smart_type`
- **Characters** (top-level) – from CharacterTraitData/Holders or Character list → `screenplay.characters`
- **ScriptNotes** – note entries (Name, Range, Type, WriterName, text) → `screenplay.script_notes`

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

## Tests

- **Smoke:** `test_parse_fdx_with_unparsed_tags_succeeds` – parse an FDX with the four starter tags; assert no crash.
- **Full:** `test_parse_revisions`, `test_parse_smart_type`, `test_parse_characters`, `test_parse_script_notes` – assert parsed content (see `tests/test_fdx_unparsed_tags.py` and fixture `sample_with_starter_tags.fdx`).
