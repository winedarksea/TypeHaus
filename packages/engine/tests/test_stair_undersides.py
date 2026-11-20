"""Catlin's stair undersides: derived gypsum boards, drawn, exported, billed and overhead."""

import pytest

from typehaus.quantities import inch
from typehaus.resolve.geometry_build import build_geometry
from typehaus.resolve.overhead import OverheadIndex
from typehaus.resolve.stair_underside_boards import flights

_T = inch(5 / 8).meters


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


def _boards(stair):
    return {m.child_key: m for m in stair.members if m.category == "stair_soffit"}


def test_boards_sit_on_the_stringers_landings_and_steps(catlin_model_ro):
    m2s = _stair(catlin_model_ro, "ST-M2S")
    boards = _boards(m2s)
    assert {"soffit-lower", "soffit-upper", "soffit-landing-lower+upper"} <= set(boards)
    # The flight board's top edge is the stringers' rake, dying at the floor.
    rake = next(f for f in flights(m2s.members) if f.name == "lower").rake
    assert (boards["soffit-lower"].z0_m, boards["soffit-lower"].z1_m) == pytest.approx(
        (rake[0][1], rake[1][1]))
    landing_z = min(m.z0_m for m in m2s.members if m.child_key.startswith("landing-joist-"))
    assert boards["soffit-landing-lower+upper"].z1_m == pytest.approx(landing_z)

    b2m = _boards(_stair(catlin_model_ro, "ST-B2M"))
    lower, upper = b2m["soffit-landing-lower"], b2m["soffit-landing-upper"]
    riser = _stair(catlin_model_ro, "ST-B2M").riser_height_m
    assert upper.z1_m - lower.z1_m == pytest.approx(riser, abs=inch(0.25).meters)
    step = b2m["soffit-step-lower-upper"]
    assert (step.z0_m, step.z1_m) == pytest.approx((lower.z0_m, upper.z1_m))
    # They stop at W-B-WELL's faces and the posts and studs on the partition line (ST-M2S's
    # landing post too); the riser stands on the lower landing's partition rim, the upper
    # board stopped at it.
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint
    from typehaus.resolve.soffits import wall_footprint

    well = wall_footprint(catlin_model_ro.wall("W-B-WELL"))
    for tag, wall in (("ST-B2M", well), ("ST-M2S", None)):
        stair = _stair(catlin_model_ro, tag)
        frame = [(Polygon(member_footprint(m)[0]), m) for m in stair.members
                 if m.category == "landing_framing" or m.p0 == m.p1]
        for key, board in _boards(stair).items():
            if not key.startswith(("soffit-landing", "soffit-step")):
                continue
            plan = Polygon(member_footprint(board)[0])
            assert wall is None or plan.intersection(wall).area < 1e-6, key
            for footprint, m in frame:
                if m.z0_m < board.z1_m - 1e-6 and m.z1_m > board.z0_m + 1e-6:
                    assert plan.intersection(footprint).area < 1e-6, (key, m.child_key)

    s2a = _stair(catlin_model_ro, "ST-S2A")
    assert not any("winder" in key for key in _boards(s2a))
    ceiling = next(c.z0_m for c in catlin_model_ro.ceilings if c.tag == "CEIL-RM-S-STUDY2")
    faces = [m for key, m in _boards(s2a).items() if "-face-" in key]
    assert faces and max(m.z1_m for m in faces) <= ceiling + 1e-4
    # The head cut stands above the ceiling butting it: concealed, so no return.
    assert "soffit-flight-head" not in _boards(s2a)
    # The free (south) side's arris is beaded, short of RL-A-FLIGHT-SKIRT's panel.
    [flight] = [u for u in s2a.undersides if u.role == "flight"]
    assert len(flight.free_edges) == 2


def test_finish_per_stair(catlin_model_ro):
    b2m = _stair(catlin_model_ro, "ST-B2M").undersides
    assert b2m and all(u.material_ref == "gwb-x" and u.coating is None for u in b2m)
    m2s = _stair(catlin_model_ro, "ST-M2S").undersides
    coat = next(c for c in catlin_model_ro.ceilings if c.room_ref == "RM-M-LIVING").layers[0]
    assert all(u.material_ref == "gwb" and u.coating == coat.material_ref for u in m2s)
    assert all(u.thickness_m == pytest.approx(_T) for u in (*b2m, *m2s))


def test_boards_reach_geometry_and_ifc_ceiling_covering(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell

    stair = _stair(catlin_model_ro, "ST-B2M")
    geometry = build_geometry(catlin_model_ro)
    [element] = [e for e in geometry.elements if e.uid == f"{stair.uid}::framing"]
    drawn = [p for p in element.parts if p.catalog.role == "stair_soffit"]
    assert len(drawn) == len(_boards(stair)) == len(stair.undersides)
    assert all(p.catalog.material_ref == "gwb-x" for p in drawn)

    model = ifcopenshell.open(str(catlin_ifc_path))
    [ifc_stair] = [item for item in model.by_type("IfcStair") if item.Name == "ST-B2M"]
    children = [item for rel in ifc_stair.IsDecomposedBy for item in rel.RelatedObjects]
    ceilings = [item for item in children
                if item.is_a("IfcCovering") and item.PredefinedType == "CEILING"]
    assert len(ceilings) == len(stair.undersides)
    assert all(item.Representation is not None for item in ceilings)


def test_upper_stair_underside_is_overhead_of_the_lower_stair(catlin_model_ro):
    b2m = _stair(catlin_model_ro, "ST-B2M")
    tread = max((m for m in b2m.members if m.category == "tread"
                 and m.p0[0] > 4.3), key=lambda m: m.z1_m)  # the lower lane's top tread
    x, y = ((a + b) / 2.0 for a, b in zip(tread.p0, tread.p1, strict=True))
    over = OverheadIndex(catlin_model_ro).lowest_above(x, y, tread.z1_m)
    assert over is not None and over.tag == "ST-M2S"
