"""``engineering/retaining_system.py`` against an independently hand-worked free body.

Two jobs, and the second is the more important one.

**The oracle.** ``houses/catlin/notes/sunken_garden_court_free_body.md`` §4 works the closed
court by hand, term by term, in a pass written before this calculation was encoded — the
discipline ``tests/test_wind_loads.py`` keeps for ``typehaus/wind.py`` and
``tests/test_retaining_wall_calc.py`` keeps for the isolated wall. A calculation that only
agrees with itself is not verified.

**The free-pass battery.** ``lateral_support="base"`` is the one field in this model that can
turn a FAIL into a PASS by being *authored*, so every condition ``_verify`` tests is broken
here in turn — the loop opened, the ref pointed at a non-member, the ref pointed at nothing,
the cross-member's concrete taken away — and each is asserted INCOMPLETE and **never OK**. A
verification that has never been shown to fail is not a verification; it is a comment.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.retaining_system import KIND

_M_PER_FT = 0.3048

# §15 of the note (2026-11-22): ONE body off the resolved solids, two planes, the case set.
# Hand-worked there term by term; every figure below is §15's.
#
# Footing plane, 110 pcf, mu 0.35 on the bed (class 3):
#   footings W1/E1 7 x 10.5, W2/E2 7 x 11.5, S 8.333 x 25 (out to out), 1' x 150 = 77,450;
#   strut 11' net of the side footings x 1 x 1 x 150 = 1,650;
#   stems 71.552 sf (27.276' each side line + 17' between) x 9.1198 x 150 = 97,882;
#   heel soil 176 sf (2 x 3' x 16.833' + 3' x 25') x 9.1198 x 110 = 176,559, less the drain
#   columns' 53.77 sf x 5.1198' x (110 - 100) = 2,753 -> W 350,788, mu W 122,776.
#   Thrust 1/2 x 60 x 10.1198^2 + apron 54.63 (L6's capped AB legs) = 3,126.94 plf over the
#   25.00' south face (W2/E2's 19.83' cancel but for W-RG-EAST's old 50.48) = 78,174 lb
#   -> dry FS 1.571.
_NOTE_BODY_LB = 350_788.0
_NOTE_RESULTANT_LB = 78_174.0
_NOTE_SOUTH_FACE_FT = 25.0
_NOTE_SIDE_FACE_FT = 19.8333
# §15h: graded on the SPECIFIED bed friction 0.43 and native phi' 25 deg (tan 0.4663);
# presumptive (0.35) dry is 1.571, scaled x 0.43/0.35.
_NOTE_FRICTION_LB = 150_839.0   # 0.43 x 350,788
_NOTE_DRY_FS = 1.930
# Perched at H/2 (water 5.06' over the footing top, bed draining): 3,843.9 plf -> 96,097 lb.
_NOTE_PERCHED_FS = 1.568
# Flooded to the court floor, both sides, uplift 527.33 sf x 62.4 = 32,905: 317,883 / 77,781.
_NOTE_FLOODED_FS = 1.702   # to D-B-SUNKEN's threshold crest, -102.14" (§15j)
# Retained water to the terrace, court empty (reported): 128,344 lb.
_NOTE_RETAINED_FULL_FS = 1.17
# Deep plane at -175.4375", mu 0.25: + bed stone 2,364.65 cf x 100 = 236,465, native under
# the W1/E1/BRKBM beds 158 cf = 17,380, native core 121,644 -> 726,276 lb; dry thrust
# 1/2 x 60 x 14.6198^2 + 50.48 = 6,462.7 x 25 = 161,567. Soakaway full to -127.4375":
# uplift 4.0' x 758.33 sf x 62.4 = 189,280, thrust 6,277.5 x 25 = 156,937.
_NOTE_DEEP_FS = {"dry": 2.09, "lip": 1.594, "flooded": 1.37}
# Strut: two-span continuous reaction, E2 3,122.79 plf over 16.333' and E1's footing 1,593.9
# plf (1/2 x 60 x 7.289^2) over 10.5'. M_B = 71,965; R 45,126 -> Pu 72,201; phi Pn at the
# strut's 5,000 psi: 0.60 x 0.45 x 5,000 x 144 x 0.6836 = 132,890.
_NOTE_STRUT_PU_LB = 72_278.0
_NOTE_STRUT_PHI_PN_LB = 132_890.0
# Plan bending FT-SG-E2 on the G3 ties (owner, 2026-11-23): 3 #5 bundled at the edge (centroid
# 3.94") + the outermost #4 (3.25"): As 1.13, centroid 3.82", z = 42 - 3.82 = 38.18";
# 1.6 x 3,122.79 x 11.5^2 / 8 = 82,598 ft-lb -> Tu 25,960 vs 0.75 x 1.13 x 60,000 = 50,850.
_NOTE_PLAN_DC = 0.51
# Staged backfill at the drawn H/2 rule: 1.24; one side empty 1.04 (§15e).
_NOTE_EXPOSURE_IN = 40.0
_NOTE_EXPOSURE_BAND_IN = (36.0, 48.0)
_NOTE_STAGED_FS = {"rule": 1.529, "empty": 1.28}


def _results(plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(plan)
    return EngineeringResults(EngineeringContext(
        plan=plan, model=model, soil_class="GM"))


def test_the_court_reproduces_the_hand_worked_free_body(catlin_plan) -> None:
    """§15: every case and load-path row, from the landed house. Rows still under their
    limit hold the record INCOMPLETE, each named — an open owner decision, never OK."""
    record = _results(catlin_plan)[f"{KIND}/W-SG-ARCH"]
    states = {state.name: state for state in record.limit_states}
    assert states["sliding, dry"].capacity == pytest.approx(_NOTE_DRY_FS, abs=0.002)
    assert states["sliding, perched at H/2"].capacity == pytest.approx(_NOTE_PERCHED_FS,
                                                                       abs=0.002)
    flooded = states["sliding, court flooded to its lowest threshold"]
    assert flooded.capacity == pytest.approx(_NOTE_FLOODED_FS, abs=0.002)
    deep = states["deep plane, soakaway full to its lip"]
    assert deep.capacity == pytest.approx(_NOTE_DEEP_FS["lip"], abs=0.002)
    strut = states["strut compression"]
    assert strut.demand == pytest.approx(_NOTE_STRUT_PU_LB, rel=0.001)
    assert strut.capacity == pytest.approx(_NOTE_STRUT_PHI_PN_LB, rel=0.001)
    assert "f'c 5,000 as specified" in strut.citation
    assert states["footing plan bending, FT-SG-E2"].ratio == pytest.approx(_NOTE_PLAN_DC,
                                                                          abs=0.005)
    staged = next(s for name, s in states.items() if name.startswith("staged backfill"))
    assert staged.capacity == pytest.approx(_NOTE_STAGED_FS["rule"], abs=0.002)
    assert f"one side empty and two full {_NOTE_STAGED_FS['empty']:.2f}" in staged.citation
    basis = next(b.statement for b in record.bases if "snow and perched water" in b.subject)
    assert "NOT concurrent" in basis and "FS 1.46" in basis   # §15k, printed once
    assert "under snowmelt" not in states
    reported = " ".join(n for n in record.notes if n.startswith("REPORTED"))
    assert f"court empty: FS {_NOTE_RETAINED_FULL_FS:.2f}" in reported
    assert f"deep plane, dry: FS {_NOTE_DEEP_FS['dry']:.2f}" in reported
    assert f"flooded court: FS {_NOTE_DEEP_FS['flooded']:.2f}" in reported
    # The terms, not only their ratio: two errors can cancel inside a safety factor.
    assert f"{_NOTE_RESULTANT_LB:,.0f}" in record.summary or \
        f"{_NOTE_FRICTION_LB:,.0f}" in " ".join(record.notes)
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["body_weight_110"] == pytest.approx(_NOTE_BODY_LB, abs=2.0)
    assert inputs["body_resultant_110"] == pytest.approx(_NOTE_RESULTANT_LB, abs=2.0)
    # Closed on the specified soil parameters; the fallback rows pre-check the lean wall.
    assert record.status is Status.OK, record.summary
    fallback = {n: s.capacity for n, s in states.items() if n.startswith("fallback")}
    assert fallback["fallback lean wall under FT-SG-S: sliding, perched at H/2"] == \
        pytest.approx(1.614, abs=0.002)
    assert fallback["fallback lean wall under FT-SG-S: sliding, flooded court"] == \
        pytest.approx(1.805, abs=0.002)
    # The wall resists north-south only: |FS T - K y| = mu N (verifier, 2026-11-23).
    assert fallback["fallback lean wall under FT-SG-S: staged backfill"] == pytest.approx(
        1.543, abs=0.002)
    assert states["sliding, ground snow on the terrace"].capacity == pytest.approx(
        1.773, abs=0.002)
    # §15l: the balcony columns' ASD base shears read from pier_basis — E-W 4 x 337 = 1,348
    # in quadrature, the governing-axis 1,348 along the resultant: 79,533 lb, FS 1.897.
    wind = states["sliding, dry with the structure's wind on the court (D + H + 0.6W)"]
    assert wind.capacity == pytest.approx(1.897, abs=0.003)
    assert "ASD base shears" in wind.citation
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["bed_friction"] == pytest.approx(0.43)
    assert inputs["restraint_friction"] == pytest.approx(1.00)
    assert inputs["at_rest_efp"] == pytest.approx(60.0)
    assert any("NOT YET CONFIRMED" in b.statement for b in record.bases)


def test_the_east_west_thrusts_cancel_and_the_south_face_is_the_body_s(catlin_plan) -> None:
    """W2/E2 mirror each other, so the resultant is the south push alone — over the body's
    25'-0" projected width, corner squares included, not the south wall's 18'-0" axis."""
    record = _results(catlin_plan)[f"{KIND}/W-SG-ARCH"]
    inputs = {q.name: q.value for q in record.inputs}
    # Mirror images but for the apron: W-RG-EAST keeps its old section until gate G9.
    assert inputs["thrust_W-SG-W2"] == pytest.approx(inputs["thrust_W-SG-E2"], abs=5.0)
    widths = next(n for n in record.notes if n.startswith("EACH PUSH"))
    assert f"W-SG-S {_NOTE_SOUTH_FACE_FT:.2f}'" in widths, widths
    assert f"W-SG-E2 {_NOTE_SIDE_FACE_FT:.2f}'" in widths, widths
    assert inputs["thrust_W-SG-S"] * _NOTE_SOUTH_FACE_FT == pytest.approx(
        _NOTE_RESULTANT_LB, rel=0.001)


def test_the_no_stone_sensitivity_is_the_designs_real_dependency(catlin_plan) -> None:
    """§15: at the site's own mu 0.25 the dry body reads 0.25 / 0.35 x 1.573 = 1.12 — the
    bed's 0.35 is still the margin, and the drawing's "no fabric under the footings" with
    it."""
    record = _results(catlin_plan)[f"{KIND}/W-SG-ARCH"]
    dry = next(s for s in record.limit_states if s.name == "sliding, dry")
    assert 0.35 / 0.43 * dry.capacity == pytest.approx(1.571, abs=0.005)
    assert 0.25 / 0.43 * dry.capacity == pytest.approx(1.12, abs=0.01)
    assert 0.25 / 0.43 * dry.capacity < 1.5


def test_every_member_quotes_the_courts_answer_and_carries_it_in_its_fingerprint(
        catlin_plan) -> None:
    """A wall's own record depends on the court, visibly and in the hash."""
    results = _results(catlin_plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        record = results[f"retaining_wall/{tag}"]
        assert record.status is Status.OK, record.summary
        by_name = {state.name: state for state in record.limit_states}
        assert "sliding" not in by_name
        assert by_name["base restraint"].capacity == pytest.approx(_NOTE_DRY_FS, abs=0.002)
        inputs = {q.name: q.value for q in record.inputs}
        assert inputs["system_demand"] == pytest.approx(_NOTE_RESULTANT_LB, rel=0.001)
        assert inputs["system_capacity"] == pytest.approx(_NOTE_FRICTION_LB, rel=0.001)
        assert by_name["overturning"].ok and by_name["bearing"].ok
        assert by_name["eccentricity"].ok and by_name["stem flexure"].ok


def test_the_native_under_the_stone_bears_the_footing_spread_at_two_to_one(catlin_plan) -> None:
    """§15m, hand-worked: q = W/B_z (1 + 6e/B_z) + 100 pcf x 3.5', B_z = B + 42" of stone."""
    results = _results(catlin_plan)
    for tag, q_hand in (("W-SG-E2", 1118.5), ("W-SG-W2", 1118.5), ("W-SG-S", 898.6)):
        record = results[f"retaining_wall/{tag}"]
        state = next(s for s in record.limit_states
                     if s.name == "bearing on the native under the stone")
        assert state.demand == pytest.approx(q_hand, abs=0.1)
        assert state.capacity == 2000.0 and state.ok
        inputs = {q.name: q.value for q in record.inputs}
        assert inputs["bed_thickness"] == pytest.approx(42.0, abs=0.01)
        assert inputs["soil_presumed"] == 1.0


def test_the_run_tops_out_on_the_porch_datum_and_its_exposure_is_a_result(
        catlin_plan) -> None:
    """One form height across all five court walls, and the 36" is derived from it.

    The owner's figure was always a BAND — around 36" out of the yard, up to about 48",
    because a freestanding wall this tall may be read as a guard. It was recorded in
    ``SPEC.retaining_top_ft`` as a MAXIMUM (``(site_grade_in + 36) / 12``), which is the
    opposite constraint: under it a lower yard would have pulled five wall tops down rather
    than letting the exposure grow into the band.

    Both halves are asserted here because each catches a different mistake. The flush tops
    catch a jog reappearing in the form line; the exposure catches the constraint being
    inverted again.

    **The exposure is measured against the AUTHORED YARD, not against ``Site.grade``.** The
    -2'-10" global plane is the near-house bench; the yard these walls stand in is -3'-4",
    and grading the exposure against the wrong one reports 34" for a wall that is 40" out
    of the ground beside it. That is also why this is an equality and not an inequality
    against the plane — see ``params/sunken_garden.RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN``.
    """
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tops = {wall.tag: round(wall.z1_m, 9) for wall in model.walls
            if wall.tag in {"W-SG-W1", "W-SG-E1", "W-SG-W2", "W-SG-E2", "W-SG-S"}}
    assert len(tops) == 5, tops
    assert set(tops.values()) == {0.0}, tops

    yard_m = min(spot.elevation.meters
                 for spot in catlin_plan.project.site.spot_elevations
                 if spot.kind == "grade")
    exposure_in = (0.0 - yard_m) / 0.0254
    assert exposure_in == pytest.approx(_NOTE_EXPOSURE_IN, abs=0.01)
    low, high = _NOTE_EXPOSURE_BAND_IN
    assert low <= exposure_in <= high


def test_the_stem_is_reinforced_and_a_plain_one_would_not_be_covered_at_all(
        catlin_plan) -> None:
    """§6. The bar schedule is what makes the section work, and it is 4.5x, not marginal.

    ** ⚠ THE GEOMETRY BELOW IS A DELIBERATELY FROZEN MECHANICS ORACLE. DO NOT "CORRECT" IT
    TO THE HOUSE. ** It is the court as it stood when §6 was first worked — stem 10.3698',
    H 11.3698' — and the wall has come down three times since (to 9.62'/10.62' when the
    footings rose, to 9.2865'/10.2865' at the 36" cap, to 9.1198'/10.1198' when the five
    court walls came flush with the porch datum). Nothing here reads the plan, so it passes
    unchanged while the house moves under it, and that is the point: these twelve numbers
    are what an independent hand pass produced from these inputs, and the job of this test
    is to prove `stem_flexure` still reproduces them. Re-deriving the inputs from today's
    model would test the arithmetic against itself and verify nothing.

    The live house's stem ratio is pinned where it belongs, against the landed model:
    `test_the_court_reproduces_the_hand_worked_free_body` above, and
    `test_concrete_cover.test_the_third_inch_on_the_garden_stems_is_pinned`.
    """
    from typehaus.engineering.retaining_basis import _Geometry, analyse, stem_flexure
    from typehaus.engineering.soil import presumptive

    geometry = _Geometry(
        tag="W-SG-E2", stem_thickness_ft=1.0, stem_height_ft=10.3698,
        footing_width_ft=8.0, footing_depth_ft=1.0, toe_ft=4.0, heel_ft=3.0,
        retained_height_ft=11.3698)
    case = analyse(geometry, presumptive("GM"), at_rest=True, soil_pcf=110.0)

    plain_demand, plain_capacity, _how = stem_flexure(geometry, case)
    assert plain_demand == pytest.approx(17_841.0, rel=0.001)
    assert plain_capacity == pytest.approx(3_944.0, rel=0.001)
    assert plain_demand / plain_capacity == pytest.approx(4.52, abs=0.02)

    reinforced = _Geometry(**{**geometry.__dict__,
                              "vertical_reinforcement": '#6 @ 10" o.c.'})
    _demand, capacity, how = stem_flexure(reinforced, case)
    assert capacity == pytest.approx(21_639.0, rel=0.001)
    assert plain_demand / capacity == pytest.approx(0.82, abs=0.01)
    assert "0.528" in how
    # `#6 @ 12"` is the arithmetic minimum and is deliberately NOT what the house authors.
    thin = _Geometry(**{**geometry.__dict__, "vertical_reinforcement": '#6 @ 12" o.c.'})
    assert plain_demand / stem_flexure(thin, case)[1] > 0.97


def test_the_footings_narrowed_inboard_only_and_the_outboard_reach_held(catlin_model) -> None:
    """§3. The outboard reach is the invariant; the toe is what moves under it.

    The raised garden's apron measures its 3'-0" clear off these walls' OUTBOARD faces — the
    owner's figure, from the brief — so the strip's outboard reach off the wall axis may not
    move. At 96" with a 6" inboard offset it was 96/24 - 6/12 = 3.5'; at 84" centred it is
    84/24 = 3.5'. The toe took both changes, into the court where nothing is.

    ** THE AXES MOVED 1'-0" IN ON 2026-09-22 ** (17'-0" court, §12): W2 at x = 9'-0", E2 at
    27'-0". The edges went with them and the apron, which is read off the same walls, went
    too — so the reach is asserted off the axis, not as an absolute x.
    """
    x_w, x_e = 9.0, 27.0
    edges = {}
    for solid in catlin_model.solids:
        if solid.tag in ("FT-SG-W2", "FT-SG-E2", "FT-SG-S"):
            xs = [x / _M_PER_FT for x, _ in solid.outline]
            ys = [y / _M_PER_FT for _, y in solid.outline]
            edges[solid.tag] = (min(xs), max(xs), min(ys), max(ys))

    # Outboard edges: 3.5' off each axis (5.5 / 30.5; 4.5 / 31.5 before the court narrowed).
    assert x_w - edges["FT-SG-W2"][0] == pytest.approx(3.5, abs=1e-6)
    assert edges["FT-SG-E2"][1] - x_e == pytest.approx(3.5, abs=1e-6)
    # -32.8333 until the court shortened: wall axis -27.3333 less half the 7'-0" strip.
    assert edges["FT-SG-S"][2] == pytest.approx(-30.8333, abs=1e-3)
    # Inboard edges, 3.5' into the court.
    assert edges["FT-SG-W2"][1] - x_w == pytest.approx(3.5, abs=1e-6)
    assert x_e - edges["FT-SG-E2"][0] == pytest.approx(3.5, abs=1e-6)
    # FT-SG-S's toe is 16" longer (2026-09-22, free body §12a): 4.8333' into the court.
    assert edges["FT-SG-S"][3] == pytest.approx(-22.5, abs=1e-3)
    # 7'-0" overall on W2/E2, 8'-4" on S; the heel still 3'-0" on all three.
    for tag, (x0, x1, y0, y1) in edges.items():
        span = (x1 - x0) if tag != "FT-SG-S" else (y1 - y0)
        assert span == pytest.approx(7.0 if tag != "FT-SG-S" else 100 / 12, abs=1e-6), tag

    # The field is what the three toes leave: 11'-0" square.
    field = next(s for s in catlin_model.solids if s.tag == "SL-SG-FIELD")
    fx = [x / _M_PER_FT for x, _ in field.outline]
    fy = [y / _M_PER_FT for _, y in field.outline]
    assert max(fx) - min(fx) == pytest.approx(11.0, abs=1e-6)
    assert max(fy) - min(fy) == pytest.approx(11.0, abs=1e-6)
    assert min(fy) == pytest.approx(edges["FT-SG-S"][3], abs=1e-6)


def test_the_net_rim_laps_no_footing(catlin_model) -> None:
    """The court's one unasserted invariant, asserted (2026-09-10).

    ``SL-SG-FLOOR``'s ``outline`` spans the whole court and its five ``FO-SG-TOE-*`` voids
    cut it back over the five wall footings, so the rim bills NET concrete while every
    derivation that gates on ``category == "slab"`` still sees one floor. That only holds if
    the voids exactly cover the footings: a lap bills the same cubic foot twice, in two
    sections, and **nothing grades it.** ``structural.concrete_interference`` reports on
    ISOLATED pours and every ``FT-SG-*`` carries ``under=``, so a lap here reads as 0 FAIL.

    It lived as a comment in ``params/sunken_garden.py`` and as a hand measurement in the
    free-body note for five days. The 2026-09-10 pass moved BOTH of its inputs at once — the
    court's clear length and the strips' toe reach — which is the moment to stop measuring it
    by hand.
    """
    from shapely.geometry import Polygon

    solids = {s.tag: s for s in catlin_model.solids}
    rim = solids["SL-SG-FLOOR"]
    net = Polygon(list(rim.outline))
    assert rim.voids, "SL-SG-FLOOR resolves no voids; the FO-SG-* openings are not landing"
    for void in rim.voids:
        net = net.difference(Polygon(list(void)))
    assert net.area > 0, "the rim voided away entirely"

    # The five WALL strips. The two column bases are not among them and never were — they
    # top out at -11.62', two and a half feet under the rim's -9.41' underside, and their
    # shafts pass up through it, so a plan lap there is not a lap. They are `PD-SG-COL` /
    # `PD-SG-FCOL` since 2026-09-14 and no longer `FT-SG-*` at all, so the prefix filter
    # below now selects the five on its own rather than by exclusion.
    footings = ("FT-SG-W1", "FT-SG-W2", "FT-SG-E1", "FT-SG-E2", "FT-SG-S")
    assert set(footings) <= set(solids), sorted(set(footings) - set(solids))
    for tag in footings:
        # These five ARE the court's walking surface: their tops are the rim's top, not its
        # underside. That coplanarity is why a plan lap would be a real double bill.
        assert solids[tag].z1_m == pytest.approx(rim.z1_m, abs=1e-9), (
            f"{tag} no longer tops out on the court floor; this test's premise is that the "
            f"five wall strips and the rim share one plane")
        lap_sf = net.intersection(
            Polygon(list(solids[tag].outline))).area / _M_PER_FT ** 2
        assert lap_sf == pytest.approx(0.0, abs=1e-6), (
            f"the net rim laps {tag} by {lap_sf:.3f} sf — that concrete bills twice, once "
            f"in the slab section and once in the footing one, and no check grades it")


def test_the_strut_is_in_the_footing_plane_and_the_rim_is_cut_off_it(catlin_model) -> None:
    """§8b. W-SG-ARCH is 12" x 12", flush with the court strips top and bottom, and between
    the toes it is the walking surface — FO-SG-STRUT voids the rim over it as the toe voids
    do over the footings. Its depth is the footing thickness by construction, not a residue.
    """
    from shapely.geometry import Polygon

    beam = next(s for s in catlin_model.solids if s.tag == "W-SG-ARCH")
    court = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR")
    footing = next(s for s in catlin_model.solids if s.tag == "FT-SG-W2")
    assert beam.z0_m == pytest.approx(footing.z0_m, abs=1e-9)
    assert beam.z1_m == pytest.approx(footing.z1_m, abs=1e-9)
    assert footing.z1_m == pytest.approx(court.z1_m, abs=1e-9)
    assert (beam.z1_m - beam.z0_m) / _M_PER_FT * 12 == pytest.approx(12.0, abs=1e-6)
    assert court.z1_m / _M_PER_FT * 12 == pytest.approx(-109.4375, abs=1e-6)
    # The net rim never shares plan area with the strut.
    rim = Polygon(list(court.outline))
    for void in court.voids:
        rim = rim.difference(Polygon(list(void)))
    assert rim.intersection(Polygon(list(beam.outline))).area == pytest.approx(0.0, abs=1e-6)
    # The curb over that floor is the flood step, and it is 7 1/4" whatever happens here.
    curb = next(w for w in catlin_model.plan.all_elements()
                if getattr(w, "tag", None) == "W-B-S2")
    assert curb.top_elevation.inches - curb.bottom_elevation.inches == pytest.approx(7.25)


def test_nothing_bears_under_the_strut_between_its_ends(catlin_model) -> None:
    """§7. The strut spans its full length with no intermediate bearing.

    An earlier scheme merged a column pour with the strut and gave it a bearing at midspan,
    halving its span. Until 2026-09-22 this pinned that ``PD-SG-FCOL`` stopped 9" below the
    beam; that pad left with the centre support line (17'-0" court, §12), so what is asserted
    now is the claim itself: under the strut's plan footprint there is no concrete, only drainage
    (its tile, and since 2026-11-02 the ``FD-B-S-LEAD-W``/``-E`` trenches ~22" below it), so §8's
    λ is rightly taken on the whole 18'-0" member.
    """
    from shapely.geometry import Polygon

    solids = {s.tag: s for s in catlin_model.solids}
    assert not {"PD-SG-FCOL", "PD-SG-COL"} & set(solids)
    beam = solids["W-SG-ARCH"]
    footprint = Polygon(list(beam.outline))
    xs = [x / _M_PER_FT for x, _ in beam.outline]
    assert max(xs) - min(xs) == pytest.approx(18.0, abs=1e-6)
    under = [s.tag for s in catlin_model.solids
             if s.tag != beam.tag and s.outline and s.z1_m <= beam.z0_m + 1e-6
             and s.category not in ("drain_tile", "french_drain", "backfill_native", "backfill_cap")
             and Polygon(list(s.outline)).intersects(footprint)]
    assert under == [], under


# --------------------------------------------------------------------------------------
# The free-pass battery. Each of these breaks one condition in ``_verify`` and asserts the
# record goes INCOMPLETE, naming what is missing — never OK, and never silently OK-by-absence.
# --------------------------------------------------------------------------------------

def _mutated(tmp_path, replacements):
    from pathlib import Path

    from _helpers import copy_house

    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    house = copy_house(catlin, tmp_path / "house")
    source = house / "params" / "sunken_garden.py"
    text = source.read_text()
    for old, new in replacements:
        assert old in text, old
        text = text.replace(old, new)
    source.write_text(text)
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    return result.plan


def _court(plan):
    return _results(plan)[f"{KIND}/W-SG-ARCH"]


def test_opening_the_loop_is_incomplete_not_ok(tmp_path) -> None:
    """Delete the cross-member and the U is open again. **The headline free-pass case.**

    The walls still say ``lateral_support="base"`` and still name ``W-SG-ARCH``. Nothing in
    the authored claim changed — only the thing it claims stopped existing. If this returned
    OK, the field would be a switch that turns the calculation off.
    """
    plan = _mutated(tmp_path, [(
        'Beam(uid="SGW102AAAA", tag="W-SG-ARCH",',
        'Beam(uid="SGW102AAAA", tag="W-SG-ARCH-GONE",')])
    record = _court(plan)
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("W-SG-ARCH" in m for m in record.missing)
    assert record.status is not Status.OK

    # And every wall that leaned on it goes INCOMPLETE with it, rather than quietly
    # reverting to a free-cantilever PASS.
    results = _results(plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        wall = results[f"retaining_wall/{tag}"]
        assert wall.status is Status.INCOMPLETE, wall.summary


def test_a_ref_that_names_nothing_is_incomplete(tmp_path) -> None:
    """``base_restraint_ref`` pointed at a tag the model does not contain."""
    plan = _mutated(tmp_path, [
        ('base_restraint_ref="W-SG-ARCH"', 'base_restraint_ref="W-SG-IMAGINARY"')])
    record = _results(plan)[f"{KIND}/W-SG-IMAGINARY"]
    assert record.status is Status.INCOMPLETE
    assert any("W-SG-IMAGINARY" in m for m in record.missing)


def test_a_ref_that_names_a_wall_off_the_loop_is_incomplete(tmp_path) -> None:
    """Point the restraint at a real concrete wall that is on no common cycle.

    ``W-SG-W1`` is a real ``FoundationWall``, real cast concrete, in the same structure and
    even touching the same node — and it is a **bridge**, an open arm of the chain, restrained
    by nothing at its far end. Naming it must not work, and "it is a wall and it is concrete"
    must not be enough.
    """
    plan = _mutated(tmp_path, [
        ('base_restraint_ref="W-SG-ARCH"', 'base_restraint_ref="W-SG-W1"')])
    record = _results(plan)[f"{KIND}/W-SG-W1"]
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("closed structural loop" in m for m in record.missing)


def test_a_cross_member_with_no_concrete_is_incomplete(tmp_path) -> None:
    """The loop has to be CAST. A framed cross-member cannot deliver the strut force."""
    plan = _mutated(tmp_path, [(
        'assembly="SUNKEN_GARDEN_GRADE_BEAM_12",\n         top_elevation=_grade_beam_top)',
        'assembly="EXT_2X6",\n         top_elevation=_grade_beam_top)')])
    record = _court(plan)
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("concrete" in m for m in record.missing)


def test_half_authoring_the_claim_reaches_no_restraint(catlin_plan, tmp_path) -> None:
    """``lateral_support="base"`` without a ref, and a ref without ``"base"``.

    A half-authored claim is the shape a free pass arrives in, so neither half alone may
    reach a restrained grading. Dropping the ref leaves the walls in the retaining_wall
    suite with no system to quote — which must be INCOMPLETE, not a silent fall-back to the
    free-cantilever numbers that used to FAIL.
    """
    plan = _mutated(tmp_path, [
        ('lateral_support="base", base_restraint_ref="W-SG-ARCH"',
         'lateral_support="base"')])
    results = _results(plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        record = results[f"retaining_wall/{tag}"]
        assert record.status is Status.INCOMPLETE, record.summary
        assert any("base restraint" in m for m in record.missing), record.missing


def test_a_base_restrained_wall_never_reaches_the_prescriptive_table(catlin_plan) -> None:
    """The most dangerous mis-step in the whole change, asserted directly.

    Table R404.1.2(8) footnote g presumes bracing top AND bottom. A ``"base"`` wall falling
    through to it would collect a prescriptive PASS with no engineering behind it — worse
    than the FAIL it replaced, because a FAIL is visible. ``_grade_one`` must send it to the
    R404.4 handoff beside ``"unsupported"``.
    """
    from _helpers import check_context

    from typehaus.checks.structural.foundation import foundation_unbalanced_fill
    from typehaus.findings import Authority, Result

    findings = foundation_unbalanced_fill(check_context(plan=catlin_plan))
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        mine = [f for f in findings if tag in f.element_tags]
        assert mine, tag
        for finding in mine:
            assert finding.authority is Authority.ENGINEERED, finding.message
            assert finding.engineering_item == f"retaining_wall/{tag}"
            assert "R404.4" in finding.message
            assert "Table R404.1.2(8)" in finding.message
            assert finding.result is not Result.FAIL

    # And the two braced porch walls are still answered by the table, prescriptively.
    porch = [f for f in findings
             if "W-SG-W1" in f.element_tags or "W-SG-E1" in f.element_tags]
    assert porch
    assert all(f.authority is Authority.PRESCRIPTIVE and f.result is Result.PASS
               for f in porch), [f.message for f in porch]


def test_the_restrained_walls_stay_in_the_engineering_suite(catlin_plan) -> None:
    """A wall that stops being computed reads exactly like a wall with no problem."""
    from typehaus.engineering import EngineeringContext
    from typehaus.engineering.retaining_wall import enumerate_walls
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tags = set(enumerate_walls(EngineeringContext(plan=catlin_plan, model=model)))
    assert tags == {"W-SG-E2", "W-SG-S", "W-SG-W2"}


def test_the_specified_soil_is_pending_until_the_report_and_fails_below_it(catlin_plan) -> None:
    """§15h, the truss pattern: UNKNOWN until Site.confirmed_soil is entered; a report short
    of the specified values FAILs the confirmation and the court's rows grade on it."""
    from types import SimpleNamespace

    from typehaus.checks.structural.soil_parameters import soil_parameters_confirmed
    from typehaus.findings import Result
    from typehaus.model.site import SoilParameters
    from typehaus.resolve import resolve

    site = catlin_plan.project.site
    model, _ = resolve(catlin_plan)

    def run(plan):
        return soil_parameters_confirmed(SimpleNamespace(plan=plan))[0].result

    assert run(catlin_plan) is Result.UNKNOWN
    short = SoilParameters(bed_friction=0.40, native_phi_deg=30.0, source="report")
    plan = catlin_plan.model_copy(update={"project": catlin_plan.project.model_copy(
        update={"site": site.model_copy(update={"confirmed_soil": short})})})
    assert run(plan) is Result.FAIL
    high = SoilParameters(bed_friction=1.10, native_phi_deg=30.0, source="report")
    over = catlin_plan.model_copy(update={"project": catlin_plan.project.model_copy(
        update={"site": site.model_copy(update={"confirmed_soil": high})})})
    assert run(over) is Result.FAIL   # above bed_friction_max 1.00: the winter rows
    from typehaus.engineering import EngineeringContext, EngineeringResults

    record = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))[
        f"{KIND}/W-SG-ARCH"]
    assert record.status is Status.OVER, record.summary


pytestmark = pytest.mark.slow
