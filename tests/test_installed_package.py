"""Install the project in an isolated venv and exercise the CLI entry points."""  # noqa: E501

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_console_script(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "schoonmaker.exe"
    return venv_dir / "bin" / "schoonmaker"


@pytest.fixture(scope="module")
def venv_with_package(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Fresh venv with ``pip install -e .`` for this repo."""
    root = tmp_path_factory.mktemp("venv_pkg")
    venv.create(root, with_pip=True)
    py = _venv_python(root)
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "-e", str(REPO_ROOT)],
        check=True,
        cwd=str(REPO_ROOT),
    )
    return root


def test_pip_show_schoonmaker(venv_with_package: Path) -> None:
    py = _venv_python(venv_with_package)
    r = subprocess.run(
        [str(py), "-m", "pip", "show", "schoonmaker"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "Name: schoonmaker" in r.stdout


def test_console_script_run_help(venv_with_package: Path) -> None:
    exe = _venv_console_script(venv_with_package)
    r = subprocess.run(
        [str(exe), "run", "-h"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    out = (r.stdout + r.stderr).lower()
    assert "run" in out


def test_python_m_schoonmaker_parse_help(venv_with_package: Path) -> None:
    py = _venv_python(venv_with_package)
    r = subprocess.run(
        [str(py), "-m", "schoonmaker", "parse", "-h"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "parse" in (r.stdout + r.stderr).lower()


def test_console_script_diff_help(venv_with_package: Path) -> None:
    exe = _venv_console_script(venv_with_package)
    r = subprocess.run(
        [str(exe), "diff", "-h"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "diff" in (r.stdout + r.stderr).lower()
