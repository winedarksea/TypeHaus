"""Framing bill-of-materials takeoff — grouped by size AND type, bucketed by length."""

from __future__ import annotations

from typehaus.takeoff import (
    _board_feet_per_ft,
    _order_length_ft,
    bill_of_materials,
    framing_bom_by_size,
    framing_takeoff,
    structural_solids_takeoff,
)

from _helpers import frames_structure


def test_order_length_rounds_up_to_stock() -> None:
    assert _order_length_ft(7.5) == 8
    assert _order_length_ft(8.0) == 8
    assert _order_length_ft(8.1) == 10
    assert _order_length_ft(15.9) == 16
    assert _order_length_ft(19.5) == 20
    # Past the longest stock length, round up to the next even foot.
    assert _order_length_ft(21.0) == 22
    assert _order_length_ft(36.0) == 36


def test_board_feet_parses_dimensional_and_builtup_profiles() -> None:
    assert _board_feet_per_ft("2x6") == 1.0            # 2*6/12
    assert _board_feet_per_ft("2-2x8") == 8.0 / 3.0    # 2 plies * 2*8/12
    assert _board_feet_per_ft("11.875 I-joist") is None  # engineered, not dimensional


def test_framing_takeoff_reconciles_and_groups(catlin_model) -> None:
    members = catlin_model.all_members()
    assert members  # the catlin model frames thousands of members

    rows = framing_takeoff(catlin_model)
    # Every (profile, category, material) triple is present exactly once and total pieces
    # reconcile 1:1. Material is part of the key because a KDAT 2x4 outrigger and an SPF 2x4
    # stud are the same profile and not the same purchase.
    keys = [(row["profile"], row["category"], row["material"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert sum(int(row["pieces"]) for row in rows) == len(members)

    for row in rows:
        # Sticks, not pieces: short cuts nest several to a stock length, so a group's bucket
        # count is at most its piece count and is only equal when nothing nested.
        sticks = sum(bucket["count"] for bucket in row["stock"])
        assert 0 < sticks <= row["pieces"]
        assert row["order_length_ft"] >= row["cut_length_ft"]  # ordered >= cut

    # Nesting is what keeps a short-piece row honest: the catlin truss's ~4,150 three-and-a-
    # half-inch girt blocks are about 1,212 lineal feet of 2x4 between them, and must not
    # order one 8-ft stick apiece.
    blocks = [row for row in rows if row["category"] == "truss_block"]
    assert blocks
    for row in blocks:
        assert row["order_length_ft"] < 1.5 * row["cut_length_ft"]

    # Head cripples over a door are a short-cut family too — an 18" stud above a garage
    # overhead-door header is ~1.5 ft of 2x6 — so the same nesting has to reach them. This
    # pins the BOM path for the family rather than leaving it incidental to the sweep.
    cripples = next(row for row in rows
                    if row["profile"] == "2x6" and row["category"] == "cripple")
    assert cripples["order_length_ft"] < 2 * cripples["cut_length_ft"]

    # A known dimensional profile carries a board-foot rollup; every stud is a real size.
    studs = [row for row in rows if row["category"] == "stud"]
    assert studs and all(row["board_feet"] for row in studs)


def test_framing_by_size_rolls_up_types(catlin_model) -> None:
    rows = framing_takeoff(catlin_model)
    by_size = framing_bom_by_size(catlin_model)

    # One row per distinct (profile, material), and the piece totals match the detailed takeoff.
    assert ({(row["profile"], row["material"]) for row in by_size}
            == {(row["profile"], row["material"]) for row in rows})
    assert sum(int(row["pieces"]) for row in by_size) == sum(
        int(row["pieces"]) for row in rows
    )
    # 2x4 is used by several member types in the catlin frame.
    two_by_four = next(row for row in by_size if row["profile"] == "2x4")
    assert len(set(two_by_four["types"])) > 1


def test_structural_solids_account_for_every_resolved_solid(catlin_model) -> None:
    """The member cut list cannot see concrete or standalone structure; this row set can."""
    rows = structural_solids_takeoff(catlin_model)
    assert sum(int(row["count"]) for row in rows) == len(catlin_model.solids)
    assert {tag for row in rows for tag in row["tags"]} == {
        solid.tag for solid in catlin_model.solids}
    # Concrete is ordered by the yard, so the volume rollup has to be real.
    footings = next(row for row in rows if row["category"] == "footing")
    assert footings["volume_cubic_yards"] > 0


def test_bill_of_materials_carries_every_section(catlin_model) -> None:
    bom = bill_of_materials(catlin_model)
    assert set(bom) == {"framing", "framing_by_size", "structural_solids",
                        # The sill seal under the bearing plates (2026-08-24), by the lineal
                        # foot and by product — its own section because
                        # ``construction_returns`` reconciles 1:1 with the resolved returns
                        # (→ ``takeoff/anchors.sill_gasket_rows``).
                        "construction_returns", "sill_gaskets",
                        "sheet_goods", "glazing_panels",
                        "glazing_trim", "hardware", "placeables", "floor_heat",
                        "electrical_devices", "panel_schedule", "service_load",
                        "conduit", "conductors", "solar",
                        # The list view of ``solar["by_product"]`` that
                        # [solar_modules] prices (2026-08-27) — every price plan
                        # reads a list and ``solar`` is a dict of summaries.
                        "solar_modules", "backup_power",
                        "luminaire_schedule", "lighting_controls", "light_runs",
                        "light_run_materials", "lighting_load",
                        # Structured cabling (2026-08-02).
                        "data_devices", "data_raceways", "poe_budget",
                        # The 2026-07-25 sweep: resolved-but-unbilled families.
                        "floor_finishes", "envelope_layers", "openings", "stair_finish",
                        # Species wood rollup (2026-08-02): sauna liner, panelings,
                        # timber posts and species floors in sf/bf.
                        "wood_surfaces",
                        "footing_bedding", "pipe_runs", "pipe_fittings", "ducts", "sleeves",
                        # Railings got their own takeoff category in 33bac47; this list and
                        # the `haus takeoff` payload both missed it, so guard rail and cable
                        # infill were billed nowhere the CLI could see.
                        "railings",
                        # The rainscreen's base vent/insect closure — derived off the wall
                        # stack, so it is billed by the lineal foot rather than authored.
                        "bug_screens",
                        # Stormwater by the foot and the piece: gutter, leader, trench,
                        # soakaway. Billed only as cubic feet of aluminium and stone before.
                        "drainage",
                        # The supply system's protection budget and the hot-line
                        # insulation, neither of which anything could see before
                        # `PipeAccessory` and `PipeRun.insulation` existed.
                        "plumbing_specialties", "install_parts", "pipe_insulation",
                        # Duct elbows off the runs' own 3D polylines and duct wrap by the
                        # foot — neither visible until `DuctRun` gained elevations and an
                        # `insulation` field (the ERV pass).
                        "duct_fittings", "duct_insulation",
                        # The species-wood rollup (2026-08-02, hardwood pass).
                        "wood_surfaces",
                        # Edge trim by the lineal foot: the fascia/soffit/flashing family,
                        # authored runs and derived roof trim alike (→ takeoff/edge_trim.py).
                        "edge_trim",
                        # Monolithic wall structure (2026-08-03): a STRUCTURE layer that
                        # frames no members and is not a solid reached no row at all —
                        # 43 of catlin's 154 walls, ~131 cy (→ takeoff/wall_structure.py).
                        "wall_structure"}
    assert all(section for section in bom.values()), "no BOM section may come back empty"
    # The framing section still reconciles 1:1 with the resolved members.
    assert sum(int(row["pieces"]) for row in bom["framing"]) == len(catlin_model.all_members())


# Every collection on ``ResolvedModel`` is either billed by a BOM section or waived here with
# the reason it is not billable. This is the test that would have caught the drift the
# 2026-07-25 sweep cleaned up: eight families had been resolved for months and were reaching
# no order, and nothing said so because the section list only ever asserted its own contents.
#
# Adding a collection to ResolvedModel now forces a decision here — bill it, or say why not.
_BOM_WAIVED_COLLECTIONS: dict[str, str] = {
    "plan": "the authored source, not a resolved quantity",
    "junctions": "derived wall-meeting topology; the framing it implies bills as members",
    "conditions": "boundary-condition keys for transition matching — an index, not material",
    "stack_edges": "assembly-change edges the detail pipeline keys on; no quantity",
    "layout_lines": "the derived wall-line chains those edges are pairs of — a shared "
                    "origin for bands and stud layout, not an element and not material",
    "canvas_objects": "the normalized placeable view; billed as `placeables` off the same "
                      "records, and billing both would double every appliance",
    "timings": "resolve instrumentation",
    "_tag_index": "a derived lookup cache over the collections above, not a collection of "
                  "its own material — every element it points to is billed under its own "
                  "collection's entry",
    "braces": "diagonal braces are FramedMembers under `all_members()`, so `framing` "
              "already carries them piece for piece",
    "soffits": "the framing host beside the soffit's own ResolvedSolid: its ladder "
               "members are FramedMembers under `all_members()` (billed by `framing`) "
               "and the finished box bills as that solid under `structural_solids`, so "
               "billing the record too would order the same chase twice",
    "roofs": "same split as walls — `framing` for the sticks, `envelope_layers` and "
             "`sheet_goods` for the skin",
    "floors": "same split — joists in `framing`, subfloor and ceiling in `sheet_goods`",
    "stairs": "carriage in `framing`, walking surfaces in `stair_finish`",
    "light_runs": "billed as `light_runs` by the lineal foot (a dict, not a row list)",
    "solar_panels": "billed as `solar` (a dict summary of installed wattage)",
    "geometry": "the derived-geometry IR: a second view of collections already billed "
                "above (a stud is one FramedMember and one GPart), so billing it would "
                "double-count the whole house",
}

# collection name -> the BOM section(s) that bill it.
_BOM_COVERAGE: dict[str, tuple[str, ...]] = {
    # Walls bill by their parts. This was a *waiver* until 2026-08-03, and its text —
    # "`framing` for the studs, `envelope_layers` for the stack" — was the false claim the
    # missing-concrete bug lived inside: `envelope_layers` never billed STRUCTURE, so a
    # wall whose core is a pour or a masonry course reached no row at all.
    # `test_every_wall_layer_is_billed_or_waived` below is the assertion that says so.
    "walls": ("framing", "envelope_layers", "wall_structure"),
    "openings": ("openings",),
    "solids": ("structural_solids",),
    "construction_returns": ("construction_returns",),
    "floor_heat": ("floor_heat",),
    "rooms": ("floor_finishes",),
    "panelings": ("wood_surfaces",),
    "pipe_runs": ("pipe_runs", "pipe_fittings", "pipe_insulation"),
    "pipe_accessories": ("plumbing_specialties", "install_parts"),
    "sleeves": ("sleeves",),
    "ducts": ("ducts", "duct_fittings", "duct_insulation"),
    "conduits": ("conduit", "conductors"),
    "footing_beddings": ("footing_bedding",),
    # The paneling records (sauna liner, wainscot, tile splash) roll up by species/material.
    "panelings": ("wood_surfaces",),
    # The resolved layer stack per room; billed off the deck/roof/room fields it was
    # derived from (``sheet_goods``'s "ceiling" scope), not off this record directly.
    "ceilings": ("sheet_goods",),
}


def test_every_resolved_collection_is_billed_or_waived(catlin_model) -> None:
    """The coverage gate. A new ResolvedModel collection must be billed or explicitly
    waived — silence is what let plumbing, ducts, sleeves, beddings, openings, envelope
    layers, floor finishes and stair treads go unordered."""
    import dataclasses

    from typehaus.resolve.model import ResolvedModel

    collections = {f.name for f in dataclasses.fields(ResolvedModel)}
    classified = set(_BOM_COVERAGE) | set(_BOM_WAIVED_COLLECTIONS)
    assert collections <= classified, (
        f"unclassified ResolvedModel collection(s): {sorted(collections - classified)} — "
        "bill them in bom.py or waive them in _BOM_WAIVED_COLLECTIONS with a reason")
    # No stale entries either: a waiver for a collection that no longer exists is a lie the
    # next reader would believe.
    assert classified <= collections, (
        f"stale entr(ies): {sorted(classified - collections)}")

    bom = bill_of_materials(catlin_model)
    for collection, sections in sorted(_BOM_COVERAGE.items()):
        if not getattr(catlin_model, collection):
            continue  # nothing resolved on this fixture; the section is still wired
        for section in sections:
            assert bom.get(section), (
                f"{collection} is resolved on catlin but its BOM section "
                f"{section!r} is empty")


# The layer-level twin of the collection sweep above. "walls are billed by their parts" is
# only true if *every* part is billed, and nothing checked that: `envelope_layers` quietly
# excluded STRUCTURE, so 43 walls' worth of concrete and masonry reached no order for months
# while the collection-level gate stayed green. A layer function that is not billed must be
# named here with the reason — keyed by function, and the reason has to survive reading.
_WAIVED_LAYER_FUNCTIONS: dict[str, str] = {
    "airgap": "an air gap is nothing at all — a void between layers, with no material",
}

# FURRING used to live in the waiver above, with an apology attached: no wall framed
# strapping at all, so on a monolithic wall (W-B-CS, a `struct-1-plywood` liner band over
# concrete) it reached no BOM section whatsoever. `resolve/framing/furring.py` now frames
# every FURRING layer that carries a FramingSpec, so the waiver is gone and this is the
# assertion that replaces it — asserted below rather than waived, because "the framing cut
# list carries it" is exactly the kind of claim that was false for months while nobody
# could see it.


def test_every_wall_layer_is_billed_or_waived(catlin_model) -> None:
    """Every layer of every wall reaches a BOM section, or its function is waived above."""
    from typehaus.model.enums import LayerFunction
    from typehaus.takeoff.envelope import _BILLABLE, envelope_layer_takeoff
    from typehaus.takeoff.wall_structure import wall_structure_takeoff

    envelope = {(str(row["scope"]), str(row["function"]), str(row["material"]))
                for row in envelope_layer_takeoff(catlin_model)}
    monolithic = {tag for row in wall_structure_takeoff(catlin_model)
                  for tag in row["tags"]}
    billable = {function.value for function in _BILLABLE}

    for wall in catlin_model.walls:
        scope = "foundation wall" if wall.is_foundation else "wall"
        for layer in wall.layers:
            if getattr(layer, "is_cavity", False):
                assert (scope, "insulation (cavity)", layer.material_ref) in envelope, (
                    f"{wall.tag}: cavity layer {layer.material_ref} is billed nowhere")
                continue
            function = layer.function
            if function in billable:
                assert (scope, function, layer.material_ref) in envelope, (
                    f"{wall.tag}: {function} layer {layer.material_ref} is billed nowhere")
            elif function == LayerFunction.STRUCTURE.value:
                framed = frames_structure(wall)
                assert framed or wall.tag in monolithic, (
                    f"{wall.tag}: its {layer.material_ref} STRUCTURE layer frames no "
                    "members and is not in `wall_structure` — it is billed nowhere")
            elif function == LayerFunction.FURRING.value:
                # A FURRING layer bills as lineal-foot lumber in the framing cut list, and
                # only if *this* layer resolved members there — including on walls whose
                # structure is a pour and frames none. Keyed by layer name (the child_key
                # `resolve/framing/furring.py` mints) rather than by category alone, so a
                # second furring layer cannot ride on the first one's strapping.
                assert any(member.category == "strapping"
                           and member.child_key.startswith(f"strapping-{layer.name}-")
                           for member in wall.members), (
                    f"{wall.tag}: its {layer.material_ref} FURRING layer {layer.name!r} "
                    "frames no strapping — it is billed nowhere")
            else:
                assert function in _WAIVED_LAYER_FUNCTIONS, (
                    f"{wall.tag}: layer function {function!r} is neither billed nor waived "
                    "— bill it or add it to _WAIVED_LAYER_FUNCTIONS with the reason")


def test_the_cli_payload_forwards_every_bom_section(catlin_model) -> None:
    """`haus takeoff` builds its own payload from the BOM, and a section it forgets is
    invisible to the estimate and to `haus variants compare`. lighting_controls was dropped
    that way for the entire life of the lighting program."""
    import json
    from pathlib import Path

    from typer.testing import CliRunner

    from typehaus.cli.app import app

    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = CliRunner().invoke(app, ["takeoff", str(house), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    # `framing` is forwarded under two keys (the raw counter and `framing_bom`), so it is
    # the one section whose payload name differs from its BOM name.
    expected = set(bill_of_materials(catlin_model)) | {"framing_bom"}
    missing = expected - set(payload)
    assert not missing, f"`haus takeoff` drops: {sorted(missing)}"


def test_placeables_takeoff_reconciles_with_canvas_objects(catlin_model) -> None:
    """The engine twin of the UI BOM's placeablesSection: every free-placed or
    wall-attached product is counted, hosted openings are billed elsewhere, and the
    grouped counts reconcile 1:1 with ``model.canvas_objects``."""
    from typehaus.takeoff.placeables import placeables_takeoff

    rows = placeables_takeoff(catlin_model)
    assert rows, "the catlin house places furniture/appliances/fixtures"
    billable = [item for item in catlin_model.canvas_objects if item.domain != "opening"]
    assert sum(int(row["count"]) for row in rows) == len(billable)
    assert {tag for row in rows for tag in row["tags"]} == {item.tag for item in billable}
    assert all(row["domain"] != "opening" for row in rows)
    # Grouping key is (type, domain, storey) — each appears exactly once.
    keys = [(row["type"], row["domain"], row["storey"]) for row in rows]
    assert len(keys) == len(set(keys))


def test_floor_heat_rides_in_the_bom(catlin_model) -> None:
    """The radiant zones moved out of the CLI patch: bill_of_materials carries them."""
    bom = bill_of_materials(catlin_model)
    rows = {row["tag"]: row for row in bom["floor_heat"]}
    assert set(rows) == {zone.tag for zone in catlin_model.floor_heat}
    bath = rows["FH-M-BATH2"]
    zone = next(z for z in catlin_model.floor_heat if z.tag == "FH-M-BATH2")
    assert bath["wire_length_ft"] == round(zone.wire_length_m / 0.3048, 1)
    assert bath["system"] == zone.system and bath["storey"] == zone.storey
