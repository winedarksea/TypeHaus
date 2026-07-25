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

from shapely.geometry import Polygon

# The sauna's hot-side liner package (houses/catlin/plan/assemblies.py _SAUNA_LINER). Every
# one of these must land inside the sauna; the studs and the cold-side gwb must not.
_LINER_LAYERS = {"tg-liner", "liner-furring", "foil-polyiso"}
_SAUNA_WALLS = {"W-B-SA-W", "W-B-SA-N", "W-B-CS"}


def _sauna(catlin_model) -> Polygon:
    room = next(r for r in catlin_model.rooms if r.tag == "RM-B-SAUNA")
    return Polygon(room.clear_face)


def test_sauna_liner_lands_inside_the_sauna(catlin_model) -> None:
    """Every liner layer of the three sauna-facing walls lies inside RM-B-SAUNA.

    Before ``interior_room``, all of them landed on the far side: ``W-B-SA-W``'s ``tg-liner``
    west of its studs, ``W-B-SA-N``'s north of them, and ``W-B-CS``'s east of the concrete,
    in the gym.
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

    Its ``face("concrete-ext", offset=-6")`` alignment centres the concrete on the axis, so
    the concrete band is invariant under the sign — assert it against the two plain concrete
    segments that continue the same grid line.
    """
    def concrete_bounds(tag: str) -> tuple[float, ...]:
        wall = next(w for w in catlin_model.walls if w.tag == tag)
        layer = next(ly for ly in wall.layers if ly.name == "concrete")
        minx, _miny, maxx, _maxy = Polygon(layer.polygon).bounds
        return (round(minx, 6), round(maxx, 6))

    assert concrete_bounds("W-B-CS") == concrete_bounds("W-B-CS2")
