"""What a hung end may hang ON: never a carrier it runs beside, and a deck joist only for a
stringer head."""

from __future__ import annotations

import math

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.joints.hung import hung_connections
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import (
    FramedMember,
    ResolvedFloor,
    ResolvedModel,
    ResolvedStair,
)
from typehaus.takeoff import hardware_takeoff


def _member(parent: str, key: str, category: str, p0, p1, z0: float, z1: float,
            **kwargs) -> FramedMember:
    return FramedMember(parent_uid=parent, child_key=key, category=category,
                        profile=kwargs.pop("profile", "2x8"), p0=p0, p1=p1, z0_m=z0,
                        z1_m=z1, length_m=1.0, **kwargs)


def _deck(*members) -> ResolvedFloor:
    return ResolvedFloor(uid="F", tag="FS-T", storey="main", direction="x",
                         members=tuple(members))


_BEAM = _member("B", "beam", "beam", (0.0, 0.0), (0.0, 4.0), 3.0, 3.2)


def test_a_joist_alongside_a_beam_does_not_hang_in_it() -> None:
    # 2" off the beam line, flush, both ends inside the gap tolerance: blocked, not hung.
    beside = _member("F", "j0", "joist", (2 * M_PER_IN, 0.0), (2 * M_PER_IN, 4.0), 3.0, 3.2)
    model = ResolvedModel(plan=None, floors=[_deck(_BEAM, beside)])
    assert hung_connections(model, CONFIG.hanger_detection) == []


def test_a_joist_just_inside_the_parallel_limit_still_hangs() -> None:
    # 25 degrees off the beam: framing into it, if askew.
    angle = math.radians(25.0)
    end = (3.0 * math.cos(angle), 2.0 + 3.0 * math.sin(angle))
    skewed = _member("F", "j0", "joist", (0.0, 2.0), end, 3.02, 3.18)
    model = ResolvedModel(plan=None, floors=[_deck(_BEAM, skewed)])
    assert [c.member_key for c in hung_connections(model, CONFIG.hanger_detection)] \
        == ["F:j0"]


def test_a_zero_length_member_does_not_raise() -> None:
    point = _member("F", "j0", "joist", (0.0, 2.0), (0.0, 2.0), 3.02, 3.18)
    model = ResolvedModel(plan=None, floors=[_deck(_BEAM, point)])
    hung_connections(model, CONFIG.hanger_detection)


def test_a_deck_joist_carries_a_stringer_head_and_nothing_else() -> None:
    edge = _member("F", "joist-edge", "joist", (0.0, 0.0), (1.0, 0.0), 3.0, 3.2)
    stringer = _member("S", "stringer-0", "stringer", (0.5, 1.5), (0.5, 0.0), 2.0, 2.3,
                       profile="2x12", z0_end_m=2.9, z1_end_m=3.19)
    tail = _member("F", "joist-tail", "joist", (0.5, 0.0), (0.5, -1.0), 3.0, 3.2)
    found = hung_connections(ResolvedModel(plan=None, floors=[_deck(edge, tail)]),
                             CONFIG.hanger_detection)
    assert found == [], "a joist ending on a joist is blocking, not a hanger"
    stair = ResolvedStair(uid="S", tag="ST-T", storey="main", to_storey="main", outline=[],
                          riser_count=4, riser_height_m=0.18, tread_depth_m=0.28,
                          run_direction="y", run_reversed=True, layout="straight",
                          turn_direction=None, winder_count=0, members=(stringer,))
    model = ResolvedModel(plan=None, floors=[_deck(edge, tail)], stairs=[stair])
    assert [(c.member_key, c.carrier_tag, c.sloped)
            for c in hung_connections(model, CONFIG.hanger_detection)] \
        == [("S:stringer-0", "F:joist-edge", True)]


def test_st_g_service_hangs_on_the_garage_landing(catlin_model_ro) -> None:
    """Its two stringer heads hang on FS-BW-GARAGE's north-edge 2x8, not on BM-BW-FC/FE,
    which run alongside them."""
    stair = next(s for s in catlin_model_ro.stairs if s.tag == "ST-G-SERVICE")
    landing = next(f for f in catlin_model_ro.floors if f.tag == "FS-BW-GARAGE")
    landing_keys = {f"{m.parent_uid}:{m.child_key}" for m in landing.members}
    heads = [c for c in hung_connections(catlin_model_ro, CONFIG.hanger_detection)
             if c.member_key.startswith(f"{stair.uid}:stringer-")]
    assert len(heads) == 2
    assert all(c.carrier_tag in landing_keys and c.sloped for c in heads), heads
    assert len({c.carrier_tag for c in heads}) == 1
    rows = [row for row in hardware_takeoff(catlin_model_ro)
            if row.get("part_number") == "LSSR" and row["basis"].startswith("2 x 2x12")]
    assert [row["count"] for row in rows] == [2], rows
