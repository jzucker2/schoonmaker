# schoonmaker

Python tool for working with Final Draft `.fdx` screenplay files. It parses FDX XML (via the std lib `xml.etree.ElementTree`), builds a structured screenplay model, and can output a JSON AST or Fountain text.

Features:

- **Low-level parse** – Traverse FDX `Content` / `Paragraph` and log structure (`cli.py run`).
- **FDX → JSON AST** – Streaming-style parser producing dataclasses (Scene, DialogueBlock, Action, etc.); emit with `cli.py parse`.
- **FDX → Fountain** – Convert parsed screenplay to Fountain format with `cli.py fountain`.

Ultimate goal: GitHub Action, PDF handling, spell check, etc.

## Local development

```bash
# Create venv and install deps
python -m venv venv
venv/bin/pip install -r requirements-dev.txt

# Run tests (pytest; fixtures in tests/fixtures/)
make test

# Format and lint
make format
make check
```

## CLI usage

Default input file is `samples/final_draft_12_sample.fdx` unless `-f` is given.

```bash
# Naive parse (logs Content/Paragraph traversal)
python cli.py run -f path/to/script.fdx

# Emit FDX → JSON AST to stdout
python cli.py parse -f path/to/script.fdx

# Write JSON AST to a file
python cli.py parse -f path/to/script.fdx -o script.json

# Emit FDX → Fountain to stdout
python cli.py fountain -f path/to/script.fdx

# Write Fountain to a file
python cli.py fountain -f path/to/script.fdx -o script.fountain
```

See **AGENTS.md** for layout, conventions, and full command reference.
