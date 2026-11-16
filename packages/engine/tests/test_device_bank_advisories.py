"""Gang-bank advisories and the bank-aware box fill (synthetic records, no house)."""

from __future__ import annotations

from types import SimpleNamespace as NS

from typehaus.checks.advisory.device_banks import device_bank, wall_plate_clearance
from typehaus.checks.mep.electrical_boxes import _grade
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN

IN = M_PER_IN


def _box(tags=("S1", "S2"), **over):
    n = len(tags)
    ring = ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0))
    # A plate 1 ft wide on a wall along +x, standing 0.2" off the face at y = 0.
    plate = ((1.0, 0.0), (1.3, 0.0), (1.3, 0.2 * IN), (1.0, 0.2 * IN))
    base = dict(
        device_tag=tags[0], device_uid="u", storey="L1", room="R", device_kind="switch",
        circuit="C14", mounting="flush", gangs=n, box_product="BOX", cover_product=None,
        volume_in3=40.0, width_m=0.1, height_m=0.1, depth_m=2.5 * IN, projection_m=0.0,
        cavity_m=None, wall_tag="W", footprint=ring, z0_m=1.0, z1_m=1.2, face_point=(1.15, 0.0),
        normal=(0.0, 1.0), device_tags=tags, device_uids=tuple(f"u{i}" for i in range(n)),
        device_kinds=("switch",) * n, circuits=("C14",) * n, member_footprints=(ring,) * n,
        snap_shifts_m=tuple(0.01 * i for i in range(n)), plate_product="PLATE",
        plate_family="midway", plate_openings=("decora",) * n, plate_size_m=(0.3, 0.12),
        plate_thickness_m=0.2 * IN,
        plate_footprint=plate, air_barrier=False, box_use=None, internal_clamps=None,
        support_fittings=0, terminal_blocks=0, shape="rectangular", device_footprint=ring)
    return NS(**{**base, **over})


def _ctx(boxes, objects=(), standard=None, wall_len=3.0):
    wall = NS(axis=((0.0, 0.0), (wall_len, 0.0)))
    elements = [standard] if standard else []
    return NS(model=NS(device_boxes=boxes, canvas_objects=list(objects), door_casings=[],
                       wall=lambda tag: wall),
              plan=NS(all_elements=lambda: elements))


def test_bank_advisory_lists_banks_only():
    lone = _box(("L1",), plate_product=None)
    (finding,) = device_bank(_ctx([_box(), lone]))
    assert finding.result is Result.PASS and "S1+S2" in finding.message
    assert "+0.39\"" in finding.message and "L1" not in finding.message


def test_plate_clearance_names_the_cabinet_and_a_standard_plate_that_clears():
    cabinet = NS(tag="CAB", kind="Casework", storey="L1", body_z0_m=0.0, body_z1_m=2.0,
                 attachment_wall="W",
                 footprint=((1.3 + 0.1 * IN, 0.0), (2.0, 0.0), (2.0, 0.5), (1.3 + 0.1 * IN, 0.5)))
    row = NS(product_ref="PLATE", openings=("decora", "decora"))
    slim = NS(size=(NS(meters=0.28), NS(meters=0.12)))
    standard = NS(element_kind="BoxStandard", plates=[row],
                  plate_for=lambda fam, op: slim if fam == "standard" else None)
    (finding,) = wall_plate_clearance(_ctx([_box()], [cabinet], standard))
    assert finding.result is Result.ADVISORY and "CAB" in finding.message
    assert "a standard plate clears" in finding.message
    (clear,) = wall_plate_clearance(_ctx([_box()]))
    assert clear.result is Result.PASS
    (end,) = wall_plate_clearance(_ctx([_box()], wall_len=1.2))
    assert "end of W" in end.message


def test_box_fill_counts_each_member_at_its_gauge_and_the_grounds_once():
    c14, c12 = NS(tag="C14", breaker_amps=15, poles=1, neutral=False), \
        NS(tag="C12", breaker_amps=20, poles=1, neutral=False)
    types = {"T": NS(gangs=1, rear_projection=None, model_representation=None)}
    refs = {"S1": "T", "S2": "T"}
    box = _box(circuits=("C14", "C12"), volume_in3=40.0)
    done = _grade(box, {"C14": c14, "C12": c12}, types, refs, {"C14": 2, "C12": 2})
    # S1: (4 + 2) x 2.0 = 12; S2: (4 + 2) x 2.25 = 13.5; shared: (EGC 1 + clamps 1) x 2.25 = 4.5
    assert done.result is Result.PASS and "30.00 in³" in done.message
    assert done.element_tags == ("S1", "S2")
    tight = _grade(_box(circuits=("C14", "C12"), volume_in3=29.0),
                   {"C14": c14, "C12": c12}, types, refs, {"C14": 2, "C12": 2})
    assert tight.result is Result.FAIL
