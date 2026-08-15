"""`haus doctor` — one command that answers "is this checkout wired up correctly?".

Every fact printed here was, at some point, rediscovered from scratch at the start of a
session: which interpreter, whether `typehaus` is the checkout or a stale copy, whether the
UI has been built, whether a server is already holding the port, and — the one that has bitten
this repo hardest — whether a `.gitignore` pattern is quietly swallowing a source tree.

Deliberately read-only and dependency-free: it must run *before* anything else works, so it
imports nothing from the engine beyond the version string and never touches a house.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import typer

from typehaus.cli._shared import app, console

# Trees that must never be ignored. `git check-ignore` over these is what makes the
# unanchored-pattern bug class (a `build/` rule matching `ui/src/three/build/`) announce
# itself instead of waiting to be found by a missing import in a shipped commit.
_SOURCE_TREES = ("packages", "ui", "library", "houses", "scripts")

_OK, _WARN, _INFO = "ok", "warn", "--"


@dataclass(frozen=True)
class _Row:
    name: str
    detail: str
    status: str


def _repo_root() -> Path | None:
    """The checkout this command was run from, or None when run outside one."""
    for node in (Path.cwd(), *Path.cwd().parents):
        if (node / ".git").exists():
            return node
    return None


def _python_row() -> _Row:
    prefix = Path(sys.prefix)
    in_venv = sys.prefix != sys.base_prefix
    where = f"({prefix.name})" if in_venv else "(system interpreter, no venv)"
    version = ".".join(str(x) for x in sys.version_info[:3])
    return _Row("python", f"{version:8} {where}", _OK if in_venv else _WARN)


def _install_row(root: Path | None) -> _Row:
    import typehaus

    src = Path(typehaus.__file__).resolve().parent.parent
    if root is not None and src == (root / "packages" / "engine" / "src").resolve():
        return _Row("typehaus", f"editable -> {src.relative_to(root)}", _OK)
    if root is None:
        return _Row("typehaus", f"installed at {src}", _INFO)
    # A non-editable install in a checkout means every edit under packages/engine/ is
    # invisible to the CLI — the single most confusing failure mode this repo has.
    return _Row("typehaus", f"NOT the checkout — resolves to {src}", _WARN)


def _ui_row(root: Path | None) -> _Row:
    if root is None:
        return _Row("ui/dist", "no checkout", _INFO)
    index = root / "ui" / "dist" / "index.html"
    if not index.is_file():
        return _Row("ui/dist", "not built (cd ui && npm run build)", _WARN)
    built = datetime.fromtimestamp(index.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return _Row("ui/dist", f"built {built}", _OK)


def _serve_row(port: int) -> _Row:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        listening = sock.connect_ex(("127.0.0.1", port)) == 0
    if listening:
        return _Row("serve", f"something is listening on {port}", _INFO)
    return _Row("serve", f"nothing listening on {port}", _INFO)


def _gitignore_row(root: Path | None) -> tuple[_Row, list[str]]:
    """`git check-ignore` over the source trees; any hit is the bug, not a preference."""
    if root is None:
        return _Row("gitignore", "no checkout", _INFO), []
    present = [t for t in _SOURCE_TREES if (root / t).is_dir()]
    if not present:
        return _Row("gitignore", "no source trees found", _INFO), []
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-v", "--", *present],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return _Row("gitignore", "git unavailable", _INFO), []
    hits = [line for line in proc.stdout.splitlines()
            if line.strip() and not _is_negation(line)]
    if hits:
        return _Row("gitignore", f"{len(hits)} source tree(s) IGNORED", _WARN), hits
    return _Row("gitignore", f"0 of {len(present)} source trees ignored", _OK), []


def _is_negation(line: str) -> bool:
    """True when `git check-ignore -v` matched a `!` rule, i.e. the path is *not* ignored.

    ``check-ignore -v`` prints the matching rule and exits 0 for a negation exactly as it
    does for an exclusion — ``!packages/*/src/**`` and ``build/`` look identical unless you
    read the pattern. Without this, every source tree covered by one of .gitignore's
    protective negations would be reported as ignored, which is the opposite of the truth.
    """
    rule = line.split("\t", 1)[0]
    pattern = rule.split(":", 2)[2] if rule.count(":") >= 2 else rule
    return pattern.startswith("!")


@app.command()
def doctor(
    port: int = typer.Option(8765, help="Port `haus serve` would use."),
) -> None:
    """Report the environment facts a session would otherwise have to rediscover."""
    from typehaus._meta import engine_version

    root = _repo_root()
    gitignore, hits = _gitignore_row(root)
    rows = [
        _python_row(),
        _install_row(root),
        _Row("engine", f"version {engine_version()}", _OK),
        _ui_row(root),
        _serve_row(port),
        gitignore,
    ]
    colors = {_OK: "green", _WARN: "yellow", _INFO: "dim"}
    for row in rows:
        color = colors[row.status]
        console.print(f"{row.name:<11} {row.detail:<44} [{color}]{row.status}[/{color}]",
                      soft_wrap=True)
    for hit in hits:
        console.print(f"  [yellow]{hit}[/yellow]", soft_wrap=True)
    if root is not None and os.environ.get("PYTHONPATH"):
        # A leftover PYTHONPATH from the old README's alias can shadow the editable install
        # with a second copy of the source, so the two disagree about what is loaded.
        console.print(f"[dim]note: PYTHONPATH is set ({os.environ['PYTHONPATH']}) — it is "
                      f"not needed with an editable install.[/dim]", soft_wrap=True)
    raise typer.Exit(1 if any(r.status == _WARN for r in rows) else 0)
