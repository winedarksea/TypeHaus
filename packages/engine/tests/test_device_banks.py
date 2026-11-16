"""Gang banks and wall plates (resolve/device_banks.py)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from typehaus.model.electrical import BoxRow, BoxStandard, PlateRow
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.device_banks import PendingBox, _Member, _place, _plate
from typehaus.resolve.device_boxes import BoxPlan
from typehaus.resolve.model import ResolvedCanvasObject


def _bank(catlin_model_ro, tag):
    return next(b for b in catlin_model_ro.device_boxes if tag in b.device_tags)


def test_a_four_gang_snaps_to_the_gang_pitch(catlin_model_ro):
    bank = _bank(catlin_model_ro, "ED-M-LIVING-SW")
    assert (bank.gangs, bank.box_product) == (4, "PROD-CARLON-BH464A")
    objs = {o.tag: o for o in catlin_model_ro.canvas_objects}
    tx, ty = -bank.normal[1], bank.normal[0]
    stations = [objs[t].position[0] * tx + objs[t].position[1] * ty for t in bank.device_tags]
    gaps = sorted(abs(b - a) / M_PER_IN for a, b in zip(stations, stations[1:], strict=False))
    assert gaps == pytest.approx([1.8125] * 3, abs=1e-6)
    assert sum(bank.snap_shifts_m) == pytest.approx(0.0, abs=1e-9)  # centred on the bank
    assert bank.uid == f"{min(bank.device_uids)}-box"


def _standard(**over):
    row = BoxRow(mounting="flush", gangs=1, box_product_ref="B1",
                 box_size=(inch(2.25), inch(3.75), inch(3.5)), box_volume_in3=22.0)
    plate = PlateRow(family="midway", openings=("decora",), product_ref="P1",
                     size=(inch(3.13), inch(4.88)), thickness=inch(0.25))
    return BoxStandard(uid="X", tag="BS", surface_drop=inch(0.75), rows=(row,),
                       plates=(plate,), default_plate="midway", **over), row


def _member(row, kind="switch", plate=None, ptype=None):
    item = NS(tag="ED-1", uid="U1", kind=NS(value=kind), plate=plate, circuit="C1",
              location=NS(attachment=NS(wall_ref="W")))
    plan = BoxPlan("flush", 1, row, 0.0, 0.1, "stud")
    return _Member(PendingBox(0, item, ptype, plan, "L1", None, (1.0, 1.1)), (0.0, 0.0),
                   (1.0, 0.0), (0.0, 1.0), 0.0, 1.05, 1)


def test_plate_family_and_exclusions():
    standard, row = _standard()
    plan = BoxPlan("flush", 1, row, 0.0, 0.1, "stud")
    assert _plate([_member(row)], plan, standard, []).product_ref == "P1"
    assert _plate([_member(row, kind="light")], plan, standard, []) is None  # canopy covers it
    findings: list = []
    assert _plate([_member(row, plate="claro")], plan, standard, findings) is None
    assert findings and findings[0].check_id == "integrity.device_plate"
    included = row.model_copy(update={"plate_included": True})
    assert _plate([_member(included)], BoxPlan("flush", 1, included, 0.0, 0.1, "stud"),
                  standard, []) is None


def test_a_plated_device_stands_off_by_the_plate():
    standard, row = _standard()
    member = _member(row)
    obj = ResolvedCanvasObject(uid="U1", tag="ED-1", storey="L1", domain="electrical",
                               kind="ElectricalDevice", type_ref=None, room=None,
                               position=(0.0, 0.0), z_m=1.0, rotation_degrees=0.0,
                               footprint=[(0, 0), (0.03, 0), (0.03, 0.005), (0, 0.005)])
    wall = NS(tag="W", members=())
    model = NS(wall=lambda ref: wall, solids=[], device_boxes=[], walls=[wall])
    objects = [obj]
    _place(model, [member], member.pending.plan, standard, objects, [])
    assert objects[0].position[1] == pytest.approx(0.25 * M_PER_IN)
    assert model.device_boxes[0].plate_thickness_m == pytest.approx(0.25 * M_PER_IN)
    assert {s.category for s in model.solids} == {"wall_plate", "electrical_box"}


def test_every_boxed_device_draws_a_symbol(catlin_model_ro):
    """A boxed device without a symbol draws the fallback prism over its own box."""
    from typehaus.model.canvas import model_symbol_for
    from typehaus.model.placeable_symbols import _REGISTRY
    from typehaus.resolve.device_boxes import boxes_by_device

    types = {t.tag: t for t in catlin_model_ro.plan.library.electrical_device_types}
    objs = {o.tag: o for o in catlin_model_ro.canvas_objects}
    boxes = boxes_by_device(catlin_model_ro)
    bare = [tag for tag, box in boxes.items()  # lights draw through the luminaire path
            if box.device_kinds[box.device_tags.index(tag)] != "light"
            and model_symbol_for(types.get(objs[tag].type_ref or "")) not in _REGISTRY]
    assert not bare
