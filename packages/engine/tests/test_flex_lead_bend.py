"""A port kit's flex lead that turns: ``houses/catlin/notes/flex_lead_bend_basis.md`` §2-§3."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus.checks.mep.erv_static_terms import _flex_bend_loss, velocity_pressure_in_wg
from typehaus.model.ducts import PortKit
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.duct_standard import duct_standard
from typehaus.resolve.flex_bend import flex_bend, run_bend
from typehaus.routing.duct_fittings import kit_lead

_KIT = PortKit(type_ref="T", flex_product_ref="FLEX", flex_length=inch(12))


def _in(x: float) -> float:
    return x * M_PER_IN


@pytest.mark.parametrize("d, flex, corner, out", [(6, 12.0, 8.0, 6.575), (8, 14.566, 10.0, 8.0)])
def test_the_note_s_bend_table(d, flex, corner, out):
    """R = D, 2" straight, arc R pi/2: the 8" arc alone (12.566") outruns Broan's 12"."""
    bend = flex_bend(_KIT, _in(d))
    assert bend.radius_m / M_PER_IN == pytest.approx(d)
    assert bend.arc_m / M_PER_IN == pytest.approx(d * math.pi / 2)
    assert bend.flex_m / M_PER_IN == pytest.approx(flex, abs=5e-4)
    assert bend.corner_m() / M_PER_IN == pytest.approx(corner)
    assert bend.out_m / M_PER_IN == pytest.approx(out, abs=5e-4)
    lead = kit_lead(_KIT, needs_transition=False, diameter_m=_in(d), bend_deg=90.0)
    assert lead.inches == pytest.approx(flex, abs=5e-4)
    assert lead.corner_m / M_PER_IN == pytest.approx(corner)
    assert kit_lead(_KIT, needs_transition=False).bend is None  # straight stays the default
    assert flex_bend(_KIT.model_copy(update={"connector": True}), _in(d)) is None


def test_an_authored_first_vertex_is_a_flex_bend_only_where_the_straight_lead_cannot_fit(
        catlin_plan):
    """Up 10" then west: the arc seats (corner >= 10"), the straight lead (12 + 12" take-off)
    does not fit, so the vertex is the kit's bend; up 30" the straight lead fits."""
    standard, _ = duct_standard(catlin_plan)
    kit = standard.port_kit("EQ-T-BROAN-B210E75RT", "outdoor")

    def duct(rise_in):
        return SimpleNamespace(diameter_m=_in(8), path=[(0.0, 0.0), (0.0, 0.0), (_in(-60), 0.0)],
                               z_m=[0.0, _in(rise_in), _in(rise_in)])

    hit = run_bend(duct(10.0), 0, kit, standard)
    assert hit is not None and hit[1] == 1
    assert hit[0].flex_m / M_PER_IN == pytest.approx(14.566, abs=5e-4)
    assert run_bend(duct(9.0), 0, kit, standard) is None  # the arc does not seat
    assert run_bend(duct(30.0), 0, kit, standard) is None  # the straight lead fits


def test_the_bend_is_charged_c_on_the_flex_s_velocity_pressure(catlin_plan):
    """Measured C (LBNL Table 4: 2.85 at 8") where authored; else the stock elbow, with a gap."""
    standard, _ = duct_standard(catlin_plan)
    ctx = SimpleNamespace(model=SimpleNamespace(canvas_objects=[
        SimpleNamespace(tag="EQ-B-ERV", type_ref="EQ-T-BROAN-B210E75RT")]))
    duct = SimpleNamespace(tag="DU", diameter_m=_in(8))
    part = SimpleNamespace(other="EQ-B-ERV", port="outdoor", bend_deg=90.0)
    vp = velocity_pressure_in_wg(210.0, _in(8))
    gaps: list[str] = []
    bare = standard.model_copy(update={"port_kits": tuple(
        k.model_copy(update={"flex_bend_loss_c": None}) for k in standard.port_kits)})
    assert _flex_bend_loss(ctx, duct, part, bare, 210.0, gaps) == pytest.approx(0.22 * vp)
    assert "stock elbow" in gaps[0]
    gaps = []
    measured = _flex_bend_loss(ctx, duct, part, standard, 210.0, gaps)  # catlin authors 2.85
    assert measured == pytest.approx(2.85 * vp) and not gaps
    assert measured == pytest.approx(0.0643, abs=5e-5)  # 16.0 Pa: the note's table


def test_the_router_turns_an_exact_ports_lead_toward_the_far_end(catlin_model_ro):
    """The supply port (z -33.838", faces +z): a far end 10 ft west and below turns the 6" lead
    west at the corner 8" up; one 100" straight above keeps the straight lead."""
    from dataclasses import replace

    from typehaus.cli.route_ports import with_port_leads
    from typehaus.cli.route_support import _endpoints
    from typehaus.resolve.mep_ports import placed_ports

    model = catlin_model_ro
    port = next(p for p in placed_ports(model)
                if p.equipment_tag == "EQ-B-ERV" and p.port_tag == "supply")
    origin = (port.x_m, port.y_m, port.z_m)
    ends = replace(_endpoints(model, "DU-B-ERV-SUP-TRUNK", "run", []), origin=origin,
                   origin_lead=None, root_lead=None, root_paths=(), advice=())
    west = with_port_leads(model, replace(ends, root=(origin[0] - _in(120), origin[1],
                                                      origin[2] - _in(12)))).origin_lead
    assert (west.direction, west.heading) == ("+z", "-x")
    assert west.corner[2] - origin[2] == pytest.approx(_in(8.0))
    assert west.tip[0] - west.corner[0] == pytest.approx(-_in(6.575), abs=_in(5e-4))
    up = with_port_leads(model, replace(ends, root=(*origin[:2], origin[2] + _in(100)))).origin_lead
    assert up.corner is None and up.heading == ""
