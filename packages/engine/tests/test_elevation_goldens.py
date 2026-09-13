"""Every resolved elevation in the reference house, pinned — the zero-delta gate.

Why this exists
---------------
Giving storeys a ``building`` means re-filing elements onto newly minted storeys. The rule
that makes that safe is *zero delta by construction*: a new storey takes its ``elevation``
from the same constant object the old one read, so nothing moves. This harness is the
mechanical proof of that rule, and it has to be mechanical, because the failure mode is
silent.

A ``PipeRun``'s inverts are **storey-relative** (``resolve/mep.py``) while a ``ConduitRun``'s
are **absolute**. Re-filing a sleeve from a storey at ``0'-0"`` onto one at ``-1'-0"`` shifts
it a foot, emits clean geometry, and reports **0 FAIL** — no check in the repo grades a
sleeve's absolute invert against anything. A per-element audit of ~9,000 elements is not a
gate; this is.

What it pins
------------
Three layers, because a shift can hide in any one of them:

1. **Storey and building identity** — every ``(building, storey)`` cell and its elevation.
   The headline: if a storey's datum moved, everything below is a consequence, not a cause.
2. **Every elevation-bearing field on every resolved element**, found by name rather than by
   a hand-kept list (see ``_is_elevation_field``) — so a field added to a ``Resolved*`` class
   after this file was written is covered without anyone remembering to add it.
3. **The geometry IR's z extent per part** — the last word on where a solid actually is,
   after layer setbacks, platform growth and rake. A resolved field can stay put while the
   solid it feeds moves.

Rounded, not byte-exact: ``_PLACES`` is 1e-7 m, which is 4e-6 inch — twelve orders of
magnitude tighter than anything this is meant to catch, and loose enough to survive the
libm difference between CI's linux and a local arm64 (the same reasoning
``test_section_goldens.py`` writes out at length).

Regenerate deliberately, never reflexively::

    .venv/bin/python -m pytest packages/engine/tests/test_elevation_goldens.py --bless

A blessed diff is a decision. During the building refactor the correct diff is **empty**.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "fixtures" / "catlin_elevations.json"

#: Decimal places kept, in metres. 1e-7 m == 4e-6 inch.
_PLACES = 7

#: ``ResolvedModel`` fields that are not collections of resolved elements.
_NOT_A_COLLECTION = frozenset({"plan", "geometry", "timings", "_tag_index"})


def _is_elevation_field(name: str) -> bool:
    """Does this field name carry an elevation?

    Name-based on purpose. The alternative is a hand-kept list of ~26 field names across 30
    dataclasses, which goes stale the first time someone adds a field — and going stale is
    indistinguishable from passing.

    A ``z`` path segment (``z_m``, ``z0_m``, ``top_z1_m``, ``bearing_z_m``, ``z_start_m``),
    or the words ``elevation``/``invert`` anywhere. Heights are deliberately **out**: a
    ``height_m`` is a dimension, not a position, and a re-filing cannot move one.
    """
    if "elevation" in name or "invert" in name:
        return True
    return any(part.rstrip("0123456789") == "z" for part in name.split("_"))


def _numbers(value: object) -> list[float]:
    """Flatten a field value to the floats in it, or ``[]`` if it holds none."""
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (tuple, list)):
        out: list[float] = []
        for item in value:
            out.extend(_numbers(item))
        return out
    return []


def _round(value: float) -> float:
    return round(value, _PLACES)


def _item_key(item: object, index: int) -> str:
    """A stable name for one resolved element.

    Tag first (the plan's own addressing scheme), then the junction's ``node_tag``, and only
    then the list index. An index-keyed entry is order-sensitive and therefore noisier than
    the rest — which is correct: a collection whose order moved is a real change.
    """
    for attr in ("tag", "node_tag", "uid"):
        name = getattr(item, attr, None)
        if isinstance(name, str) and name:
            return name
    return f"#{index}"


def _z_digest(values: list[float]) -> list[object]:
    """min, max, count and a hash — diff-legible at the top, complete at the end.

    min/max name the shift in metres the moment a reader opens the diff; the hash catches a
    reshaping that happens to preserve both (a part whose middle vertices moved).
    """
    rounded = [_round(v) for v in values]
    blob = ",".join(f"{v:.7f}" for v in rounded).encode()
    return [min(rounded), max(rounded), len(rounded),
            hashlib.sha256(blob).hexdigest()[:12]]


def _solid_z(solid: object) -> list[float]:
    """Every z in one geometry-IR solid, whichever of the four shapes it is."""
    out: list[float] = []
    for name in ("z0_m", "z1_m", "top"):
        out.extend(_numbers(getattr(solid, name, None)))
    for name in ("corners_bottom", "corners_top", "vertices"):
        ring = getattr(solid, name, None)
        if ring is None:
            continue
        for point in ring:
            if isinstance(point, (tuple, list)) and len(point) == 3:
                out.append(float(point[2]))
    # GSweep: a profile swept along ``extrude`` from ``origin``.
    for name in ("origin", "extrude"):
        vec = getattr(solid, name, None)
        if isinstance(vec, (tuple, list)) and len(vec) == 3:
            out.append(float(vec[2]))
    return out


def _collect(model: object) -> dict[str, object]:
    plan = model.plan  # type: ignore[attr-defined]
    out: dict[str, object] = {}

    # --- 1. cells: which building holds which datum -------------------------------------
    for building, storey in plan.cells():
        out[f"cell/{building.tag}/{storey.tag}"] = _round(storey.elevation.meters)
        out[f"cell/{building.tag}/{storey.tag}/ceiling"] = _round(
            storey.default_ceiling_height.meters)

    # --- 2. every elevation-bearing field on every resolved element ----------------------
    for field in dataclasses.fields(model):  # type: ignore[arg-type]
        if field.name in _NOT_A_COLLECTION:
            continue
        collection = getattr(model, field.name)
        if not isinstance(collection, list):
            continue
        for index, item in enumerate(collection):
            if not dataclasses.is_dataclass(item):
                continue
            name = _item_key(item, index)
            for sub in dataclasses.fields(item):
                if not _is_elevation_field(sub.name):
                    continue
                values = _numbers(getattr(item, sub.name))
                if not values:
                    continue
                key = f"{field.name}/{name}/{sub.name}"
                out[key] = _round(values[0]) if len(values) == 1 else _z_digest(values)

    # --- 3. framing members, which live inside their host rather than in a collection ----
    for member in model.all_members():  # type: ignore[attr-defined]
        key = f"member/{member.parent_uid}/{member.child_key}"
        values = [member.z0_m, member.z1_m]
        for end in (member.z0_end_m, member.z1_end_m):
            if end is not None:
                values.append(end)
        out[key] = _z_digest(values)

    # --- 4. the geometry IR: where the solid actually is --------------------------------
    geometry = model.geometry  # type: ignore[attr-defined]
    assert geometry is not None, "the golden needs the geometry stage; resolve(), not preview"
    for element in geometry.elements:
        for part in element.parts:
            values: list[float] = []
            for solid in part.solids:
                values.extend(_solid_z(solid))
            if values:
                out[f"geometry/{element.uid}/{part.key}"] = _z_digest(values)

    return out


def _differences(golden: dict[str, object], live: dict[str, object]) -> list[str]:
    """Key-set first, then values.

    The key set is checked in **both** directions on purpose. A golden compared only where
    the two agree passes while half the model has vanished from it — the stale-slice failure
    ``test_section_goldens`` learned the hard way.
    """
    out: list[str] = []
    gone = sorted(set(golden) - set(live))
    added = sorted(set(live) - set(golden))
    for key in gone[:20]:
        out.append(f"{key}: gone (was {golden[key]!r})")
    if len(gone) > 20:
        out.append(f"… and {len(gone) - 20} more gone")
    for key in added[:20]:
        out.append(f"{key}: new ({live[key]!r})")
    if len(added) > 20:
        out.append(f"… and {len(added) - 20} more new")
    moved = 0
    for key in sorted(set(golden) & set(live)):
        if golden[key] != live[key]:
            moved += 1
            if moved <= 30:
                out.append(f"{key}: {golden[key]!r} -> {live[key]!r}")
    if moved > 30:
        out.append(f"… and {moved - 30} more moved")
    return out


def test_no_resolved_elevation_moves(catlin_model_ro, request) -> None:
    live = _collect(catlin_model_ro)
    # A harness that silently collected nothing would pass forever. The reference house has
    # thousands of elevations; the floor only has to be far enough above zero to prove the
    # walk ran.
    assert len(live) > 5000, f"collected only {len(live)} elevations — the walk is broken"

    if request.config.getoption("--bless"):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(live, indent=0, sort_keys=True) + "\n")
        pytest.skip(f"blessed {len(live)} catlin elevations")

    assert GOLDEN.is_file(), f"no elevation golden; run with --bless ({GOLDEN})"
    golden = json.loads(GOLDEN.read_text())
    differences = _differences(golden, live)
    assert not differences, (
        f"{len(differences)} resolved elevation(s) changed. Under the zero-delta rule a "
        f"building re-filing moves NONE of these — a new storey takes its elevation from "
        f"the same constant object the old one read. Bless only a deliberate datum change:"
        f"\n  " + "\n  ".join(differences)
    )
