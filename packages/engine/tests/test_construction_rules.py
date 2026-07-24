"""ConstructionRule application pass (#45): authored returns -> geometry + BOM + overlay.

The four Catlin returns (CR-CONC-TO-FRAMED-SILL, CR-SAUNA-LINER-RETURN,
CR-FOUNDATION-FOAM-RETURN, CR-PORCH-MASONRY-RETURN) are authored on
``PlanModel.construction_rules`` and were, before this pass, consumed by nothing. These
tests assert each now emits a resolved return, a render solid, and a take-off row, and
carries the overlay metadata a detail recipe binds to — without touching framing members.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.takeoff import construction_returns_takeoff

_RULE_TAGS = {
    "CR-CONC-TO-FRAMED-SILL",
    "CR-SAUNA-LINER-RETURN",
    "CR-FOUNDATION-FOAM-RETURN",
    "CR-PORCH-MASONRY-RETURN",
}


def test_all_authored_returns_are_emitted(catlin_model) -> None:
    """Every authored ConstructionRule produces at least one resolved return."""
    emitted = {ret.tag for ret in catlin_model.construction_returns}
    assert _RULE_TAGS <= emitted, _RULE_TAGS - emitted


def test_returns_emit_valid_render_geometry(catlin_model) -> None:
    """Each return has a real (positive-area, valid) plan polygon and a z extent, and is
    mirrored into ``model.solids`` so section/3D/IFC/model.json render it."""
    solid_uids = {solid.uid for solid in catlin_model.solids}
    for ret in catlin_model.construction_returns:
        poly = Polygon(ret.outline)
        assert poly.is_valid and poly.area > 0.0, ret.tag
        assert ret.z1_m > ret.z0_m, ret.tag
        assert ret.uid in solid_uids, ret.tag  # renders via the shared solid path


def test_returns_do_not_pose_as_structural_solids(catlin_model) -> None:
    """Returns must never be emitted as column/beam solids — those are the only solids the
    member-interference check inspects, so a return must not create a false clash."""
    return_uids = {ret.uid for ret in catlin_model.construction_returns}
    for solid in catlin_model.solids:
        if solid.uid in return_uids:
            assert solid.category not in ("column", "beam")
            assert solid.category.startswith("return:")


def test_returns_contribute_takeoff_rows(catlin_model) -> None:
    """Each return's take-off category bills a BOM row with a positive count and length."""
    rows = construction_returns_takeoff(catlin_model)
    categories = {row["category"] for row in rows}
    assert {"pt-sill-plate", "sauna-liner-return", "foundation-foam-return",
            "masonry-corner-return"} <= categories, categories
    for row in rows:
        assert row["count"] >= 1
        assert row["length_ft"] > 0.0
    # Rows reconcile 1:1 with the resolved returns.
    assert sum(row["count"] for row in rows) == len(catlin_model.construction_returns)


def test_sill_plate_is_pt_bearing_and_carries_overlay_metadata(catlin_model) -> None:
    """The concrete-to-framed sill is a PT bearing plate landing on the concrete top, with
    the lap/sealant/element-tag data an overlay recipe needs."""
    sills = [r for r in catlin_model.construction_returns
             if r.tag == "CR-CONC-TO-FRAMED-SILL"]
    assert sills
    for sill in sills:
        assert sill.kind == "bearing_plate"
        assert sill.material_ref == "spf"
        assert sill.lap_m > 0.0
        assert sill.sealant is not None
        assert len(sill.element_tags) >= 2  # the concrete wall + the framed wall
        assert sill.condition_key and sill.condition_key.startswith("wall_foundation:")


def test_sauna_liner_return_declares_air_vapor_continuity(catlin_model) -> None:
    """The sauna hot-side liner return carries the vapour/air continuity claim (it is the
    control layer that must wrap onto the concrete, not merely butt)."""
    liners = [r for r in catlin_model.construction_returns
              if r.tag == "CR-SAUNA-LINER-RETURN"]
    assert liners
    assert all(r.air_vapor_continuity and r.returning_layer == "foil-polyiso"
               for r in liners)


def test_foundation_foam_return_is_thermal(catlin_model) -> None:
    """The exterior foundation foam return maintains thermal continuity around the corner."""
    foam = [r for r in catlin_model.construction_returns
            if r.tag == "CR-FOUNDATION-FOAM-RETURN"]
    assert foam
    assert all(r.thermal_continuity for r in foam)
    assert all(r.material_ref in ("xps", "icf-eps") for r in foam)
