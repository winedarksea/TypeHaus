"""Derived window stools and shelf banks — the model and the resolver (→ model/millwork.py).

The reason this module exists in one sentence: the reference house's windows sit in four
host assemblies of four different thicknesses, so a stool depth is a *derivation*, not a
number. Every assertion below is chosen so that authoring a single depth somewhere would
break it.
"""

from __future__ import annotations

import pytest

M_TO_IN = 39.37007874


@pytest.fixture(scope="module")
def stools(catlin_model_ro):
    return catlin_model_ro.window_stools


def _by_assembly(stools) -> dict[str, list]:
    out: dict[str, list] = {}
    for stool in stools:
        out.setdefault(stool.assembly, []).append(stool)
    return out


# --- registration ------------------------------------------------------------------------

def test_the_millwork_kinds_are_registered_elements_and_dialect_constructors() -> None:
    from typehaus.model import element_kinds
    from typehaus.model.registry import constructor_names

    kinds, ctors = element_kinds(), constructor_names()
    for name in ("WindowStool", "ShelfBank", "MillworkStandard", "Countertop"):
        assert name in kinds, f"{name} is not a registered element kind"
        assert name in ctors, f"{name} is not a dialect constructor"
    # ShelfBay is a HausModel, not an Element — it has no identity of its own — but the
    # dialect still has to be able to call it, or the bays cannot be authored.
    assert "ShelfBay" in ctors and "ShelfBay" not in kinds
    assert "StairLandingMillwork" in ctors and "StairLandingMillwork" not in kinds


def test_a_window_type_can_carry_a_frame_depth(catlin_plan) -> None:
    """The one term of the stool derivation that is a product fact and nothing else."""
    types = {wt.tag: wt for wt in catlin_plan.library.window_types}
    assert types, "the catlin library authors window types"
    assert all(wt.frame_depth is not None for wt in types.values()), (
        "every catlin window type authors frame_depth; without it a stool reports UNKNOWN")
    # Not one number for every product: the plant room's triple/warm-edge units are a
    # deeper section than the ordinary double-glazed ones.
    depths = {round(wt.frame_depth.inches, 3) for wt in types.values()}
    assert len(depths) > 1


# --- the derivation ------------------------------------------------------------------------

def test_stools_derive_only_for_the_assemblies_the_standard_scopes(stools, catlin_model_ro):
    """30 windows get derived oak; the plant room's four and the kitchen sink window are
    quartz, and the east row's four are 2" oak meeting the living-room slabs."""
    derived = [stool for stool in stools if stool.derived]
    assert {stool.assembly for stool in derived} == {"EXT_2X6"}
    # Seven of the 42 are out of scope because of their host wall: the four plant-room
    # windows, sauna, and two garage windows. WIN-M-KITCH and the east row are in scope but
    # authored.
    assert len(derived) == 30
    windows = [o for o in catlin_model_ro.openings if o.kind == "window"]
    assert len(windows) == 42, "the seven out-of-scope windows still exist; they get no oak"
    assert all(stool.material_ref == "oak-stool" for stool in derived)
    # The plant room's four and the kitchen sink window are authored in 3 cm quartz; the east
    # row's four in 2" oak, flush with the counter.
    authored = {stool.window_ref: stool for stool in stools if not stool.derived}
    assert set(authored) == {*(f"WIN-S-PLANT{n}" for n in range(1, 5)), "WIN-M-KITCH",
                             "WIN-M-LIV-E1", "WIN-M-LIV-E2", "WIN-M-LIV-E3", "WIN-M-EAST-MID"}
    east = {"WIN-M-LIV-E1", "WIN-M-LIV-E2", "WIN-M-LIV-E3", "WIN-M-EAST-MID"}
    assert all(stool.material_ref == ("oak-stool-12q" if ref in east else "quartz-counter")
               for ref, stool in authored.items())
    assert {stool.window_ref: stool.assembly for stool in authored.values()} == {
        **{f"WIN-S-PLANT{n}": "PLANT_EXT_2X6_HUMID" for n in range(1, 5)},
        "WIN-M-KITCH": "EXT_2X6", **{ref: "EXT_2X6" for ref in east},
    }


def test_quartz_stools_bill_with_the_stone_not_the_mill(catlin_model_ro):
    """A stone stool is the slab yard's: in [countertops] by area, never on the oak list."""
    from typehaus.takeoff.countertops import countertop_takeoff
    from typehaus.takeoff.hardwood import hardwood_takeoff

    quartz = [s for s in catlin_model_ro.window_stools if s.material_ref == "quartz-counter"]
    row = next(r for r in countertop_takeoff(catlin_model_ro)
               if r["material"] == "quartz-counter")
    assert row["stools"] == sorted(s.tag for s in quartz)
    tops = sum(t.area_m2 for t in catlin_model_ro.countertops
               if t.material_ref == "quartz-counter")
    stools = sum(s.length_m * s.depth_m for s in quartz)
    assert row["net_area_sqft"] == pytest.approx((tops + stools) * 10.7639104, abs=0.01)
    milled = {tag for r in hardwood_takeoff(catlin_model_ro) if r["use"] == "window stool"
              for tag in r["tags"]}
    assert milled.isdisjoint(s.window_ref for s in quartz)


def test_a_stools_depth_is_derived_from_its_host_wall_not_authored(stools):
    """depth = (interior finish face -> mount plane) - frame_depth + overhang, per stool.

    Deliberately re-derived here from the record's own two terms rather than compared to a
    constant: a test that pinned one number would pass just as happily against an authored
    depth, which is the exact bug this design exists to prevent.
    """
    for stool in stools:
        assert stool.return_m is not None and stool.frame_depth_m is not None
        expected = stool.return_m - stool.frame_depth_m + stool.overhang_m
        assert stool.depth_m == pytest.approx(expected, abs=1e-9)


def test_the_four_host_assemblies_derive_four_different_returns(catlin_model_ro):
    """The reason a stool cannot carry an authored depth.

    A window's host wall decides its interior return, and the reference house hosts windows
    in four assemblies whose returns are all different. Asserting they are *distinct* — not
    what each one is — is what keeps this honest when a foam lift or a girt depth moves.
    """
    from typehaus.resolve.millwork import interior_return_m

    walls = {wall.tag: wall for wall in catlin_model_ro.walls}
    hosts = {walls[o.host_wall].assembly for o in catlin_model_ro.openings
             if o.kind == "window" and o.host_wall in walls}
    assert len(hosts) == 4
    returns = {}
    for assembly in hosts:
        wall = next(w for w in catlin_model_ro.walls if w.assembly == assembly)
        value = interior_return_m(wall)
        assert value is not None and value > 0.0
        returns[assembly] = round(value * M_TO_IN, 3)
    assert len(set(returns.values())) == 4, f"returns collapsed: {returns}"
    # The two truss walls differ by exactly the plant room's extra liner and furring, which
    # is the whole point: the same window in the two walls needs two different boards.
    assert returns["PLANT_EXT_2X6_HUMID"] > returns["EXT_2X6"]


def test_the_mount_plane_ignores_furring_on_the_inside_face(catlin_model_ro):
    """A liner wall furs its INTERIOR face; a window does not mount on that.

    The sauna's ``liner-furring`` sits 1-1/2" in from the room, inboard of the studs. Taking
    "the outermost FURRING layer" literally would call that the mount plane and return a
    1-1/2" reveal on a 14"-thick wall.
    """
    from typehaus.resolve.millwork import interior_return_m

    wall = next(w for w in catlin_model_ro.walls
                if w.assembly == "SAUNA_LINER_ON_GARDEN_FRAMED")
    assert interior_return_m(wall) * M_TO_IN > 10.0


def test_a_stools_length_is_the_opening_plus_two_horns(stools, catlin_model_ro):
    openings = {o.tag: o for o in catlin_model_ro.openings}
    for stool in stools:
        opening = openings[stool.window_ref]
        assert stool.length_m == pytest.approx(
            opening.width_m + 2.0 * stool.horn_m, abs=1e-9)


def test_the_stool_cut_list_collapses_to_the_three_window_widths(stools):
    """30 oak stools, three sizes — which is what makes them worth milling from few setups."""
    oak = [stool for stool in stools if stool.material_ref == "oak-stool"]
    sizes = {round(stool.length_m * M_TO_IN, 2) for stool in oak}
    assert len(sizes) == 3
    counts = _by_assembly(oak)
    assert sum(len(v) for v in counts.values()) == 30


# --- shelf banks --------------------------------------------------------------------------

def test_the_attic_built_in_keeps_its_explicit_shelf_depth(catlin_model_ro):
    """The stock shelf stays 9-7/8" while its separate carcass includes a 3/4" back."""
    bank = next(b for b in catlin_model_ro.shelf_banks if b.tag == "SB-A-STUDY")
    assert bank.host_kind == "placeable" and bank.host == "FURN-A-STUDY-BUILTIN"
    assert bank.depth_m * M_TO_IN == pytest.approx(9.875, abs=0.01)
    case = next(o for o in catlin_model_ro.canvas_objects if o.tag == bank.host)
    assert bank.depth_m < max(y for _x, y in case.footprint) - min(
        y for _x, y in case.footprint)


def test_the_attic_bays_are_stepped_bays_with_their_own_counts(catlin_model_ro):
    """A uniform spacing does not divide into a raked case; per-bay counts are the point.

    The bay tops come from `5'-0" + (36' - x)/3` off a knee wall; at 6:12 off a rafter
    plate they are `1 1/2" + (36' - x)/2`. The bays STEP, and the counts are per-bay
    because one pitch does not divide into a rake.
    """
    bank = next(b for b in catlin_model_ro.shelf_banks if b.tag == "SB-A-STUDY")
    assert len(bank.shelves) == 3
    heights = [round(shelf.clear_height_m * M_TO_IN, 1) for shelf in bank.shelves]
    assert heights == sorted(heights, reverse=True), "the bays step down under the rake"
    assert len({shelf.count for shelf in bank.shelves}) > 1
    assert sum(shelf.count for shelf in bank.shelves) == 12


def test_a_carcass_hosted_bank_derives_its_depth_from_the_furniture_type(catlin_model_ro):
    """The pantry's 24" is the type's footprint depth, inherited rather than restated.

    Authoring the depth here would be a second source of truth for a number the carcass
    already states — and it is the number that makes every pantry shelf a glue-up.
    """
    bank = next(b for b in catlin_model_ro.shelf_banks if b.tag == "SB-M-PANTRY")
    assert bank.host_kind == "placeable"
    ftype = next(t for t in catlin_model_ro.plan.library.furniture_types
                 if t.tag == "FT-KIT-PANTRY-SHELVES-70")
    assert bank.depth_m == pytest.approx(ftype.footprint[1].meters, abs=1e-9)


def test_every_shelf_bank_resolves_a_host_and_a_depth(catlin_model_ro):
    """Counted against the PLAN rather than a literal, deliberately: comparing to the
    authored count means no authored bank is silently DROPPED — an unresolvable host or an
    underivable depth makes a bank vanish from the model with a finding nobody reads — and
    it needs no edit the next time the house grows a bookcase."""
    from typehaus.model.millwork import ShelfBank

    authored = [el for storey in catlin_model_ro.plan.storeys
                for el in catlin_model_ro.plan.storey_elements(storey.tag)
                if isinstance(el, ShelfBank)]
    assert authored, "the catlin fixture should carry shelf banks at all"
    assert len(catlin_model_ro.shelf_banks) == len(authored)
    for bank in catlin_model_ro.shelf_banks:
        assert bank.host_kind in ("wall", "placeable")
        assert bank.depth_m is not None and bank.depth_m > 0.0
        assert bank.shelves and all(shelf.count > 0 for shelf in bank.shelves)


# --- the declaration ----------------------------------------------------------------------

def test_the_house_declares_exactly_one_millwork_standard(catlin_plan) -> None:
    from typehaus.model.millwork import MillworkStandard

    found = [el for el in catlin_plan.all_elements()
             if isinstance(el, MillworkStandard)]
    assert len(found) == 1
    standard = found[0]
    assert standard.max_board_width.inches == pytest.approx(18.0)
    assert standard.tread_stairs == ("ST-M2S", "ST-S2A")
    assert standard.landing_deck.stair_refs == ("ST-M2S",)
    assert standard.landing_deck.field_material_ref == "oak-floor-custom"
    assert standard.landing_deck.board_face_width.inches == pytest.approx(3.5)
    assert standard.landing_deck.board_coverage_width.inches == pytest.approx(3.125)
    assert standard.landing_deck.nosing_material_ref == "oak-tread"
    assert standard.landing_deck.nosing_depth.inches == pytest.approx(3.5)
    assert standard.landing_deck.stack_thickness_m == pytest.approx(1.5 * 0.0254)
    assert standard.landing_deck.nosing_profile == "landing tread"


def test_a_second_millwork_standard_is_an_error_not_a_winner(catlin_plan) -> None:
    """Two declarations would need a precedence rule nobody could guess from the source."""
    from typehaus.findings import Severity
    from typehaus.model.millwork import MillworkStandard
    from typehaus.quantities import inch
    from typehaus.resolve.millwork import _the_standard

    second = MillworkStandard(
        uid="TESTUIDAAA", tag="MW-SECOND", stool_material_ref="oak-stool",
        stool_thickness=inch(1.5), stool_overhang=inch(0.75), stool_horn=inch(1),
        max_board_width=inch(18))
    storey = catlin_plan.storeys[0].tag
    plan = catlin_plan.with_elements(
        storey, [*catlin_plan.storey_elements(storey), second])
    standard, findings = _the_standard(plan)
    assert standard is None
    assert [f.check_id for f in findings] == ["integrity.millwork_standard"]
    assert findings[0].severity is Severity.ERROR


_M2_TO_FT2 = 10.7639104


# --- countertops -------------------------------------------------------------------------

@pytest.fixture(scope="module")
def countertops(catlin_model_ro):
    return {top.tag: top for top in catlin_model_ro.countertops}


def test_a_countertops_area_is_derived_from_the_cabinets_under_it(countertops):
    """The quantity is a consequence of the layout, which is the whole point of the element.

    Re-derived here from the run rather than compared against one pinned total: a test that
    asserted "61.34 SF" would pass just as happily against a hand figure typed into the
    house, which is exactly what this element replaced.
    """
    M2_TO_FT2 = 10.7639104
    north = countertops["CT-M-KIT-N"]
    # Five hosts: the dishwasher and stock base modules close directly to the carousel.
    assert north.hosts == ("FURN-M-KIT-E1", "APPL-M-DW", "FURN-M-KIT-SINKBASE",
                           "FURN-M-KIT-E2", "FURN-M-KIT-CORNER-NE")
    # 24" of carcass plus the 1" a top oversails its doors — nothing authored the 25".
    assert north.depth_m * M_TO_IN == pytest.approx(25.0, abs=1e-6)
    # The run is straight up to the NE carousel, whose L adds its 13" east-leg tail beyond
    # the 38" it contributes to the length: (length - 38") x 25" + the L's 38x25 + 13x25.
    corner = 38.0 / M_TO_IN
    l_slab = (38.0 * 25.0 + 13.0 * 25.0) / M_TO_IN**2
    expected = ((north.length_m - corner) * north.depth_m + l_slab) * M2_TO_FT2
    assert north.area_m2 * M2_TO_FT2 == pytest.approx(expected, rel=0.01)


def test_the_peninsula_is_one_notched_slab_on_brackets(countertops):
    """Quartz over the bases and the 15" seating knee behind them, for 73 1/2" only."""
    from shapely.geometry import Polygon

    stone = countertops["CT-M-KIT-PENINSULA"]
    assert "CT-M-KIT-PENINSULA-BAR" not in countertops
    assert stone.material_ref == "quartz-counter" and stone.support == "brackets"
    assert stone.depth_m * M_TO_IN == pytest.approx(40.0, abs=1e-6)
    assert stone.unsupported_overhang_m * M_TO_IN == pytest.approx(15.0, abs=1e-6)
    ring = Polygon(stone.outline)
    assert len(stone.outline) == 6
    # 84 1/2 x 25 over the boxes, plus the 73 1/2 x 15 knee.
    assert ring.area * M_TO_IN**2 == pytest.approx(84.5 * 25 + 73.5 * 15, abs=1e-3)
    x0, y0, x1, y1 = (value * M_TO_IN for value in ring.bounds)
    assert (x0, y0, x1, y1) == pytest.approx((302.875, 304.375, 387.375, 344.375))
    # The knee stops 25" short of the pantry's nominal front, x=401 3/8.
    knee = ring.intersection(Polygon([(0, 0), (1e3, 0), (1e3, 319.0 / M_TO_IN),
                                      (0, 319.0 / M_TO_IN)]))
    assert knee.bounds[2] * M_TO_IN == pytest.approx(376.375)


def test_an_l_host_takes_the_slab_over_its_whole_l(countertops):
    """A carousel corner's slab is its L, oversailing only the two notch faces."""
    from shapely.geometry import Polygon

    corner = countertops["CT-M-KIT-E"]
    assert corner.hosts == ("FURN-M-KIT-CORNER-PEN",)
    ring = Polygon(corner.outline)
    # Two 24"-deep legs, 38" long, plus 1" on each of the two 14" notch faces.
    expected = (38 * 25 + 13 * 25) / 144.0
    assert ring.area * _M2_TO_FT2 == pytest.approx(expected, abs=1e-6)
    assert len(corner.outline) == 6, "an L, not a rectangle"
    x0, y0, x1, y1 = ring.bounds
    # The backs and the leg ends stay on the 38" box; nothing oversails them.
    assert ((x1 - x0) * M_TO_IN, (y1 - y0) * M_TO_IN) == pytest.approx((38.0, 38.0), abs=1e-6)


def test_one_quartz_slab_over_the_sektion_peninsula_now_passes(countertops):
    """9 5/8" on 34 5/8" is 28%: one-piece quartz is the recorded alternative to the oak."""
    import dataclasses

    from typehaus.checks.advisory.countertops import _grade
    from typehaus.findings import Result

    one_slab = dataclasses.replace(
        countertops["CT-M-KIT-PENINSULA"], depth_m=34.625 / M_TO_IN,
        unsupported_overhang_m=9.625 / M_TO_IN, support="none")
    assert _grade(one_slab).result is Result.PASS


def test_the_peninsula_type_states_how_much_of_its_depth_is_box(catlin_plan):
    """Without this split a 39" top on a 24" carcass reads as fully supported."""
    types = {ft.tag: ft for ft in catlin_plan.library.furniture_types}
    peninsula = types["CASE-PENINSULA-120"]
    assert peninsula.footprint[1].inches == pytest.approx(39.0)
    assert peninsula.carcass_depth is not None
    assert peninsula.carcass_depth.inches == pytest.approx(24.0)


def test_one_quartz_slab_over_the_whole_peninsula_is_a_fail(countertops):
    """The finding the peninsula's brackets exist to avoid — graded, not asserted in prose.

    Caesarstone's published limits: 1/3 of depth, 15" absolute, 14" unsupported in 3 cm.
    15" on a 39" top is 38%, which is the figure plan/assemblies.py records.
    """
    import dataclasses

    from typehaus.checks.advisory.countertops import _grade
    from typehaus.findings import Result

    one_slab = dataclasses.replace(
        countertops["CT-M-KIT-PENINSULA"], depth_m=39.0 / M_TO_IN,
        unsupported_overhang_m=15.0 / M_TO_IN, support="none")
    finding = _grade(one_slab)
    assert finding.result is Result.FAIL
    assert "38%" in finding.message
    # Advisory, not code: WARN severity keeps it out of permit.py's ERROR-keyed gate while
    # `haus check` still reports it as a failure.
    assert finding.severity.name == "WARN"
    # Support is what buys it back, and it is a stated fact rather than an inferred one.
    assert _grade(dataclasses.replace(one_slab, support="steel-plate")).result is Result.PASS


def test_the_house_as_built_is_inside_every_published_limit(catlin_model_ro):
    from _helpers import check_context

    from typehaus.checks.advisory.countertops import countertop_overhang
    from typehaus.findings import Result

    findings = countertop_overhang(check_context(model=catlin_model_ro))
    assert findings and all(f.result is Result.PASS for f in findings)
    # The seating knee is past the 14" unsupported cap, so it passes only on its brackets.
    peninsula = next(f for f in findings if "CT-M-KIT-PENINSULA" in f.element_tags)
    assert "carried on brackets" in peninsula.message


def test_a_bank_on_a_fitted_bookcase_bills_the_boards_its_spec_draws(catlin_plan,
                                                                    catlin_model_ro):
    """The shelf bank is the takeoff and the spec is the geometry; they must be one case.

    Per bay: clear width, board count, and the height the boards divide (the bay less any
    closed base). Depth comes off the spec. Thickness is not compared: SB-A-STUDY mills
    6/4 stock while its spec draws 1-1/2" boards.
    """
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    hosts = {o.tag: o.type_ref for o in catlin_model_ro.canvas_objects}
    checked = []
    for bank in catlin_model_ro.shelf_banks:
        spec = getattr(types.get(hosts.get(bank.host) or ""), "built_in_bookcase", None)
        if spec is None:
            continue
        checked.append(bank.tag)
        assert bank.depth_m == pytest.approx(spec.shelf_depth.meters), bank.tag
        assert len(bank.shelves) == len(spec.bays), bank.tag
        for shelf, bay in zip(bank.shelves, spec.bays, strict=True):
            assert shelf.width_m == pytest.approx(bay.clear_width.meters), bank.tag
            assert shelf.count == bay.horizontal_board_count, bank.tag
            assert shelf.clear_height_m == pytest.approx(
                bay.height.meters - bay.closed_base_height.meters), bank.tag
    assert {"SB-A-STUDY", "SB-S-BATH1"} <= set(checked)


def test_a_cantilever_length_past_the_slab_is_refused(catlin_plan, catlin_model_ro):
    from typehaus.quantities import inch
    from typehaus.resolve.countertops import _placeable_sizes, _slab

    el = catlin_plan.by_tag("CT-M-KIT-PENINSULA")
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    run = [objects[tag] for tag in el.hosts]
    sizes = _placeable_sizes(catlin_plan)
    record, findings = _slab(el, run, "main", sizes)
    assert record is not None and not findings
    record, findings = _slab(el.model_copy(update={"cantilever_length": inch(90)}), run,
                             "main", sizes)
    assert record is None and findings[0].check_id == "integrity.countertop_run"
