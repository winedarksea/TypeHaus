"""Stored section/detail goldens — the harness the section migration is reviewed against.

Every other "snapshot" test in this suite compares a scene to *itself*
(``x.to_json() == x.to_json()``), which pins determinism and nothing else: a change to the
cut would sail through invisibly. These goldens are the missing half. For a fixed set of
cuts on both houses — the center section, every authored ``Slice``, every derived detail —
the scene IR is persisted under ``fixtures/section_goldens/`` and compared byte for byte.

Regenerate deliberately, never reflexively::

    .venv/bin/python -m pytest packages/engine/tests/test_section_goldens.py --bless

and read the diff. A blessed diff is a decision; an unblessed one is a regression.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _helpers import CATLIN, STARTER

GOLDENS = Path(__file__).parent / "fixtures" / "section_goldens"

# Keep the file names short and stable: a derived detail's key is long and carries
# assembly tags with characters no filesystem should have to think about.
_SAFE = str.maketrans({"|": "-", ":": "-", "/": "-", " ": "_"})


def _slug(name: str) -> str:
    return name.translate(_SAFE)


def _house_scenes(house: Path) -> dict[str, str]:
    """Every golden-tracked scene for one house, keyed by its golden file stem."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices
    from typehaus.emit.draw.section import build_center_section, build_section
    from typehaus.model.enums import SliceKind
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]

    out: dict[str, str] = {"center_section": build_center_section(model).to_json()}
    for view in model.plan.elements_of_kind("Slice"):
        if view.kind not in (SliceKind.SECTION, SliceKind.DETAIL):
            continue
        out[f"slice_{_slug(view.tag)}"] = build_section(model, view).to_json()
    for derived in derive_detail_slices(model):
        scene, _ = build_detail(model, derived)
        out[f"detail_{_slug(derived.key)}"] = scene.to_json()
    return out


@pytest.fixture(scope="module")
def catlin_goldens() -> dict[str, str]:
    return _house_scenes(CATLIN)


@pytest.fixture(scope="module")
def starter_goldens() -> dict[str, str]:
    return _house_scenes(STARTER)


def _compare(house: str, scenes: dict[str, str], bless: bool) -> None:
    root = GOLDENS / house
    if bless:
        root.mkdir(parents=True, exist_ok=True)
        for stale in root.glob("*.json"):
            if stale.stem not in scenes:
                stale.unlink()
        for stem, payload in scenes.items():
            (root / f"{stem}.json").write_text(payload + "\n")
        pytest.skip(f"blessed {len(scenes)} {house} goldens")

    assert root.is_dir(), f"no goldens for {house}; run with --bless"
    stored = {p.stem for p in root.glob("*.json")}
    assert stored == set(scenes), (
        f"{house} golden set drifted: "
        f"missing {sorted(set(scenes) - stored)}, stale {sorted(stored - set(scenes))}"
    )
    mismatched = [
        stem for stem, payload in sorted(scenes.items())
        if (root / f"{stem}.json").read_text() != payload + "\n"
    ]
    assert not mismatched, f"{house} scenes changed: {mismatched}"


def test_catlin_section_goldens(catlin_goldens, request):
    _compare("catlin", catlin_goldens, request.config.getoption("--bless"))


def test_starter_section_goldens(starter_goldens, request):
    _compare("starter", starter_goldens, request.config.getoption("--bless"))
