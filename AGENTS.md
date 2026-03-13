# Agent instructions (albion-esphome-admin)

This repo is an **admin** project for syncing dependencies and workflow config across multiple local albion-esphome repos.

## Layout

- **`repos.yaml`** – List of local repo paths under `repos:` (absolute or relative). Optional **`graybox`** block with `old_ref` and `new_ref`: the script replaces the graybox tag `old_ref` with `new_ref` in any YAML/yml file that contains “graybox” (e.g. package blocks with `ref: 1.3.6`).
- **`requirements.txt`** – Canonical Python deps (sync payload); copied into each repo by the sync script. Do not use for `pip install` in this repo.
- **`requirements-runtime.txt`** – This project’s runtime deps (PyYAML only); use for `make install` or minimal venv.
- **`upgrade-requirements.txt`** – Single line `esphome==X.Y.Z`. That version is written into each repo’s `.github/workflows/build.yml` under `esphome-version:`.
- **`scripts/sync_requirements.py`** – Script that:
  1. Reads `repos.yaml` and finds project root (directory containing `repos.yaml`).
  2. Copies this repo’s `requirements.txt` into each listed repo (overwrites their `requirements.txt`).
  3. Reads esphome version from `upgrade-requirements.txt` and updates `esphome-version:` in each repo’s `.github/workflows/build.yml` (if that file exists).
  4. If `graybox.old_ref` and `graybox.new_ref` are set in `repos.yaml`, replaces that tag in each repo in any YAML/yml file that contains “graybox” (whole-token replacement, e.g. `ref: 1.3.6` → `ref: 1.3.7`).
- **`tests/`** – Unit tests for the sync script (unittest, no pytest). **When adding or changing script behavior, add or update unit tests and keep README/AGENTS.md in sync.**

## Environment

Use the **existing local venv** at the repo root:

- Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows).
- Run script: `python scripts/sync_requirements.py` (or `venv/bin/python scripts/sync_requirements.py` without activating).
- Run tests: `python -m unittest discover -s tests -v` (from repo root, with venv so PyYAML is available).

If the venv is missing or broken: `python -m venv venv` then `venv/bin/pip install -r requirements-runtime.txt` (or `requirements-dev.txt` for tests/lint).

## Commands (from repo root, with venv)

```bash
# Sync all repos (writes requirements.txt + build.yml esphome-version)
python scripts/sync_requirements.py

# Preview only (no file writes)
python scripts/sync_requirements.py --dry-run

# Run unit tests
python -m unittest discover -s tests -v

# Pre-commit (use venv: venv/bin/pre-commit or activate first)
venv/bin/pre-commit run --all-files
```

## Conventions

- **YAML:** Repo uses `.yamllint`; prefer 2-space indent, no document-start `---`.
- **Python:** Script is 3.9+ (uses `list[Path]`, `str | None`). No pytest; tests use `unittest` and temp files.
- **When changing the sync script or config:** Add or update **unit tests** in `tests/` for the new or modified behavior, and update **README** (and this **AGENTS.md**) so usage and config are documented.
