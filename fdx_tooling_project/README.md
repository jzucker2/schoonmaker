# fdx-tooling

A small Python package for working with Final Draft `.fdx` files.

It includes:

- a streaming-ish FDX parser
- an FDX → JSON AST CLI
- an FDX → Fountain converter
- tests and a sample fixture

## Install

```bash
pip install -e .
```

## CLI usage

Print JSON AST to stdout:

```bash
fdx-tool parse path/to/script.fdx
```

Write JSON AST to a file:

```bash
fdx-tool parse path/to/script.fdx -o script.json
```

Convert to Fountain:

```bash
fdx-tool fountain path/to/script.fdx
```

Write Fountain to a file:

```bash
fdx-tool fountain path/to/script.fdx -o script.fountain
```

## Notes

This parser intentionally treats pages and other layout hints as metadata instead of core screenplay structure.
