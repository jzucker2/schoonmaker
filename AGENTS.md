# Agent instructions (schoonmaker)

This repo is a **Python tool** for working with Final Draft `.fdx` screenplay files. It parses FDX XML, builds a structured model, and can output JSON AST or Fountain text, or diff two parse JSON snapshots.

## Layout

- **`schoonmaker/`** – Main package.
  - **`fdx/`** – FDX parsing and export (single parser path):
    - **`models.py`** – Dataclasses for Screenplay, Scene, SceneHeading, DialogueBlock, Action, Transition, etc.
    - **`parser.py`** – `FDXParser`: streaming-ish parser that produces `Screenplay` from an FDX path.
    - **`fountain.py`** – `screenplay_to_fountain(screenplay)` for FDX → Fountain text.
  - **`cli_arg_parser.py`** – CLI argument parsing (file path, subcommands).
  - **`metadata.py`** – `compute_screenplay_metadata(screenplay)` for scene/character/line stats (used when `parse --metadata`).
  - **`source_file_info.py`** – `source_file_info(path)` for optional `parse --file-info` JSON (`path_resolved`, `size_bytes`, timestamps).
  - **`parse_json_diff.py`** – `build_diff_report`, `load_parse_json`, `scene_digests` for `cli.py diff`.
  - **`utils.py`** – Logging helpers.
- **`cli.py`** – Entry point: subcommands `run`, `parse`, `fountain`, `diff` (see Commands). Parse output always includes `nonce`, `parser_version`, `parse_datetime`; with `--checksum`, adds a `checksums` object (SHA-256 per section plus `scene_checksums`, one digest per scene in order).
- **`tests/`** – Unified test suite (pytest). **`tests/fixtures/`** – FDX and other test fixtures (e.g. `sample.fdx`).
- **`samples/`** – Sample FDX files for manual use.
- **`requirements.txt`** – Runtime deps (empty or minimal for stdlib-only use).
- **`requirements-dev.txt`** – Dev deps: black, flake8, pytest, pytest-cov, pre-commit, etc.
- **`Makefile`** – `make test`, `make check`, `make format`, `make lint`, `make ci-check`.
- **`.flake8`**, **`.pre-commit-config.yaml`** – Lint and pre-commit config. **`.yamllint`** – YAML style (2-space indent, no `---`).

## Environment

Use the **existing local venv** at the repo root:

- Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows).
- Run CLI: `python cli.py …` (or `venv/bin/python cli.py …` without activating).
- Run tests: `make test` (pytest) or `pytest -v` from repo root with venv active.

If the venv is missing or broken: `python -m venv venv` then `venv/bin/pip install -r requirements-dev.txt`.

## Commands (from repo root, with venv)

Options like `-f`/`--file` are per-subcommand; pass them after the command (e.g. `cli.py run -f file.fdx`).

```bash
# Parse FDX and print a short summary (document_type, version, scene count)
python cli.py run -f path/to/script.fdx

# Emit FDX → JSON AST to stdout
python cli.py parse -f path/to/script.fdx

# Write JSON AST to a file
python cli.py parse -f path/to/script.fdx -o script.json

# Include computed metadata (scene/character/line counts) in the JSON
python cli.py parse -f path/to/script.fdx -o script.json --metadata

# Add SHA-256 checksums for sections to JSON (for easier diffing)
python cli.py parse -f path/to/script.fdx -o script.json --checksum

# Include source file path, size, and timestamps in JSON
python cli.py parse -f path/to/script.fdx -o script.json --file-info

# All optional parse flags together (metadata, checksums, source file stats)
python cli.py parse -f path/to/script.fdx -o script.json \
  --metadata --checksum --file-info

# Diff two parse JSON files (JSON report to stdout or -o)
python cli.py diff --before older.json --after newer.json
python cli.py diff -a older.json -b newer.json -o report.json

# Emit FDX → Fountain to stdout
python cli.py fountain -f path/to/script.fdx

# Write Fountain to a file
python cli.py fountain -f path/to/script.fdx -o script.fountain

# Run tests
make test

# Format and lint (run both before committing)
make format
make lint
make check

# Pre-commit on all files
make pre-commit-run

# Full CI-style check (pre-commit + tests)
make ci-check
```

## Conventions

- **YAML:** Use `.yamllint`; prefer 2-space indent, no document-start `---`.
- **Python:** 3.9+ (e.g. `list[...]`, `str | None`). Tests use **pytest**; put fixtures in **`tests/fixtures/`** and reference them from tests (e.g. `Path(__file__).parent / "fixtures" / "sample.fdx"`).
- **Format and lint:** Black (`make format`) uses `--line-length=79` but does **not** shorten every long line (e.g. comments and docstrings are often left as-is). Flake8 E501 fails on **any** line over 79 characters. So after `make format`, run **`make lint`** (or `make check`); fix any E501 by shortening those lines (break or reword comments/docstrings) so both format and lint pass.
- **When adding or changing behavior:**
  - Keep **README** and this **AGENTS.md** in sync; update README when CLI, layout, or usage changes.
  - Add or update tests in **`tests/`** for new or modified behavior; for bug fixes, add or adjust tests when reasonable so the fix is covered.
  - Keep files at a **reasonable length**; split modules or extract helpers when a file grows large or a distinct responsibility appears, so the codebase stays navigable.
