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
from collections.abc import Iterable, Mapping, Sequence
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


def pe_readme(*, house: str, generated: str, engine_version: str, content_hash: str,
              records, notes: Sequence[str], checklist, has_pdf: bool) -> str:
    """The page a reviewing engineer opens first — five minutes, in order.

    Written as a route through the bundle rather than a description of it. A PE handed forty
    calculation sheets and three models needs to know where to start, what a stamp would and
    would not cover, and how to hand the work back; everything else in the folder answers a
    question they have not asked yet.
    """
    from typehaus.engineering.item import Status

    ok = [r for r in records if r.status is Status.OK]
    incomplete = [r for r in records if r.status is Status.INCOMPLETE]
    over = [r for r in records if r.status is Status.OVER]
    deferred = [r for r in records if r.status is Status.NO_CALC]

    out = [
        f"# {house} — engineering handoff",
        "",
        "**NOT FOR CONSTRUCTION.** Nothing in this bundle is sealed. It is one house's",
        "engineered requirements, the calculations behind them, and the hand-worked notes",
        "each calculation is checked against, assembled so that a licensed professional can",
        "confirm them and stamp what they agree with.",
        "",
        "| | |",
        "|---|---|",
        f"| Generated | {generated} |",
        f"| Engine | {engine_version} |",
        f"| Model content hash | `{content_hash}` |",
        f"| Items | {len(records)} |",
        "",
        "## Five minutes, in order",
        "",
        "1. **`calcs/00-cover.md`** — the building, the code edition, and the design",
        "   criteria every calculation shares. If a criterion is wrong, stop here.",
        "2. **`calcs/02-item-register.md`** — every item, its governing limit state and its",
        "   demand/capacity ratio, on one page.",
        "3. **`calcs/03-open-items.md`** — what is *not* finished, and who owns each one.",
        "4. **`calcs/<kind>__<tag>.md`** — one nine-section sheet per item: scope,",
        "   references, given, analysis, result, assumptions, open inputs, independent",
        "   check, and what the sheet does not cover.",
        f"5. **`notes/`** — {len(notes)} hand-worked note(s). Each calculation in this engine",
        "   is checked against an independent hand pass, and section 8 of every sheet names",
        "   the note that checks it. A calculation that only agrees with itself is not",
        "   verified, and these are how that rule is kept.",
        "",
    ]
    if has_pdf:
        out += ["`calcs.pdf` is the same content flattened and page-anchored — the file to",
                "mark up and stamp, because no jurisdiction accepts Markdown.", ""]

    out += [
        "## What a stamp here covers",
        "",
        f"- **{len(ok)} item(s) are computed and check out.** Every limit state is graded",
        "  and under 1, with nothing missing. These are what a seal can cover today.",
    ]
    if incomplete:
        out.append(f"- **{len(incomplete)} item(s) are INCOMPLETE** — computed, but an input")
        out.append("  is missing. `03-open-items.md` names each one. You may well be the")
        out.append("  person who supplies it.")
    if over:
        out.append(f"- **{len(over)} item(s) are OVER capacity.** These are not review")
        out.append("  items, they are design changes.")
    if deferred:
        out.append(f"- **{len(deferred)} item(s) are DEFERRED and are not yours** — a truss")
        out.append("  fabricator's or a supplier's sealed design governs them, and this")
        out.append("  engine computes nothing for them. They carry no fingerprint and a")
        out.append("  stamp over them could not be pinned.")
    out += [
        "",
        "**Not in this bundle, and not covered by any stamp on it:** anything answered by a",
        "prescriptive table (the IRC's, or a manufacturer's published span table read on the",
        "element) and anything the sheets' section 9 lists as out of scope.",
        "",
        "## Pinning, and why the fingerprints matter",
        "",
        "Each item carries a **fingerprint** — a hash of the inputs its calculation actually",
        "consumed, each rounded to its own declared tolerance, plus the calculation's basis",
        "version. It is not a hash of the model: a doorknob moving must not stale a footing",
        "seal. When the model changes in a way that changes an input, the fingerprint stops",
        "matching and the item reads STALE rather than sealed. That is the mechanism that",
        "keeps a stamp meaning something six months later.",
        "",
        "## How to hand the work back",
        "",
        "1. Stamp `calcs.pdf` (or the sheets you reviewed).",
        "2. Fill in `engineering.toml.draft` — it is a form, with every blank marked",
        "   `<<LIKE THIS>>`, and the fingerprints already filled in. Do not edit those.",
        "3. Return both. The owner copies the draft to `houses/<name>/engineering.toml` and",
        "   runs `haus engineering --require-seal` and `haus print --sealed`.",
        "",
        "The engine refuses to load that file while any `<<placeholder>>` remains, so an",
        "unedited form cannot become a seal by being copied.",
        "",
        "## The models",
        "",
        "`model.ifc` is IFC4, framing level of detail. It opens in Bonsai (the Blender IFC",
        "add-on) and in any IFC4 viewer. Structural members carry their section profiles and",
        "material grades, and every engineered item's record rides on its elements as a",
        "`Pset_TH_Engineering_<kind>` property set: item id, status, governing limit state,",
        "demand, capacity, ratio, citation and fingerprint. `model.glb` is the same building",
        "for a viewer that does not read IFC.",
        "",
        "## Integrity",
        "",
        "`MANIFEST.json` lists every file in this bundle with its sha256. The bundle is",
        "byte-deterministic: regenerating it from an unchanged model reproduces every hash,",
        "so a changed hash is a changed model and not a re-run.",
        "",
    ]
    return "\n".join(out) + "\n"
