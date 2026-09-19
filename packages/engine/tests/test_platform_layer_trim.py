"""A lifted wall's finish stops at the top plate — house-wide, on the reference house.

``resolve/platform.py`` grows a stacked wall up to the platform above it (#43) and drops a
framed wall down over the basement rim, so the wall spans floor-to-floor the way Revit and
SketchUp expect. Its *framing* stays at the plates, and so does its *body*: everything
inboard of the studs, and a partition's whole body, is stopped at ``plate_top_z_m`` /
``plate_base_z_m`` by ``layer_bands.clamp_to_plates``.

Untrimmed, catlin ordered 1,198 sf of interior finish over the joist band and another 322 sf
below the rim. This module is the invariant, not the number: what may run through a band is
the weather side of an envelope wall, and nothing else.

Two halves, in this order: 179 real walls first, because the question is whether the rules
hold on a house nobody wrote for them; then the same rules on ``test_layer_extent``'s
synthetic two-storey fixture, where a stack can be made to say one thing at a time.
"""

from __future__ import annotations

from functools import cache

import pytest

from typehaus.quantities import inch
from typehaus.resolve.layer_bands import has_weather_skin, reband_for_platform

#: A liner band the AUTHOR wrote, and the plate above it — the whole story in two numbers.
#: ``W-B-CS`` is the sauna's north partition: its top plate is 13 7/16" below 0'-0", and the
#: sauna's own ceiling is a further 6" down at 7'-6" over the slab. The trim is a ``min``, so
#: the authored band wins on the liner and the plate governs the gypsum on the cold side.
_SAUNA_WALL = "W-B-CS"
_SAUNA_CEILING_IN = -19.4375
_SAUNA_PLATE_IN = -13.4375


def _lifted(model):
    return [w for w in model.walls if w.plate_top_z_m is not None]


def _dropped(model):
    return [w for w in model.walls if w.plate_base_z_m is not None]


def _trimmed_names(wall) -> set[str]:
    """The layers ``clamp_to_plates`` owes this wall — restated from the RULE, not the code.

    A partition's whole body; an envelope wall's layers inboard of its first STRUCTURE
    layer. Cavity fill follows its host rather than being trimmed on its own.
    """
    names = [ly.name for ly in wall.layers]
    first = next((i for i, ly in enumerate(wall.layers)
                  if ly.function == "structure"), None)
    if first is None:
        return set()
    if not has_weather_skin(wall.layers):
        return set(names)
    return set(names[:first])


def test_nothing_but_the_weather_side_reaches_above_a_lifted_walls_top_plate(
        catlin_model_ro):
    assert len(_lifted(catlin_model_ro)) > 50, "the lift stopped happening; nothing is pinned"
    over = []
    for wall in _lifted(catlin_model_ro):
        owed = _trimmed_names(wall)
        for layer in wall.layers:
            if layer.name in owed and layer.band(wall)[1] > wall.plate_top_z_m + 1e-9:
                over.append(f"{wall.tag}/{layer.name}")
    assert not over, over


def test_nothing_but_the_weather_side_reaches_below_a_dropped_walls_base_plate(
        catlin_model_ro):
    assert _dropped(catlin_model_ro), "the drop stopped happening; nothing is pinned"
    under = []
    for wall in _dropped(catlin_model_ro):
        owed = _trimmed_names(wall)
        for layer in wall.layers:
            if layer.name in owed and layer.band(wall)[0] < wall.plate_base_z_m - 1e-9:
                under.append(f"{wall.tag}/{layer.name}")
    assert not under, under


def test_a_weather_layer_still_laps_the_rim(catlin_model_ro):
    """The other half, and the one a wrong predicate breaks silently: closing the band is
    the REASON the lift exists, so a cladding, sheathing, membrane, drainage or vent gap
    outboard of the studs must still run the wall's own full height."""
    short = []
    for wall in _lifted(catlin_model_ro):
        if not has_weather_skin(wall.layers):
            continue
        for layer in wall.layers:
            if layer.function not in ("cladding", "sheathing", "airgap", "drainage"):
                continue
            if layer.band_spec is not None:  # an AUTHORED band is the author's business
                continue
            if layer.band(wall)[1] < wall.z1_m - 1e-9:
                short.append(f"{wall.tag}/{layer.name}")
    assert not short, short


def test_the_trim_is_a_min_so_an_authored_band_still_wins(catlin_model_ro):
    """``W-B-CS`` carries both answers at once. Its ``shiplap-liner`` is banded to the
    sauna's 7'-6" ceiling, 6" BELOW the plate, and stays there — removing it would buy
    basswood, strapping and foil-faced polyiso for that 6". Its cold-side ``gwb-b`` has no
    band of its own and is stopped at the plate.
    """
    wall = catlin_model_ro.wall(_SAUNA_WALL)
    assert wall.plate_top_z_m == pytest.approx(inch(_SAUNA_PLATE_IN).meters)
    for name in ("shiplap-liner", "liner-furring", "foil-polyiso"):
        layer = next(ly for ly in wall.layers if ly.name == name)
        assert layer.band(wall)[1] == pytest.approx(inch(_SAUNA_CEILING_IN).meters), name
    for name in ("gwb-b", "stud"):
        layer = next(ly for ly in wall.layers if ly.name == name)
        assert layer.band(wall)[1] == pytest.approx(inch(_SAUNA_PLATE_IN).meters), name


def test_every_cavity_layer_shares_its_hosts_band(catlin_model_ro):
    """Cavity fill bills as ``insulation (cavity)`` over its own band, so a cavity that did
    not follow its host would claim a joist depth more batt than the stud bay it fills."""
    wrong = []
    for wall in catlin_model_ro.walls:
        bands = {ly.name: ly.band(wall) for ly in wall.layers}
        for layer in wall.layers:
            if not layer.is_cavity or layer.cavity_host not in bands:
                continue
            if layer.band(wall) != bands[layer.cavity_host]:
                wrong.append(f"{wall.tag}/{layer.name}")
    assert not wrong, wrong


def test_applying_the_trim_a_second_time_changes_nothing(catlin_model_ro):
    """``_lift`` and ``_drop`` both fold through ``reband_for_platform``, and all 14 dropped
    walls are also lifted — so the second pass re-runs it over a wall the first already
    trimmed. A fixed point is what makes that safe."""
    from typehaus.resolve.layout_lines import lines_by_wall

    grade_m = catlin_model_ro.plan.project.site.grade.meters
    # The real layout line, because a LINE_BASE band (the sauna liner's) re-resolves off it
    # — handing ``None`` would re-datum the band and prove nothing about the clamp.
    lines = lines_by_wall(catlin_model_ro.layout_lines)
    for wall in _lifted(catlin_model_ro):
        again = reband_for_platform(
            wall, wall.z0_m, wall.z1_m, grade_m, lines.get(wall.tag),
            plate_top=wall.plate_top_z_m, plate_base=wall.plate_base_z_m)
        assert [(ly.name, ly.z0_m, ly.z1_m) for ly in again] == \
            [(ly.name, ly.z0_m, ly.z1_m) for ly in wall.layers], wall.tag


def test_the_takeoff_bills_no_finish_above_the_plate(catlin_model_ro):
    """The quantity the whole change is for, as a RELATION rather than a magic number: an
    interior finish may not bill more face than the plate-to-plate rectangle it covers."""
    from shapely.geometry import LineString

    from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2

    nets = wall_net_areas_m2(catlin_model_ro)
    over = []
    for wall in _lifted(catlin_model_ro):
        run = LineString(wall.axis).length
        base = wall.plate_base_z_m if wall.plate_base_z_m is not None else wall.z0_m
        ceiling = run * (wall.plate_top_z_m - base)
        owed = _trimmed_names(wall)
        for layer in wall.layers:
            if layer.function != "finish" or layer.name not in owed:
                continue
            billed = wall_layer_net_area_m2(catlin_model_ro, wall, layer, nets[wall.tag])
            if billed > ceiling + 1e-9:
                over.append(f"{wall.tag}/{layer.name}: {billed:.3f} > {ceiling:.3f}")
    assert not over, over


# --- the same rules on the synthetic two-storey fixture ----------------------------------
#
# ``test_layer_extent._lift_plan`` is where the stack can be made to say one thing at a
# time: an EXT wall with a finish inboard of the studs and a cladding outboard of them, and
# an INT partition with nothing weatherproof anywhere. Imported rather than rebuilt — it is
# one fixture, and a second copy of it would drift.


@cache
def _lift_model():
    from test_layer_extent import _lift_plan

    from typehaus.resolve import resolve

    model, _findings = resolve(_lift_plan())
    return model


def test_a_lifted_envelope_walls_finish_stops_at_the_plate_and_its_skin_does_not():
    model = _lift_model()
    wall = model.wall("W-M-1")
    assert wall.plate_top_z_m is not None, "fixture regression: W-M-1 was not lifted"

    def band(name):
        return next(ly for ly in wall.layers if ly.name == name).band(wall)

    assert band("drywall")[1] == pytest.approx(wall.plate_top_z_m)
    # Everything from the studs out closes the rim, which is the whole point of the lift.
    assert band("stud")[1] == pytest.approx(wall.z1_m)
    assert band("siding")[1] == pytest.approx(wall.z1_m)
    assert band("frieze")[1] == pytest.approx(wall.z1_m)


def test_a_lifted_partitions_whole_body_stops_at_the_plate():
    model = _lift_model()
    wall = model.wall("W-M-P")
    assert wall.plate_top_z_m is not None, "fixture regression: W-M-P was not lifted"
    for layer in wall.body_layers():
        assert layer.band(wall)[1] == pytest.approx(wall.plate_top_z_m), layer.name


def test_the_trim_invents_no_recipe():
    """``band_spec`` is the AUTHOR's ``Layer.extent``, and a platform trim is not one.

    It is an instance fact about one lifted wall, not a statement the ``Assembly`` made —
    which is what keeps every lifted ``EXT`` on one ``IfcWallType`` and what stops a later
    ``reband`` from re-widening the layer.
    """
    model = _lift_model()
    for tag in ("W-M-1", "W-M-P"):
        wall = model.wall(tag)
        for layer in wall.layers:
            authored = next(
                ly for ly in model.plan.library.resolve_assembly(wall.assembly).layers
                if ly.name == layer.name)
            assert (layer.band_spec is None) == (authored.extent is None), layer.name


def test_a_wall_with_no_structure_layer_is_left_alone():
    """Interior and exterior are not distinguishable without studs, and on a monolithic
    lifted wall the pour IS what closes the rim. An explicit refusal, not a heuristic."""
    from typehaus.resolve.layer_bands import clamp_to_plates
    from typehaus.resolve.model import ResolvedLayer

    layers = tuple(
        ResolvedLayer(name=name, material_ref="wood", function="finish",
                      thickness_m=0.1, polygon=())
        for name in ("a", "b"))
    assert clamp_to_plates(layers, wall_z0=0.0, wall_z1=3.0, plate_top=2.7,
                           plate_base=0.3, clad=False) == layers
