"""The IFC a reviewing engineer gets: sections, engineering records and a bar schedule.

``haus build``'s IFC is for a plan reviewer who wants geometry. ``haus handoff``'s is for a
PE who wants to check the calculation package against the model, and these pin the three
things that make that possible.

The assertion doing the most work is
:func:`test_the_bar_schedule_agrees_with_the_bill_of_materials`. Two views of the same steel
computed by two code paths would drift, and the drift would be invisible: the IFC would look
complete and quietly disagree with what gets ordered. Both go through the same two length
helpers, and this is what says so.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN

import ifcopenshell
import ifcopenshell.util.element as ue

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def enriched(tmp_path_factory):
    """catlin emitted the way ``haus handoff`` emits it, once."""
    from typehaus.checks import build_context, run_checks
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    loaded = load_plan(CATLIN)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    model, _ = resolve(loaded.plan)
    ctx, _ = build_context(loaded.plan, CATLIN)
    run_checks(ctx)
    out = tmp_path_factory.mktemp("enriched") / "model.ifc"
    emit_ifc(model, out, lod="framed", house_dir=CATLIN,
             engineering=ctx.engineering, register=ctx.engineering_register)
    return ifcopenshell.open(str(out)), model, ctx


# --- section profiles --------------------------------------------------------------------

def test_members_carry_a_material_profile_set_matching_their_own_section(enriched):
    """The section a reviewer reads has to be the section the geometry was built from."""
    from typehaus.resolve.framing.profiles import cross_section

    f, _model, _ctx = enriched
    sets = f.by_type("IfcMaterialProfileSet")
    assert len(sets) > 20, "almost nothing got a section"
    for profile_set in sets:
        material_profile = profile_set.MaterialProfiles[0]
        shape = material_profile.Profile
        section = cross_section(profile_set.Name)
        if shape.is_a("IfcRectangleProfileDef"):
            assert shape.XDim == pytest.approx(section.width_m, abs=1e-9)
            assert shape.YDim == pytest.approx(section.depth_m, abs=1e-9)
        else:
            assert shape.is_a("IfcCircleProfileDef")
            assert shape.Radius == pytest.approx(section.width_m / 2.0, abs=1e-9)


def test_a_section_set_is_shared_not_duplicated_per_member(enriched):
    """~15,000 members over a few dozen sections. One profile set each would be 75,000
    entities for no information a reader does not get from the shared one."""
    f, _model, _ctx = enriched
    relations = [r for r in f.by_type("IfcRelAssociatesMaterial")
                 if r.RelatingMaterial.is_a("IfcMaterialProfileSet")]
    members = sum(len(r.RelatedObjects) for r in relations)
    assert members > 1000
    assert len(relations) == len({r.RelatingMaterial for r in relations})
    assert members > 20 * len(relations), "sections are not being shared"


def test_no_species_or_grade_is_invented_for_sawn_lumber(enriched):
    """This engine authors no species anywhere. A grade in the IFC would be a claim."""
    from typehaus.emit.ifc.profiles import material_name

    assert material_name("2x6") == "sawn lumber"
    assert "SPF" not in material_name("2x10")
    assert material_name('2-ply 14" LVL') == "laminated veneer lumber"
    f, _model, _ctx = enriched
    names = {m.Name for m in f.by_type("IfcMaterial")}
    assert not {n for n in names if "SPF" in n or "#2" in n}


# --- the engineering records ---------------------------------------------------------------

def test_a_graded_column_carries_its_record_and_the_live_fingerprint(enriched):
    from typehaus.engineering.fingerprint import fingerprint

    f, _model, ctx = enriched
    column = next(e for e in f.by_type("IfcColumn") if e.Name == "PT-SG-COL")
    pset = ue.get_psets(column)["Pset_TH_Engineering_deck_post"]
    record = ctx.engineering["deck_post/PT-SG-COL"]
    assert pset["ItemId"] == "deck_post/PT-SG-COL"
    assert pset["Status"] == record.status.value
    assert pset["GoverningLimitState"] == record.governing.name
    assert pset["DemandCapacityRatio"] == pytest.approx(record.governing.ratio)
    assert pset["Citation"] == record.governing.citation
    # The fingerprint is what a seal would be pinned to. Wrong here and the model tells a
    # reviewer to pin something the CLI would not.
    assert pset["Fingerprint"] == fingerprint(record)
    assert pset["Seal"] == "unsealed"


def test_a_deferred_item_says_it_has_nothing_to_fingerprint(enriched):
    f, _model, _ctx = enriched
    walls = [e for e in f.by_type("IfcWall") if e.Name == "W-SG-W1"]
    assert walls
    pset = ue.get_psets(walls[0]).get("Pset_TH_Engineering_column_support")
    assert pset is not None
    assert pset["Fingerprint"].startswith("none")


def test_the_ordinary_build_carries_none_of_this(tmp_path):
    """`haus build`'s IFC goes to a plan reviewer who wants geometry, not calculations."""
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    loaded = load_plan(CATLIN)
    model, _ = resolve(loaded.plan)
    plain = ifcopenshell.open(str(emit_ifc(model, tmp_path / "plain.ifc", lod="framed")))
    assert not [p for p in plain.by_type("IfcPropertySet")
                if p.Name.startswith("Pset_TH_Engineering_")]


# --- the bar schedule ----------------------------------------------------------------------

def test_the_bar_schedule_agrees_with_the_bill_of_materials(enriched):
    """Two views of one steel, through the same two length helpers. Drift here is invisible."""
    from typehaus.takeoff.reinforcement import reinforcement_takeoff

    f, model, _ctx = enriched
    bars = [b for b in f.by_type("IfcReinforcingBar")
            if "Pset_TH_Reinforcement" in ue.get_psets(b)]
    assert bars, "no bar schedule at all"
    in_model = sum(ue.get_psets(b)["Pset_TH_Reinforcement"]["TotalLengthFt"] for b in bars)
    in_bom = sum(float(row["length_ft"]) for row in reinforcement_takeoff(model))
    # The BOM rounds each aggregated row to a tenth of a foot; that rounding is the only
    # difference the two may have.
    assert in_model == pytest.approx(in_bom, abs=1.0)


def test_each_bar_hangs_under_the_pour_it_is_in(enriched):
    """A bar aggregated to the wrong host is worse than a missing one."""
    f, _model, _ctx = enriched
    hosted = {}
    for relation in f.by_type("IfcRelAggregates"):
        for related in relation.RelatedObjects:
            if related.is_a("IfcReinforcingBar"):
                hosted[related] = relation.RelatingObject
    bars = [b for b in f.by_type("IfcReinforcingBar")
            if "Pset_TH_Reinforcement" in ue.get_psets(b)]
    for bar in bars:
        host = hosted.get(bar)
        assert host is not None, bar.Name
        assert host.Name == ue.get_psets(bar)["Pset_TH_Reinforcement"]["Host"]


def test_a_bar_carries_its_size_in_metres_not_inches(enriched):
    """The project is metre-unit. A #5 written as 0.625 would be a two-foot-diameter bar."""
    f, _model, _ctx = enriched
    bar = next(b for b in f.by_type("IfcReinforcingBar")
               if "Pset_TH_Reinforcement" in ue.get_psets(b) and "#5" in (b.Name or ""))
    assert bar.NominalDiameter == pytest.approx(0.625 * 0.0254, abs=1e-9)
    assert bar.CrossSectionArea == pytest.approx(0.31 * 0.0254 ** 2, abs=1e-12)


def test_the_bars_have_no_body_representation(enriched):
    """Drawing a cage would invent hooks, laps and cover the model does not carry — and a
    drawn cage read as a placement drawing is worse than none, because it looks like one."""
    f, _model, _ctx = enriched
    bars = [b for b in f.by_type("IfcReinforcingBar")
            if "Pset_TH_Reinforcement" in ue.get_psets(b)]
    assert all(bar.Representation is None for bar in bars)
