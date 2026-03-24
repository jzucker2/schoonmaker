# schoonmaker

Python tool for working with Final Draft `.fdx` screenplay files. It parses FDX XML (via the std lib `xml.etree.ElementTree`), builds a structured screenplay model, and can output a JSON AST or Fountain text.

Features:

- **Parse & summary** – Parse FDX and print a short summary (document type, version, scene count) with `cli.py run`.
- **FDX → JSON AST** – Streaming-style parser producing dataclasses (Scene, DialogueBlock, Action, etc.); emit with `cli.py parse`.
- **FDX → Fountain** – Convert parsed screenplay to Fountain format with `cli.py fountain`.
- **Parse JSON diff** – Compare two `parse` JSON snapshots (e.g. two saves of the same script) with `cli.py diff`; reports word/element deltas, changed scene indices, character and location changes as JSON.

Ultimate goal: GitHub Action, PDF handling, spell check, etc.

## Local development

```bash
# Create venv and install deps
python -m venv venv
venv/bin/pip install -r requirements-dev.txt

# Run tests (pytest; fixtures in tests/fixtures/)
make test

# Format and lint (run both: format then lint; see AGENTS.md if lint fails after format)
make format
make lint
make check
```

## CLI usage

Run with **`python cli.py`** followed by a subcommand and options. Default input is `samples/final_draft_12_sample.fdx` unless `-f` is given.

```bash
# Parse FDX and print summary (document_type, version, scene count)
python cli.py run -f path/to/script.fdx

# Emit FDX → JSON AST to stdout
python cli.py parse -f path/to/script.fdx

# Write JSON AST to a file
python cli.py parse -f path/to/script.fdx -o script.json

# Include computed metadata (scene/character/line counts) in the JSON
python cli.py parse -f path/to/script.fdx -o script.json --metadata

# Add SHA-256 checksums for sections (alts, scenes, etc.) to JSON (for easier diffing)
python cli.py parse -f path/to/script.fdx -o script.json --checksum

# Include source file path, size, and filesystem timestamps in the JSON
python cli.py parse -f path/to/script.fdx -o script.json --file-info

# All optional parse flags together (metadata, checksums, source file stats)
python cli.py parse -f path/to/script.fdx -o script.json \
  --metadata --checksum --file-info

# Emit FDX → Fountain to stdout
python cli.py fountain -f path/to/script.fdx

# Write Fountain to a file
python cli.py fountain -f path/to/script.fdx -o script.fountain

# Compare two parse JSON files (before = earlier save, after = later)
# Use --metadata on both parses for word counts, characters, and locations.
python cli.py diff --before script_v1.json --after script_v2.json -o diff.json

# Same with short flags (-b = --before, -a = --after; stdout if you omit -o)
python cli.py diff -b old.json -a new.json
```

## Docker

Default image command runs `cli.py run` (parse default sample, print summary).

```bash
docker compose build && docker compose run --rm schoonmaker
# Or with your own file (mount a dir and pass -f):
# docker compose run --rm -v "$(pwd)/my-scripts:/data:ro" schoonmaker python cli.py parse -f /data/script.fdx -o /data/out.json
```

Parse JSON output always includes **`nonce`** (unique per run), **`parser_version`** (from `schoonmaker.version`), and **`parse_datetime`** (UTC ISO). With **`--checksum`**, a **`checksums`** object is added with SHA-256 hashes for `alt_collection`, `scenes`, `title_page`, and `preamble` (each is the hash of canonical JSON of that section after normalizing away run-varying IDs). **`scene_checksums`** is a parallel list of SHA-256 digests, one per scene in order, so a diff can show which scene indices changed without re-parsing the full `scenes` array. With **`--file-info`**, a **`source_file`** object records the input path (as given and resolved), basename, **`size_bytes`**, and UTC ISO **`modified`** / **`accessed`** times; **`created`** is included when the OS exposes it (e.g. Windows, macOS).

The **`diff`** subcommand reads two parse JSON files and writes a report with **`scenes`** (counts, **`changed_indices`**, **`added_scene_indices`**, **`removed_scene_indices`**), **`counts`** (word and paragraph totals with before/after/delta), **`elements`** (action, dialogue lines, etc.), **`characters`** (new, removed, line/scene deltas), and **`locations`** (summary and per-location scene-count changes). Pass **`--metadata`** when generating both JSON files for full stats; scene-level changes are always derived from **`scenes`** using the same digest rules as parse checksums (stale **`scene_checksums`** in hand-edited JSON are not trusted).

See **AGENTS.md** for layout, conventions, and full command reference.
