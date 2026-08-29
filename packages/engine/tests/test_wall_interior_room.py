"""``Wall.interior_room`` — which side an asymmetric interior partition faces.

``storey_outward_sign`` recovers the outdoor direction by tracing the storey's outer wall
loop. That answer is right for an exterior wall and *meaningless* for an interior partition:
both sides are indoors, so there is no geometry to recover it from. Handing the one storey
constant to every wall put the sauna's hot-side liner (T&G over furring over foil-faced
polyiso) on the outside of the sauna — in the gym, the hall, and the corridor.

``Wall.interior_room`` names the room layer 0 looks at, and ``wall_outward_sign`` turns that
into the per-wall sign. A room reference rather than a bare ``flip``: swapping
``start_node``/``end_node`` would silently invert a flip, and leaves this alone.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.quantities import inch

# The sauna's hot-side liner package (houses/catlin/plan/assemblies.py _SAUNA_LINER). Every
# one of these must land inside the sauna; the studs and the cold-side gwb must not.
_LINER_LAYERS = {"shiplap-liner", "liner-furring", "foil-polyiso"}
# Five since 2026-08-28: the south face is a framed wall (W-B-S2-FR) on a 7 1/4" curb
# (W-B-S2), and both carry the liner so the hot side's vapour control reaches the slab.
_SAUNA_WALLS = {"W-B-SA-W", "W-B-SA-N", "W-B-CS", "W-B-S2", "W-B-S2-FR"}


def _sauna(catlin_model) -> Polygon:
    room = next(r for r in catlin_model.rooms if r.tag == "RM-B-SAUNA")
    return Polygon(room.clear_face)


def test_sauna_liner_lands_inside_the_sauna(catlin_model) -> None:
    """Every liner layer of the four sauna-facing walls lies inside RM-B-SAUNA.

    Before ``interior_room``, all of them landed on the far side: ``W-B-SA-W``'s ``shiplap-liner``
    west of its studs, ``W-B-SA-N``'s north of them, and ``W-B-CS``'s east of the concrete,
    in the gym. ``W-B-S2``, the south face, joined them on 2026-08-18 — the same question
    asked of a foundation wall whose finish layers all sit outboard of the pour.
    """
    sauna = _sauna(catlin_model).buffer(1e-6)  # absorb the shared-edge tolerance
    checked = 0
    for wall in catlin_model.walls:
        if wall.tag not in _SAUNA_WALLS:
            continue
        for layer in wall.layers:
            if layer.name not in _LINER_LAYERS:
                continue
            poly = Polygon(layer.polygon)
            covered = poly.intersection(sauna).area / poly.area
            assert covered > 0.99, f"{wall.tag}/{layer.name} is {covered:.2f} inside the sauna"
            checked += 1
    assert checked == len(_SAUNA_WALLS) * len(_LINER_LAYERS), checked


def test_sauna_cold_side_stays_outside_the_sauna(catlin_model) -> None:
    """The framed partitions' cold-side gypsum faces away — the liner is not merely
    mirrored onto both sides."""
    sauna = _sauna(catlin_model)
    checked = 0
    for wall in catlin_model.walls:
        if wall.tag not in ("W-B-SA-W", "W-B-SA-N"):
            continue
        for layer in wall.layers:
            if layer.name != "gwb-cold":
                continue
            poly = Polygon(layer.polygon)
            assert poly.intersection(sauna).area / poly.area < 0.01, wall.tag
            checked += 1
    assert checked == 2, checked


def test_center_wall_concrete_stays_on_the_bearing_grid(catlin_model) -> None:
    """Flipping ``W-B-CS`` must move only the liner, not the 18' bearing line.

    Its alignment offset is a hand-written HALF of its structure thickness, so the bearing
    band is invariant under the sign — assert it against the plain concrete segment that
    continues the same grid line. **The band is 5 1/2" of stud since 2026-08-28**, where it
    was 12" of concrete under ``face("concrete-ext", offset=-6")``; it is centred on the
    same x=18' axis by ``face("stud-ext", offset=-2.75")``, which is what this asserts —
    the two bands share a centreline, not a width.
    """
    def band_center(tag: str, layer_name: str) -> float:
        wall = next(w for w in catlin_model.walls if w.tag == tag)
        layer = next(ly for ly in wall.layers if ly.name == layer_name)
        minx, _miny, maxx, _maxy = Polygon(layer.polygon).bounds
        return round((minx + maxx) / 2.0, 6)

    assert band_center("W-B-CS", "stud") == band_center("W-B-CS2", "concrete")


def test_south_wall_concrete_stays_on_the_garden_wall_line(catlin_model) -> None:
    """The twin invariant for ``W-B-S2``, and the one thing the 2026-08-18 liner must not
    break: the south face is aligned on ``face("concrete-ext")`` with *no* offset, because
    on that wall the concrete's outboard face is the datum. So the pour stays exactly where
    W-B-S1 and W-B-S3 leave it and only the liner grows inward, into the sauna.
    """
    def concrete_bounds(tag: str) -> tuple[float, ...]:
        wall = next(w for w in catlin_model.walls if w.tag == tag)
        layer = next(ly for ly in wall.layers if ly.name == "concrete")
        _minx, miny, _maxx, maxy = Polygon(layer.polygon).bounds
        return (round(miny, 6), round(maxy, 6))

    # W-B-S2 is the sauna's 7 1/4" curb since 2026-08-28 and its pour is 6", not 8" — 6" is
    # exactly stud-plus-sheathing, so the curb's faces land where the framed wall's do and
    # there is no shelf inside the room. What must not move is the OUTBOARD face, which is
    # the datum W-B-S1 sets and W-B-BRICK's 4.55" stand-off is measured from: the pour still
    # starts at y=0 and only its inboard face is 2" nearer.
    assert concrete_bounds("W-B-S2")[0] == concrete_bounds("W-B-S1")[0]
    assert concrete_bounds("W-B-S2")[1] == pytest.approx(inch(6).meters, abs=1e-9)
    assert concrete_bounds("W-B-S2") == concrete_bounds("W-B-S3")
