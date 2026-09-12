"""Pure helpers behind the two deliverable folders — ``haus calcs`` and ``haus handoff``.

Both write a *regenerated* tree, not a maintained one, so both need the same two things: a
manifest a reviewer can check a file against, and a prune that makes the folder say what
the model says. A sheet for an item that no longer exists is worse than a missing one — it
reads as a calculation somebody did.

No I/O policy lives here beyond writing the files the caller names: the CLI owns the paths.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path

#: The manifest's own name, so callers do not spell it three times.
MANIFEST = "MANIFEST.json"

#: Every file a deterministic zip claims to have been written at. A real mtime would make
#: two identical bundles differ, which is the one thing the manifest exists to rule out.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path, files: Iterable[str], *, prune: bool = True) -> dict[str, str]:
    """Write ``root/MANIFEST.json`` (sorted relative path -> sha256) and prune orphans.

    ``files`` is what this run produced, relative to ``root``. Anything the *previous*
    manifest listed and this run did not produce is deleted: that is the whole point, and
    it is why the manifest is written even when nothing else changed.

    ``prune=False`` is for a partial run (``haus calcs --item``), where "absent now" means
    "not asked for", not "no longer exists".
    """
    produced = sorted(set(files))
    manifest_path = root / MANIFEST
    if prune:
        _prune(root, manifest_path, produced)
    digests = {name: sha256_file(root / name) for name in produced
               if (root / name).is_file()}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"files": digests}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="")
    return digests


def _prune(root: Path, manifest_path: Path, produced: list[str]) -> None:
    previous: list[str] = []
    if manifest_path.is_file():
        try:
            previous = sorted(json.loads(manifest_path.read_text(encoding="utf-8"))["files"])
        except (ValueError, KeyError, TypeError):
            previous = []
    for name in previous:
        if name in produced:
            continue
        stale = root / name
        if stale.is_file():
            stale.unlink()
        _prune_empty(root, stale.parent)


def _prune_empty(root: Path, folder: Path) -> None:
    while folder != root and folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def prune_unlisted(root: Path, produced: Iterable[str], *, subdir: str) -> list[str]:
    """The first-run prune, for a tree written before manifests existed.

    Without a previous manifest there is nothing to diff against, so the sweep is narrowed
    to one subdirectory whose contents this run fully determines.
    """
    keep = {name for name in produced}
    removed: list[str] = []
    folder = root / subdir
    if not folder.is_dir():
        return removed
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if name not in keep:
            path.unlink()
            removed.append(name)
    _prune_empty(root, folder)
    return removed


def write_deterministic_zip(archive: Path, root: Path, files: Iterable[str]) -> Path:
    """Zip ``files`` (relative to ``root``) so two runs produce identical bytes."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in sorted(set(files)):
            info = zipfile.ZipInfo(filename=name, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, (root / name).read_bytes())
    return archive


def cited_notes(records: Iterable[object]) -> list[str]:
    """The note filenames the records' oracles name, deduplicated and sorted.

    A handoff copies these and no others: the bundle is what verifies *these* calcs, and a
    notes folder holding the whole house's design log buries that.
    """
    names: set[str] = set()
    for record in records:
        for oracle in getattr(record, "oracle", ()) or ():
            note = getattr(oracle, "note", None)
            if note:
                names.add(note)
    return sorted(names)


def manifest_table(digests: Mapping[str, str]) -> str:
    """The manifest as a Markdown table, for the README a reviewer actually opens."""
    lines = ["| File | sha256 |", "|---|---|"]
    lines += [f"| `{name}` | `{digest}` |" for name, digest in sorted(digests.items())]
    return "\n".join(lines)
