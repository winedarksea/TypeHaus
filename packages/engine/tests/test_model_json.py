"""WP5 — model.json serialization contract: every member dict carries a pre-resolved
cross-section (the UI never parses ``profile`` strings itself)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.quantities import inch
from typehaus.server.model_json import model_to_dict
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



@pytest.fixture(scope="module")
def catlin_payload():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model_to_dict(model)


@pytest.fixture(scope="module")
def catlin_provenance_payload():
    result = load_plan(CATLIN_DIR)
    model, _findings = resolve(result.plan)
    return model_to_dict(model, provenance=result.provenance)


def _all_members(payload):
    for wall in payload["walls"]:
        yield from wall["members"]
    for roof in payload["roofs"]:
        yield from roof["members"]
    for floor in payload["floors"]:
        yield from floor["members"]
    for stair in payload["stairs"]:
        yield from stair["members"]


def test_every_member_carries_shape_width_depth(catlin_payload):
    members = list(_all_members(catlin_payload))
    assert members
    for member in members:
        assert member["shape"] in ("rect", "i_joist")
        assert member["width_m"] > 0
        assert member["depth_m"] > 0


def test_member_key_is_unique_within_its_parent(catlin_payload):
    """``<parent uid>/<member key>`` is the per-member identity the 3D panel picks with.

    Per-stud selection resolves an InstancedMesh instanceId back to a member; the id it
    stores must survive a rebuild, so it has to be the engine's own semantic child key
    (``stud-007``, ``plate-bottom``) and not a draw-call index. That only works if the key
    is unique inside its parent — assert it for every framed parent in the house.
    """
    parents = [
        *((w["uid"], w["members"]) for w in catlin_payload["walls"]),
        *((r["uid"], r["members"]) for r in catlin_payload["roofs"]),
        *((f["uid"], f["members"]) for f in catlin_payload["floors"]),
        *((s["uid"], s["members"]) for s in catlin_payload["stairs"]),
    ]
    assert parents
    seen = set()
    for uid, members in parents:
        keys = [m["key"] for m in members]
        assert all(keys), f"{uid} has a member with an empty key"
        assert len(set(keys)) == len(keys), f"{uid} repeats a member key"
        seen.update(f"{uid}/{key}" for key in keys)
    assert len(seen) == sum(len(members) for _, members in parents)


def test_every_member_carries_its_resolved_length(catlin_payload):
    """The inspector reports a picked stud's length from ``length_m``, not from p0/p1: a
    raked rafter's plan run is shorter than the stick, and a vertical stud has no run at all.
    """
    members = list(_all_members(catlin_payload))
    assert members
    assert all(member["length_m"] > 0 for member in members)


def test_skin_members_carry_a_material_and_lumber_does_not(catlin_payload):
    """The viewer colours a member by material when it has one, by category otherwise.

    Without the material the wall->roof closure and the roof-edge band fall through to the
    grey category fallback, which is what made the garage gable read as unwanted fill and
    left the house's standing seam stopping short of the roof's.
    """
    members = list(_all_members(catlin_payload))
    assert all("material" in member for member in members)
    house = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    # The house edge is a continuous standing-seam wrap (flush edge, one skin wall→roof):
    # the drip-edge band gave way to a corner trim piece. Since 2026-08-01 that piece is
    # ordered in RF-HOUSE's own `edge_trim_material` rather than the roofing's stock — the
    # charcoal accent coil that makes a zero-overhang rake legible. What matters here is
    # unchanged: it names *a* material, so neither renderer falls back to category grey.
    trims = [m for m in house["members"] if "-corner-trim-" in m["key"]]
    assert trims and all(m["material"] == "metal-dark-exterior" for m in trims)
    # The ridge cap is part of the same outline, so it follows the same coil — while the
    # garage, which authors no trim material, keeps its cap in the roofing's own stock.
    house_cap = [m for m in house["members"] if m["category"] == "ridge_cap"]
    assert house_cap and all(m["material"] == "metal-dark-exterior" for m in house_cap)
    garage = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-GARAGE")
    gable = [m for m in garage["members"]
             if "W-G-E-closure-" in m["key"] and m["category"] == "cladding"]
    assert gable and all(m["material"] == "standing-seam" for m in gable)
    garage_cap = [m for m in garage["members"] if m["category"] == "ridge_cap"]
    assert garage_cap and all(m["material"] == "standing-seam" for m in garage_cap)
    studs = [m for m in house["members"] if m["category"] == "rafter"]
    assert studs and all(m["material"] is None for m in studs)


def test_construction_returns_serialize_with_their_overlay_metadata(catlin_payload):
    """ConstructionRule returns reach the browser as their own records, not as solids.

    The solid mirror used to be the only path to model.json, and it carried none of the
    lap / sealant / flashing / returning-layer data the Inspector wants. Dropping it (the
    prisms were mis-placed gray fins in 3D) means these records have to be serialized.
    """
    returns = catlin_payload["construction_returns"]
    assert returns
    assert not [s for s in catlin_payload["solids"] if s["category"].startswith("return:")]
    uids = [r["uid"] for r in returns]
    assert uids == sorted(uids)
    for record in returns:
        assert record["material_ref"]
        assert record["tag"].startswith("CR-")
        assert len(record["outline"]) >= 3
        assert record["z1_m"] > record["z0_m"]
        assert record["length_m"] > 0.0
        assert record["element_tags"]


def test_second_floor_joists_are_i_joists(catlin_payload):
    floor = next(f for f in catlin_payload["floors"] if f["tag"] == "FS-SECOND")
    joists = [m for m in floor["members"] if m["category"] == "joist"]
    assert joists
    assert all(m["shape"] == "i_joist" for m in joists)
    assert all(m["flange_width_m"] is not None for m in joists)


def test_stud_carries_orient(catlin_payload):
    wall = next(w for w in catlin_payload["walls"] if w["tag"] == "W-M-S1")
    studs = [m for m in wall["members"] if m["category"] == "stud"]
    assert studs
    assert all(m["orient"] is not None and len(m["orient"]) == 2 for m in studs)


def test_roofs_carry_bearing_datum_and_layer_edge_setbacks(catlin_payload):
    """model.json contract: every roof serializes ``bearing_z_m`` and
    ``layer_edge_setbacks``; the rafter-framed house roof's deck plane rides ~0.2551 m
    above the plate (11.875" I-joist less the 5.5" 2x6 seat drop at 4:12) and its setbacks step monotonically deck >= foam >= batten >= metal."""
    from typehaus.quantities import inch

    for roof in catlin_payload["roofs"]:
        assert "bearing_z_m" in roof
        assert "layer_edge_setbacks" in roof
    house = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    assert house["eave_z_m"] - house["bearing_z_m"] == pytest.approx(
        inch(11.875 - 5.5 / 3.0).meters)
    entries = {entry["layer"]: entry for entry in house["layer_edge_setbacks"]}
    assert entries
    for edge in ("west", "east", "south", "north"):
        assert (entries["deck"][edge] >= entries["polyiso"][edge]
                >= entries["batten-gap"][edge] >= entries["roofing"][edge])
    garage = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-GARAGE")
    assert garage["layer_edge_setbacks"] == []  # truss roof deferred


def test_ridge_beam_member_carries_multi_ply_width(catlin_payload):
    roof = next(r for r in catlin_payload["roofs"] if r["tag"] == "RF-HOUSE")
    beams = [m for m in roof["members"] if m["category"] == "ridge_beam"]
    assert len(beams) == 1
    assert beams[0]["plies"] == 3
    assert beams[0]["shape"] == "rect"


def test_opening_kind_serializes_all_interchange_categories(catlin_model):
    model = deepcopy(catlin_model)
    source = model.openings[0]
    model.openings[0] = replace(source, kind="rough_opening", is_door=False, type_ref=None)

    payload = model_to_dict(model)
    kinds = {opening["kind"] for opening in payload["openings"]}
    assert {"door", "window", "rough_opening"} <= kinds
    rough = next(opening for opening in payload["openings"] if opening["kind"] == "rough_opening")
    assert rough["is_door"] is False


def test_openings_serialize_swing_and_framing_overlays(catlin_payload):
    door = next(opening for opening in catlin_payload["openings"] if opening["is_door"])
    assert len(door["swing_clearance"]) == 10
    assert len(door["framing_bumper"]) == 4


def test_sunken_garden_arch_openings_serialize_their_rise(catlin_payload):
    arches = [opening for opening in catlin_payload["openings"]
              if opening["tag"].startswith("AO-ARCH-")]
    assert len(arches) == 2
    assert all(opening["arch_rise_m"] == pytest.approx(1.2192) for opening in arches)


def test_site_context_serializes_grade_parcel_and_spot_elevations(catlin_payload):
    site = catlin_payload["site"]
    assert {"grade_m", "parcel", "spot_elevations"} <= site.keys()
    assert site["grade_m"] is None or isinstance(site["grade_m"], float)
    assert isinstance(site["parcel"], list)
    assert all(set(spot) == {"position", "elevation_m"}
               for spot in site["spot_elevations"])


def test_model_json_serializes_finished_height_above_average_grade(catlin_payload):
    summary = catlin_payload["building_height_summary"]
    assert summary["average_ground_grade_m"] == pytest.approx(0.0)
    assert {row["roof_tag"] for row in summary["roofs"]} == {"RF-HOUSE", "RF-GARAGE"}
    assert all(row["peak_above_grade_m"] > row["midpoint_above_grade_m"] > 0
               for row in summary["roofs"])


def test_project_serializes_the_active_clearance_code_profile(catlin_payload):
    assert "active_code_profile" in catlin_payload["project"]


def test_catalog_materials_carry_both_vapour_fields_and_their_source(catlin_payload):
    """Both permeance fields must cross the UI boundary, and they are not interchangeable.

    ``perm_rating`` is perm-*inch* (scales with depth); ``vapor_permeance_perms`` is the
    finished product's ASTM E96 permeance and wins outright. A consumer given only the first
    would divide a whole-sheet rating by a thickness and invent a number nobody measured —
    which is precisely what ``Material.vapor_permeance_at`` refuses to do. Catlin authors
    whole-sheet perms for zip-r, the air barrier, and standing seam, so a regression that
    drops the field is visible here rather than as a silently wrong lens reading.
    """
    materials = {m["tag"]: m for m in catlin_payload["catalog"]["materials"]}
    assert materials, "the catalog must publish its materials"
    for material in materials.values():
        assert {"perm_rating", "vapor_permeance_perms", "source"} <= material.keys()

    sheet_rated = {tag: m["vapor_permeance_perms"] for tag, m in materials.items()
                   if m["vapor_permeance_perms"] is not None}
    assert sheet_rated, "sheet goods author a whole-sheet permeance"
    # 0.0 is a sourced vapour barrier, not missing data — it must survive as a float.
    assert all(isinstance(value, float) for value in sheet_rated.values())


def test_provenance_carries_the_editable_flag(catlin_provenance_payload):
    """model.json contract: every provenance record says whether writeback can target it.
    Editable-scanned elements ship editable=True; runtime-captured (params-generated)
    ones ship editable=False with the generating file — the UI's read-only badge."""
    walls = {w["tag"]: w for w in catlin_provenance_payload["walls"]}
    authored = walls["W-B-S1"]["provenance"]  # plan/storeys/basement.py, editable
    assert authored is not None and authored["editable"] is True
    generated = walls["W-SG-S"]["provenance"]  # params/sunken_garden.py, captured
    assert generated is not None
    assert generated["editable"] is False
    assert generated["file"] == "params/sunken_garden.py"
    assert generated["line"] > 0


def test_catalog_assembly_editability_requires_editable_provenance(catlin_provenance_payload):
    assemblies = catlin_provenance_payload["catalog"]["assemblies"]
    assert assemblies
    for assembly in assemblies:
        prov = assembly["provenance"]
        assert assembly["editable"] == bool(prov and prov["editable"])
    assert any(a["editable"] for a in assemblies)


def test_variant_catalog_defaults_to_an_empty_list(catlin_payload):
    """Absent-catalog story: a house with no variants.toml still serializes ``variants``
    (as []), so the UI's variant picker reads one stable key instead of probing for it."""
    assert catlin_payload["variants"] == []


def test_variant_catalog_threads_declared_variants_into_the_payload(catlin_model, starter_dir):
    import json

    from typehaus.server.model_json import load_variant_catalog

    specs = load_variant_catalog(starter_dir)
    assert specs, "the starter house declares variants"
    payload = model_to_dict(catlin_model, variants=specs)
    names = [entry["name"] for entry in payload["variants"]]
    assert names == ["as-authored", "2x4-ci", "thicker-zip-r"]
    swap = next(entry for entry in payload["variants"] if entry["name"] == "2x4-ci")
    assert swap["assembly_swaps"] == {"HOUSE_WALL_2X6_WITH_ZIPR": "HOUSE_WALL_2X4_WITH_CI"}
    # The payload must stay JSON-serializable end to end (specs are dataclasses upstream).
    json.dumps(payload["variants"])


def test_load_variant_catalog_degrades_gracefully(tmp_path):
    """Neither an absent nor a malformed variants.toml may break model.json emission —
    ``haus variants list`` is where a broken catalog reports loudly."""
    from typehaus.server.model_json import load_variant_catalog

    assert load_variant_catalog(None) == ()
    assert load_variant_catalog(tmp_path) == ()  # no variants.toml
    (tmp_path / "variants.toml").write_text("[[variant]]\n# no name -> loader error\n")
    assert load_variant_catalog(tmp_path) == ()


def test_stairs_payload_carries_landing_depth(catlin_payload):
    stairs = {stair["tag"]: stair for stair in catlin_payload["stairs"]}
    assert "landing_depth_m" in stairs["ST-B2M"]
    # ST-B2M authors the IRC R311.7.6 minimum landing_depth=ft(3) — the payload carries
    # the *authored* value, which the resolver then floors at the flight width. The winder
    # stair authors none.
    assert stairs["ST-B2M"]["landing_depth_m"] == pytest.approx(0.9144)  # 3'-0"
    assert stairs["ST-S2A"]["landing_depth_m"] is None
    for stair in stairs.values():
        assert stair["tread_depth_m"] == pytest.approx(inch(11).meters)
        assert stair["going_depth_m"] == pytest.approx(inch(10).meters)
        assert stair["nosing_depth_m"] == pytest.approx(inch(1).meters)


def test_every_payload_key_has_a_ui_type(catlin_payload):
    """The wire contract's cheap enforcement (→ Phase 5): every top-level key
    ``model_to_dict`` emits must have a matching field on ``ui/src/model/types.ts``'s
    ``Model`` interface. This is the whole mechanism keeping the two in lockstep — it used
    to be a comment ("keep this file in lockstep with model_to_dict") that had already
    silently dropped three whole blocks (alarms, floor_heat, variants) by the time anyone
    checked. Line-scraping the field names out of the TS source is crude, but it needs no
    TS toolchain and it catches exactly the failure mode that happened: a key present in
    one language and absent in the other.
    """
    types_ts = (
        Path(__file__).resolve().parents[3] / "ui" / "src" / "model" / "types.ts"
    ).read_text()
    start = types_ts.index("export interface Model {")
    end = types_ts.index("\n}", start)
    body = types_ts[start:end]
    ts_fields = {
        line.split(":", 1)[0].strip().rstrip("?")
        for line in body.splitlines()
        if ":" in line and not line.strip().startswith("//")
    }
    missing = sorted(set(catlin_payload) - ts_fields)
    assert not missing, (
        f"model_to_dict emits {missing} but ui/src/model/types.ts's Model interface "
        "has no matching field(s) — the UI cannot see this data"
    )
