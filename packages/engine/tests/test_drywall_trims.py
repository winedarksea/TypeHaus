"""Drywall accessories off catlin's DrywallStandard (decision #103)."""

import copy
import dataclasses

import pytest
from shapely.geometry import LineString, Polygon

from typehaus.resolve.drywall_led import drywall_standard, host_plaster_in_runs

_IN = 0.0254
_COVES = {"LR-M-LIVING-W", "LR-M-LIVING-E", "LR-M-BATH2-TUB-CLG", "LR-S-HALL-GAP"}


def test_the_four_coves_are_plaster_in_and_slot_their_host(catlin_model_ro):
    model = catlin_model_ro
    plaster = {run.tag: run for run in model.light_runs if run.profile == "plaster_in"}
    assert set(plaster) == _COVES
    soffits = {soffit.tag: soffit for soffit in model.soffits}
    for run in plaster.values():
        slot = LineString(run.path).buffer(run.aperture_m / 2.0 - 1e-4, cap_style=2,
                                           join_style=2)
        if run.host_ref in soffits:
            boards = [Polygon(p.prism.ring, p.prism.voids)
                      for p in soffits[run.host_ref].finish_panels
                      if p.key.startswith("underside")]
            assert abs(run.z_m - soffits[run.host_ref].z0_m) < 1e-9
        else:
            boards = [Polygon(s.outline) for s in model.solids
                      if s.category == "ceiling" and s.uid.startswith(run.host_ref)]
            assert len(boards) > 1, "the slot splits the ceiling into pieces"
        assert boards and sum(board.intersection(slot).area for board in boards) < 1e-9
        # The profile's record bills the run's own length.
        assert sum(t.length_m for t in model.drywall_trims
                   if t.kind == "led_profile" and run.tag in t.tags) == pytest.approx(
            run.length_m)


def test_trimless_door_bead_and_living_corner_by_hand(catlin_model_ro):
    model = catlin_model_ro
    # D-M-BED2's RO is 34.236" x 83.012": 2 x 83.012 + 34.236 = 200.26" a face, two faces.
    bead = [t for t in model.drywall_trims if t.kind == "door_l_bead" and "D-M-BED2" in t.tags]
    assert len(bead) == 2
    assert sum(t.length_m for t in bead) / _IN == pytest.approx(2 * 200.26, abs=0.02)
    # RM-M-LIVING's outside corners run its LVP (+15/16") to the 5/8" ceiling face at
    # 9'-1/8" less 5/8" = 107 1/2": 106 9/16".
    corners = [t for t in model.drywall_trims
               if t.kind == "outside_corner" and t.room == "RM-M-LIVING"]
    assert corners and all(t.length_m / _IN == pytest.approx(106.5625, abs=1e-3)
                           for t in corners)


def test_a_cove_off_its_wall_is_an_integrity_error(catlin_model_ro):
    standard, findings = drywall_standard(catlin_model_ro.plan)
    assert standard is not None and not findings
    model = copy.copy(catlin_model_ro)
    model.solids = list(catlin_model_ro.solids)
    model.light_runs = [
        dataclasses.replace(run, profile="surface", section=(),
                            path=[(x + 6 * _IN, y) for x, y in run.path])
        if run.tag == "LR-M-LIVING-W" else run
        for run in catlin_model_ro.light_runs]
    found = host_plaster_in_runs(model, standard)
    assert [(f.check_id, f.element_tags) for f in found] == [
        ("integrity.light_run_host", ("LR-M-LIVING-W",))]
    assert "8.74\"" in found[0].message


def test_jbead_stops_with_the_bare_face_and_slivers_are_not_corners(catlin_model_ro):
    trims = catlin_model_ro.drywall_trims
    # W-M-STRW's mudroom face is open bays to 7'-0" over a +0.94685" floor: the two vertical
    # J-beads stop there; the board above is a horizontal one.
    vertical = sorted(t.length_m / _IN for t in trims
                      if t.kind == "termination" and t.room == "RM-M-MUDROOM")[:2]
    assert vertical == pytest.approx([84 - 0.94685] * 2, abs=1e-3)
    # A clear face's ~1" mitre sliver (the closet's SW corner, the attic's building corners)
    # is an inside corner. SF-S-HP1 butts walls 0.1-0.6" off three sides and SF-S-DUCT's
    # higher board on the fourth: free are its 40 3/4" south edge and its west edge's
    # 35 3/4" over the hall, less the 1" a wall's gap reaches.
    rooms = {t.room for t in trims if t.kind == "outside_corner" and len(t.tags) == 1}
    assert not rooms & {"RM-S-NCLOSET", "RM-B-ESS", "RM-A-POCKET", "RM-S-SUITEBATH"}
    hp1 = sum(t.length_m for t in trims if "SF-S-HP1" in t.tags) / _IN
    assert hp1 == pytest.approx(40.75 + 35.74, abs=1.5)
