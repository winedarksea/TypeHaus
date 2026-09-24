"""No engine or UI source names a material tag that only a house defines (decision #57).

A house's material is its own business: the engine reads it through the resolved
``Material`` (``hatch``, ``color``, ``skin_family``, ``finish``), never by spelling its tag.
The set is built from source, not a load: every ``Material(tag=...)`` literal and every
``model_copy(update={"tag": ...})`` under ``houses/*/plan`` and ``houses/*/params``, less
the library's own tags. ``finish`` values are exempt: a finish is presentation vocabulary
shared by the renderers, even where a house happens to name a material after it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from typehaus.library import ALL_MATERIALS

REPO = Path(__file__).resolve().parents[3]
ENGINE = REPO / "packages" / "engine" / "src" / "typehaus"
UI = REPO / "ui" / "src"
_TS_STRING = re.compile(r"""(["'`])([a-z0-9][a-z0-9-]*)\1""")


def _house_sources() -> list[Path]:
    return [p for house in (REPO / "houses").iterdir() if house.is_dir()
            for sub in ("plan", "params") if (house / sub).is_dir()
            for p in (house / sub).rglob("*.py")]


def _literal(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _house_tags_and_finishes() -> tuple[set[str], set[str]]:
    tags: set[str] = set()
    finishes: set[str] = set()
    for path in _house_sources():
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                for kw in node.keywords:
                    value = _literal(kw.value)
                    if value and kw.arg == "tag" and name == "Material":
                        tags.add(value)
                    if value and kw.arg == "finish":
                        finishes.add(value)
                if name == "model_copy":
                    for kw in node.keywords:
                        if kw.arg == "update" and isinstance(kw.value, ast.Dict):
                            for k, v in zip(kw.value.keys, kw.value.values, strict=True):
                                if k is not None and _literal(k) == "tag" and _literal(v):
                                    tags.add(_literal(v))
    finishes |= {m.finish for m in ALL_MATERIALS if m.finish}
    return tags - {m.tag for m in ALL_MATERIALS}, finishes


def _python_strings(path: Path) -> set[str]:
    return {n.value for n in ast.walk(ast.parse(path.read_text()))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def _ts_strings(path: Path) -> set[str]:
    # Comments are prose, not lookups: strip them before collecting string tokens.
    text = re.sub(r"//[^\n]*|/\*.*?\*/", "", path.read_text(), flags=re.S)
    return {m.group(2) for m in _TS_STRING.finditer(text)}


def test_no_engine_or_ui_literal_names_a_house_only_material() -> None:
    house_tags, finishes = _house_tags_and_finishes()
    assert "brown-brick" in house_tags, "the house-tag scan found nothing it should"
    forbidden = house_tags - finishes
    hits: list[str] = []
    for path in sorted(ENGINE.rglob("*.py")):
        if "templates" in path.parts:
            continue  # a template IS a house
        hits += [f"{path.relative_to(REPO)}: {s}" for s in _python_strings(path) & forbidden]
    if UI.is_dir():
        for path in sorted([*UI.rglob("*.ts"), *UI.rglob("*.tsx")]):
            if "generated" in path.parts or ".test." in path.name:
                continue  # generated mirrors, and test fixtures that invent their own data
            hits += [f"{path.relative_to(REPO)}: {s}" for s in _ts_strings(path) & forbidden]
    assert not hits, ("engine/UI source names a house-only material tag; read the resolved "
                      "Material instead:\n  " + "\n  ".join(hits))
