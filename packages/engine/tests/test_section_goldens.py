"""Stored section/detail goldens — the harness the section migration is reviewed against.

Every other "snapshot" test in this suite compares a scene to *itself*
(``x.to_json() == x.to_json()``), which pins determinism and nothing else: a change to the
cut would sail through invisibly. These goldens are the missing half. For a fixed set of
cuts on both houses — the center section, every authored ``Slice``, every derived detail —
the scene IR is persisted under ``fixtures/section_goldens/`` and compared field by field.

Not byte for byte, and not because that would be stricter — because it would be a statement
about the runner's CPU. ``Scene.to_json`` is ``model_dump_json`` with no rounding, and 31,464
of the numbers in these files carry thirteen or more decimals (``-13.437499999999998``,
``6.000000000000001``). IEEE-754 arithmetic agrees exactly across platforms but libm's
transcendentals do not, so a coordinate that went through a sine or an ``atan2`` can differ in
its last bits between this machine and CI's. See ``COORD_TOLERANCE_IN`` below for what
replaces equality, and what it costs.

Regenerate deliberately, never reflexively::

    .venv/bin/python -m pytest packages/engine/tests/test_section_goldens.py --bless

and read the diff. A blessed diff is a decision; an unblessed one is a regression.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _helpers import CATLIN, STARTER

GOLDENS = Path(__file__).parent / "fixtures" / "section_goldens"

# Keep the file names short and stable: a derived detail's key is long and carries
# assembly tags with characters no filesystem should have to think about.
_SAFE = str.maketrans({"|": "-", ":": "-", "/": "-", " ": "_"})


def _slug(name: str) -> str:
    return name.translate(_SAFE)


#: Model-space coordinates are inches (``scene.py``: "Coordinates are model-space **inches**"),
#: so this is one eighth of an inch in the goldens' own units — the finest tolerance anyone
#: builds to, and twelve orders of magnitude above the cross-platform float noise this
#: replaces.
#:
#: What it costs, stated plainly: a change that moves drawn geometry by less than 1/8" is now
#: invisible to these goldens, including a systematic shift of everything by a sixteenth. That
#: is the deliberate trade — a tolerance keyed to what a builder can hold, not to what a CPU
#: can reproduce. Tighten this one constant if a future regression proves it too generous.
COORD_TOLERANCE_IN = 0.125

#: Everything numeric that is *not* a building dimension. A blanket coordinate tolerance here
#: would be a bug, not a loosening: ``scale`` is 0.25 for 1/4" = 1'-0" and 0.375 for 3/8", so
#: 1/8" of slack would make two different drawing scales compare equal. ``lineweight`` is
#: 0.25 **mm**, smaller than the tolerance itself. Rotations are degrees. These keep a
#: tolerance that only absorbs float noise.
PARAM_TOLERANCE = 1e-9

#: JSON keys holding model-space geometry — the "where the building is" fields of the drawing
#: IR (``scene.py``). Everything numeric outside this set is graded at ``PARAM_TOLERANCE``.
#: Named rather than inferred, so a new coordinate field on a node is graded strictly until
#: someone adds it here on purpose.
COORD_KEYS = frozenset({
    "xy", "points", "boundary", "anchor", "at", "to", "insert", "window", "offset",
})


def _diff_scene(got: object, want: object, where: str, key: str | None,
                out: list[str]) -> None:
    """Collect every field-level difference between two parsed scenes.

    Structure — node kinds, layers, text strings, list lengths, key sets — is compared
    exactly. Only numbers get a tolerance, and which tolerance depends on whether the number
    is a building dimension or a drawing parameter.
    """
    if isinstance(want, dict):
        if not isinstance(got, dict) or got.keys() != want.keys():
            out.append(f"{where}: keys differ")
            return
        for name in want:
            _diff_scene(got[name], want[name], f"{where}.{name}", name, out)
    elif isinstance(want, list):
        if not isinstance(got, list) or len(got) != len(want):
            n = len(got) if isinstance(got, list) else got
            out.append(f"{where}: length {n} != {len(want)}")
            return
        for index, item in enumerate(want):
            # A coordinate key names a point or a list of points; the key does not repeat on
            # the way down, so carry it through the nesting.
            _diff_scene(got[index], item, f"{where}[{index}]", key, out)
    elif isinstance(want, (int, float)) and not isinstance(want, bool):
        if not isinstance(got, (int, float)) or isinstance(got, bool):
            out.append(f"{where}: {got!r} is not a number")
            return
        tolerance = COORD_TOLERANCE_IN if key in COORD_KEYS else PARAM_TOLERANCE
        delta = abs(got - want)
        if delta > tolerance:
            out.append(f"{where}: {got!r} != {want!r} (delta {delta:.4g} > {tolerance:g})")
    elif got != want:
        out.append(f"{where}: {got!r} != {want!r}")


def _scene_differences(got_json: str, want_json: str, stem: str) -> list[str]:
    out: list[str] = []
    _diff_scene(json.loads(got_json), json.loads(want_json), stem, None, out)
    return out


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
    differences: list[str] = []
    for stem, payload in sorted(scenes.items()):
        stored_text = (root / f"{stem}.json").read_text()
        if stored_text == payload + "\n":
            continue  # the common case: byte-identical, nothing to parse
        differences.extend(_scene_differences(payload, stored_text, stem))
    assert not differences, (
        f"{house} scenes changed ({len(differences)} field(s)); bless deliberately:\n  "
        + "\n  ".join(differences[:40])
        + (f"\n  ... and {len(differences) - 40} more" if len(differences) > 40 else ""))


def test_catlin_section_goldens(catlin_goldens, request):
    _compare("catlin", catlin_goldens, request.config.getoption("--bless"))


def test_starter_section_goldens(starter_goldens, request):
    _compare("starter", starter_goldens, request.config.getoption("--bless"))


# --- the comparator itself ---------------------------------------------------------------
#
# A tolerance nobody tests is a tolerance that quietly becomes "always passes". These pin
# both halves: what it must absorb, and what it must still catch.

def _a_stored_golden() -> tuple[str, dict]:
    stem = "center_section"
    for house in ("catlin", "starter"):
        path = GOLDENS / house / f"{stem}.json"
        if path.is_file():
            return path.read_text(), json.loads(path.read_text())
    raise AssertionError("no center_section golden to exercise the comparator against")


def _nudged(payload: dict, key: str, delta: float) -> dict:
    """Return a copy with the first number found under ``key`` moved by ``delta``."""
    moved = json.loads(json.dumps(payload))

    def walk(node: object, parent: str | None) -> bool:
        if isinstance(node, dict):
            return any(walk(v, k) for k, v in node.items())
        if isinstance(node, list):
            for index, item in enumerate(node):
                if isinstance(item, (int, float)) and not isinstance(item, bool) \
                        and parent == key:
                    node[index] = item + delta
                    return True
                if walk(item, parent):
                    return True
        return False

    def walk_scalars(node: object) -> bool:
        if isinstance(node, dict):
            for name, value in node.items():
                if name == key and isinstance(value, (int, float)) \
                        and not isinstance(value, bool):
                    node[name] = value + delta
                    return True
                if walk_scalars(value):
                    return True
        elif isinstance(node, list):
            return any(walk_scalars(item) for item in node)
        return False

    assert walk(moved, None) or walk_scalars(moved), f"no {key!r} number in this golden"
    return moved


def test_a_coordinate_moves_freely_below_an_eighth_of_an_inch() -> None:
    """The point of the tolerance: platform float noise, and anything under a builder's 1/8"."""
    text, payload = _a_stored_golden()
    for delta in (1e-12, 1e-6, 0.0625, 0.124):
        assert not _scene_differences(json.dumps(_nudged(payload, "points", delta)), text,
                                      "center_section"), f"{delta} should be absorbed"


def test_a_coordinate_past_an_eighth_of_an_inch_is_caught() -> None:
    text, payload = _a_stored_golden()
    for delta in (0.2, 1.0, 12.0):
        diffs = _scene_differences(json.dumps(_nudged(payload, "points", delta)), text,
                                   "center_section")
        assert diffs, f"a {delta}in move must not pass"


def test_scale_is_not_graded_at_the_coordinate_tolerance() -> None:
    """0.25 is 1/4" = 1'-0" and 0.375 is 3/8". A coordinate tolerance would equate them."""
    text, payload = _a_stored_golden()
    diffs = _scene_differences(json.dumps(_nudged(payload, "scale", 0.125)), text,
                               "center_section")
    assert diffs, "a drawing scale change must never be absorbed as a building tolerance"


def test_structure_is_still_compared_exactly() -> None:
    """Node kinds, layers and text are not numbers and get no tolerance."""
    text, payload = _a_stored_golden()

    dropped = json.loads(json.dumps(payload))
    dropped["nodes"] = dropped["nodes"][:-1]
    assert any("length" in d for d in
               _scene_differences(json.dumps(dropped), text, "center_section"))

    relayered = json.loads(json.dumps(payload))
    relayered["nodes"][0]["layer"] = "A-NOT-A-REAL-LAYER"
    assert _scene_differences(json.dumps(relayered), text, "center_section")
