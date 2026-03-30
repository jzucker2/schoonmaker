# Agent instructions (schoonmaker)

This repo is a **Python tool** for working with Final Draft `.fdx` screenplay files. It parses FDX XML, builds a structured model, and can output JSON AST or Fountain text, or diff two parse JSON snapshots.

## Layout

- **`pyproject.toml`** – Package metadata and the **`schoonmaker`** console script (`setuptools`).
- **`schoonmaker/`** – Main package.
  - **`cli.py`** – CLI implementation: `main()`, `run_parse`, `run_diff`, checksum helpers, etc.
  - **`__main__.py`** – Supports **`python -m schoonmaker`**.
  - **`fdx/`** – FDX parsing and export (single parser path):
    - **`models.py`** – Dataclasses for Screenplay, Scene, SceneHeading, DialogueBlock, Action, Transition, etc.
    - **`parser.py`** – `FDXParser`: streaming-ish parser that produces `Screenplay` from an FDX path.
    - **`fountain.py`** – `screenplay_to_fountain(screenplay)` for FDX → Fountain text.
  - **`cli_arg_parser.py`** – CLI argument parsing (file path, subcommands).
  - **`metadata.py`** – `compute_screenplay_metadata(screenplay)` for scene/character/line stats (used when `parse --metadata`).
  - **`source_file_info.py`** – `source_file_info(path)` for optional `parse --file-info` JSON (`path_resolved`, `size_bytes`, timestamps).
  - **`parse_json_diff.py`** – `build_diff_report`, `load_parse_json`, `scene_digests` for `schoonmaker diff`.
  - **`ci_fdx_diff.py`** – `run_ci_fdx_diff`, `resolve_base_sha`, etc. for `schoonmaker ci-fdx-diff` (git + parse + diff).
  - **`ci_report_md.py`** – `markdown_from_ci_reports` for `schoonmaker ci-report-md` (GitHub Step Summary).
  - **`utils.py`** – Logging helpers; `strip_run_varying_ids` (shared checksum / diff normalization).
- **`cli.py`** (repo root) – Thin shim calling `schoonmaker.cli:main` so **`python cli.py`** still works from a clone without installing.
- **`tests/`** – Unified test suite (pytest). **`tests/fixtures/`** – FDX and other test fixtures (e.g. `sample.fdx`).
- **`samples/`** – Sample FDX files for manual use.
- **`examples/`** – GitHub Actions templates (`github-actions-fdx-changes-*.yml`),
  **`requirements-ci.txt`**, and **`examples/README.md`**. They should mirror real
  CLI usage (see **When adding or changing behavior** below).
- **`requirements.txt`** – Runtime deps (empty or minimal for stdlib-only use).
- **`requirements-dev.txt`** – `-e .` plus dev deps: black, flake8, pytest, pytest-cov, pre-commit, etc.
- **`Makefile`** – `make test`, `make check`, `make format`, `make lint`, `make ci-check`.
- **`.flake8`**, **`.pre-commit-config.yaml`** – Lint and pre-commit config. **`.yamllint`** – YAML style (2-space indent, no `---`).

## Environment

Use the **existing local venv** at the repo root:

- Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows).
- Install: **`pip install -r requirements-dev.txt`** (editable package + dev tools), or **`pip install .`** for runtime only.
- Run CLI: **`schoonmaker …`**, or **`python -m schoonmaker …`**, or **`python cli.py …`** from the repo root (wrapper).
- Run tests: `make test` (pytest) or `pytest -v` from repo root with venv active.

If the venv is missing or broken: `python -m venv venv` then `venv/bin/pip install -r requirements-dev.txt`.

## Commands (from repo root, with venv)

Options like `-f`/`--file` are per-subcommand; pass them after the command (e.g. `schoonmaker run -f file.fdx`).

```bash
# Parse FDX and print a short summary (document_type, version, scene count)
schoonmaker run -f path/to/script.fdx

# Emit FDX → JSON AST to stdout
schoonmaker parse -f path/to/script.fdx

# Write JSON AST to a file
schoonmaker parse -f path/to/script.fdx -o script.json

# Include computed metadata (scene/character/line counts) in the JSON
schoonmaker parse -f path/to/script.fdx -o script.json --metadata

# Add SHA-256 checksums for sections to JSON (for easier diffing)
schoonmaker parse -f path/to/script.fdx -o script.json --checksum

# Include source file path, size, and timestamps in JSON
schoonmaker parse -f path/to/script.fdx -o script.json --file-info

# Include <ListItems> beat board in JSON (excluded from --metadata script totals)
schoonmaker parse -f path/to/script.fdx -o script.json --list-items

# Include <DisplayBoards> Story Map / Beat layout (excluded from --metadata totals)
schoonmaker parse -f path/to/script.fdx -o script.json --display-boards

# All optional parse flags together (metadata, checksums, source file stats)
schoonmaker parse -f path/to/script.fdx -o script.json \
  --metadata --checksum --file-info

# Diff two parse JSON files (JSON report to stdout or -o)
schoonmaker diff --before older.json --after newer.json
schoonmaker diff -b older.json -a newer.json -o report.json

# Changed .fdx between two git commits (CI); optional env CI_FDX_BASE_SHA / CI_FDX_HEAD_SHA
schoonmaker ci-fdx-diff -o fdx-reports --base-sha "$BASE" --head-sha "$HEAD"

# Same with beat-board parse extras (or set CI_FDX_LIST_ITEMS / CI_FDX_DISPLAY_BOARDS)
schoonmaker ci-fdx-diff -o fdx-reports --list-items --display-boards

# Markdown summary of ci-fdx-diff output (append to GITHUB_STEP_SUMMARY in Actions)
schoonmaker ci-report-md fdx-reports

# Emit FDX → Fountain to stdout
schoonmaker fountain -f path/to/script.fdx

# Write Fountain to a file
schoonmaker fountain -f path/to/script.fdx -o script.fountain

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

Parse output always includes `nonce`, `parser_version`, `parse_datetime`; with `--checksum`, adds a `checksums` object (SHA-256 per section plus `scene_checksums`, one digest per scene in order).

## Conventions

- **YAML:** Use `.yamllint`; prefer 2-space indent, no document-start `---`.
- **Python:** 3.9+ (e.g. `list[...]`, `str | None`). Tests use **pytest**; put fixtures in **`tests/fixtures/`** and reference them from tests (e.g. `Path(__file__).parent / "fixtures" / "sample.fdx"`).
- **Format and lint:** Black (`make format`) uses `--line-length=79` but does **not** shorten every long line (e.g. comments and docstrings are often left as-is). Flake8 E501 fails on **any** line over 79 characters. So after `make format`, run **`make lint`** (or `make check`); fix any E501 by shortening those lines (break or reword comments/docstrings) so both format and lint pass.
- **When adding or changing behavior:**
  - Keep **README** and this **AGENTS.md** in sync; update README when CLI, layout, or usage changes.
  - Keep **`examples/`** in sync with the **parser**, **CLI**, **`parse`/`diff`**
    output, **`ci-fdx-diff`**, and anything those workflows depend on (flags,
    env vars, artifact layout, install instructions).
  - When CI usage of schoonmaker changes, update the workflow YAML under
    **`examples/`**, **`examples/requirements-ci.txt`** if install or pinning
    changes, and **`examples/README.md`** so copied templates stay accurate.
  - Add or update tests in **`tests/`** for new or modified behavior; for bug fixes, add or adjust tests when reasonable so the fix is covered.
  - Keep files at a **reasonable length**; split modules or extract helpers when a file grows large or a distinct responsibility appears, so the codebase stays navigable.
