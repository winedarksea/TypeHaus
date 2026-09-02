"""WP3.7 — migration equivalence, measured against the archived catlin-house IFC.

The old builder's whole-house export lives in
``fixtures/catlin_reference/catlin_house_reference.ifc.gz`` (verbatim, IFC4, millimetres).
This module emits the current engine's catlin IFC, lifts **both files** into the neutral
semantic vocabulary (:mod:`typehaus.diff.semantic`) and diffs them
(:mod:`typehaus.diff.equivalence`): spatial hierarchy, per-storey category census, and one
row per occurrence pairing the reference element with the element that now means it.

Two conventions have to be normalized before anything is comparable, and they are the whole
reason a naive element-count check was never equivalence:

* the reference draws every **layer** of a wall as its own ``IfcWall`` (7 walls for one
  exterior wall, 2 XPS walls beside each basement wall); TypeHaus emits one wall carrying an
  ``IfcMaterialLayerSet``. Both sides are merged into face-adjacent *runs*, so a run's layer
  count is comparable either way.
* the reference splits the house into four ``IfcBuilding``s with nine storeys; TypeHaus
  models one building with five. ``STOREY_ALIASES`` states that mapping explicitly.

Catlin is expected to evolve past this source (→ ``test_catlin_reference_parity.py``), so a
divergence is a decision to record in ``DECLARED_DIVERGENCES`` with its reason — never a
reason to freeze the house, and never a reason to soften the comparison.
"""

from __future__ import annotations

import gzip
import os
from pathlib import Path

import pytest

from typehaus.diff.equivalence import (
    STATUS_ONLY_REFERENCE,
    EquivalenceTolerance,
    compare_semantic_models,
)
from typehaus.diff.semantic import semantic_model_from_ifc
from typehaus.quantities import ft

REFERENCE_ARCHIVE = (Path(__file__).parent / "fixtures" / "catlin_reference"
                     / "catlin_house_reference.ifc.gz")

# The reference's storey names → TypeHaus storey keys. The old builder gave the porch, the
# deck and the sunken garden their own storeys inside a separate "Porch + Sunken Garden"
# building; TypeHaus carries them on the house storey they physically sit on.
STOREY_ALIASES = {
    "Basement": "basement",
    "Main Floor": "main",
    "Second Floor": "second",
    "Attic Floor": "attic",
    "Garage Level": "garage",
    "Sunken Garden Floor": "basement",
    "Porch Floor": "main",
    "Deck Floor": "second",
    "Level 0": "breezeway-placeholder",
}
# The reference's fourth building is an explicitly labelled placeholder with no elements the
# design ever committed to; comparing against it would report noise as deletions.
DROPPED_REFERENCE_STOREYS = ("breezeway-placeholder",)

# Reference occurrences with no counterpart in the current model, each with the decision that
# removed it. A reference element that stops matching without being listed here is a
# regression: something the old house had and the new one silently lost.
_GARAGE_MOVED = "the garage moved 7'-5 5/8\" south to close the breezeway gap to 4'-0 1/2\""

DECLARED_DIVERGENCES = {
    "Basement Shower Recess (placeholder)": (
        "the old model reserved a slab recess placeholder; the sauna/shower is now a real "
        "room with its own floor-heat zone and drain fixtures (RM-B-SAUNA)"
    ),
    "House Basement Center Wall (N-S)": (
        "the old center wall ran the full 36' as one solid; the basement's N-S centerline is "
        "now split into segments at door and stair openings, so no single run spans it"
    ),
    "House Centerline Wall (Second)": (
        "8'-6\" of that line (y 22'-4\"..30'-10\") is BM-S-HALL now — a flush 3-ply 11-7/8\" "
        "LVL over the open hall/landing/stair — so no single wall run spans the storey and "
        "the reference's one-piece centerline no longer pairs; the bearing stack itself is "
        "unbroken, which the contract test measures wall runs + beam to prove"
    ),
    "House Centerline Wall (Main)": (
        "the same decision one storey down (2026-07-28): 4'-2\" of that line "
        "(y 21'-8\"..25'-10\") is BM-M-HALL now — a flush 3-ply 11-7/8\" LVL over the open "
        "hall/living room, carrying the second floor (FS-S-WEST/FS-S-EAST since "
        "2026-08-21) either side and BM-S-HALL's south reaction 8\" "
        "off its own bearing — so no single wall run spans the storey and the reference's "
        "one-piece centerline no longer pairs; the bearing stack itself is unbroken"
    ),
    "House Main Floor Ceiling Drywall": "ceiling finishes are IfcCovering now, not IfcSlab",
    "House Main Floor Concrete Slab": (
        "the 2026-08-21 basement-ceiling overhaul: the 1,233 SF x 9\" cast suspended deck "
        "became two I-joist FloorSystems (FS-M-WEST, FS-M-EAST, 819 SF) plus a 414 SF "
        "EPS-formed concrete band that keeps SL-M-DECK's tag and uid. Nothing pairs with a "
        "whole-floor slab any more because there is not one"
    ),
    "House Second Floor Ceiling Drywall": "ceiling finishes are IfcCovering now, not IfcSlab",
    "Deck Railing East": "railings are IfcRailing now, not wall solids",
    "Deck Railing South": "railings are IfcRailing now, not wall solids",
    "Deck Railing West": "railings are IfcRailing now, not wall solids",
    "Garage Door": (
        "the old overhead door was a full-height wall-width prism; the garage door is now a "
        "real opening + IfcDoor in the framed wall, at a different height and depth"
    ),
    "Sunken Garden East Door": "porch doors moved with the porch/balcony redesign",
    "Sunken Garden West Door": "porch doors moved with the porch/balcony redesign",
    "Sunken Garden East Wall (Open Zone)": "porch/balcony redesign (→ contract test)",
    "Sunken Garden West Wall (Open Zone)": "porch/balcony redesign (→ contract test)",
    "Sunken Garden East Wall (Porch Box)": "porch/balcony redesign (→ contract test)",
    "Sunken Garden West Wall (Porch Box)": "porch/balcony redesign (→ contract test)",
    "Sunken Garden Porch North Arch Wall (Lower)": (
        "the two-tier arch stack became a single 16\" arched front wall with two 8' arches, "
        "and that wall became PT-SG-FCOL + BM-SG-FRW/FRE on 2026-08-18 — the porch's front "
        "edge is a column and two beams now, mirroring its back edge"
    ),
    "Sunken Garden Porch South Arch Wall (Upper)": (
        "the two-tier arch stack became a single 16\" arched front wall with two 8' arches, "
        "and that wall became PT-SG-FCOL + BM-SG-FRW/FRE on 2026-08-18 — the porch's front "
        "edge is a column and two beams now, mirroring its back edge"
    ),
    "Sunken Garden Porch South Arch Wall (Lower)": (
        "the porch's south edge carries no wall at all since 2026-08-18: PT-SG-FCOL, a 16\" "
        "round cast column (square until 2026-08-28), and two flush LVL beams into the "
        "side walls replaced the arched cross-wall, and the 42\" masonry parapet over it "
        "became RL-SG-PORCH (→ contract test)"
    ),
    # "Sunken Garden North Wall Footing" is not declared here even though that wall is gone:
    # FT-B-BRICK, the plinth under the glazed-brick veneer (params/foundations.py), lands
    # 0.6 m from the old footing line and the matcher pairs the two. They are not the same
    # element — a strip of concrete simply runs along that line once more, which is all the
    # matcher claims.
    #
    # The garage move (_GARAGE_MOVED) leaves it unchanged in size, section and framing; only
    # its y is different, and 7'-5 5/8" is far past MAX_PAIRED_PLACEMENT_DELTA_M —
    # deliberately: an element that travelled that far is not the same element in the same
    # place, and the matcher is right to say so.
    #
    # The reference drew the basement stair-side line as 8" of concrete on x=11'; it is a
    # 2x6 bearing STUD wall on x=10' now — two of them, W-B-STR and W-B-STR3 — because it
    # retains nothing (`unbalanced_fill` is always ft(0)) and what it carries is
    # FS-M-MECH/FS-M-STAIR's joists and the W-M-STRW stack, which is a stud-wall job on a
    # footing. The footing is the part that did NOT change. The matcher stops pairing it,
    # correctly: a 6 1/4"/6 7/8" framed stack on a different line is not the same element as
    # an 8" pour, and there is no pour on this line to pair.
    "House Basement Stair Side Wall (8\")": (
        "the stair shaft's west wall is two framed 2x6 bearing walls on x=10' since "
        "2026-08-24 (W-B-STR + W-B-STR3), not a pour on x=11' — see plan/storeys/basement.py"
    ),
    "Garage Floor Slab": _GARAGE_MOVED,
    "Garage ICF Concrete Core 3": _GARAGE_MOVED,
    "Garage Stud Wall 1": _GARAGE_MOVED,
    "Garage Stud Wall 2": _GARAGE_MOVED,
    "Garage Stud Wall 4": _GARAGE_MOVED,
}

# Bounds on how far a *paired* occurrence may have travelled and still be the same element of
# the same house. These are design tolerances, not modelling noise: the exterior wall stack
# grew, so faces move by layer thicknesses, not by feet.
MAX_PAIRED_PLACEMENT_DELTA_M = 0.9      # ~3', the attic knee/gable stack's own height change
MAX_PAIRED_PLAN_EXTENT_DELTA_M = 0.75   # ~2'-6"

# Walls whose plan extent changed *by decision* and so may exceed the delta above. Same
# shape and the same discipline as DECLARED_STOREY_ELEVATION_MOVES: the change is pinned to
# its expected magnitude, so a further silent stretch of an already-declared wall still
# fails, and a stale entry is deleted the moment the wall stops diverging.
#
# Keyed on the *reference* name — the current tag is the thing that may be renamed.
DECLARED_WALL_EXTENT_CHANGES: dict[str, tuple[float, str]] = {
    # Empty: the mechanism stays even with nothing in it — a wall whose plan extent changes
    # by decision is pinned to the size of the change here, so a further silent stretch
    # still fails.
}

HOUSE_SIZE_FT = 36.0


@pytest.fixture(scope="module")
def reference_model(tmp_path_factory):
    """The archived catlin-house IFC, read with ifcopenshell — never regenerated."""
    pytest.importorskip("ifcopenshell")
    override = os.environ.get("TYPEHAUS_CATLIN_REFERENCE_IFC")
    if override:
        path = Path(override)
        if not path.exists():
            pytest.fail(f"TYPEHAUS_CATLIN_REFERENCE_IFC points at a missing file: {path}")
    else:
        if not REFERENCE_ARCHIVE.exists():
            pytest.skip(f"no reference IFC at {REFERENCE_ARCHIVE}")
        path = tmp_path_factory.mktemp("reference") / "catlin_house_reference.ifc"
        path.write_bytes(gzip.decompress(REFERENCE_ARCHIVE.read_bytes()))
    return semantic_model_from_ifc(path, "catlin-house (archived)", STOREY_ALIASES,
                                   drop_storeys=DROPPED_REFERENCE_STOREYS)


@pytest.fixture(scope="module")
def current_ifc_path(catlin_ifc_path):
    """The engine's own catlin IFC at framed LOD — the shared session emission."""
    pytest.importorskip("ifcopenshell")

    return catlin_ifc_path


@pytest.fixture(scope="module")
def current_model(current_ifc_path):
    """The emitted catlin IFC, read back through the same semantic extractor."""
    return semantic_model_from_ifc(current_ifc_path, "typehaus catlin")


# The reference states most keys' datum more than once: the porch/garden building repeats
# the basement/main/second keys at its own slab elevations (e.g. the Sunken Garden Floor at
# -2.6543 aliases onto "basement" beside the House Basement's -2.7432). The house's own
# storey — the garage building's for the garage key — is the authoritative datum per key.
REFERENCE_DATUM_BUILDINGS = ("House", "Garage")


@pytest.fixture(scope="module")
def equivalence(reference_model, current_model):
    return compare_semantic_models(reference_model, current_model, EquivalenceTolerance(),
                                   datum_buildings=REFERENCE_DATUM_BUILDINGS)


def _paired(report, category: str):
    return [item for item in report.matched() if item.category == category]


def test_spatial_hierarchy_carries_every_reference_storey(equivalence):
    """Four buildings and nine storeys collapse onto five storeys — none of them lost."""
    missing = [item.key for item in equivalence.storeys
               if item.status == STATUS_ONLY_REFERENCE]
    assert not missing, f"reference storeys with no counterpart: {missing}"
    assert {item.key for item in equivalence.storeys} >= {
        "basement", "main", "second", "attic", "garage"}


# Storey datums that deliberately moved since the reference: key → (expected current
# elevation in metres, the decision that moved it). Same discipline as
# DECLARED_DIVERGENCES: an undeclared move fails, and a declared one is pinned to its
# expected value so a further silent move still fails.
DECLARED_STOREY_ELEVATION_MOVES = {
    "second": (3.048, "the main storey grew from 9' to 10' floor-to-floor"),
    "attic": (6.096, "rides the taller stack: 10' + 10' instead of 9' + 9'"),
    "garage": (-0.3048, "the garage storey sits at its ICF stem top, which is 1'-10\" above "
                        "*grade* — and grade is 2'-10\" below the main floor since the "
                        "2026-08-18 lift and the 2026-08-21 deck overhaul, so the stem top "
                        "is -1'-0\". The reference model put the garage at the house datum "
                        "because it had the house at grade; the garage has not moved "
                        "relative to the ground it is driven into, the ground moved "
                        "relative to the house"),
    # **"basement" is deliberately absent.** The slab sits at -9'-1 7/16", which is 1 7/16"
    # off the reference's -9'-0" — inside the +/-0.05 m the comparison allows, so an entry
    # here would be stale and the `stale` assertion below would delete it for us. The
    # basement agrees with the reference model again; do not re-add it.
}


def test_storey_elevations_agree_where_both_models_state_one(reference_model, equivalence):
    """The reference stacks 9' floor to floor — read off its placements, not its labels.

    The reference writes ``IfcBuildingStorey.Elevation`` in metres inside a millimetre file,
    so only the placement is trustworthy; the extractor prefers it deliberately.

    The TypeHaus export now places every storey at its authored elevation (and states the
    ``Elevation`` attribute to match), so this is the live comparison the tripwire it
    replaced promised: every storey both sides state must agree with the reference datum
    within ±0.05 m, or carry its move in ``DECLARED_STOREY_ELEVATION_MOVES``.
    """
    elevations = {round(item.elevation_m, 4) for item in reference_model.storeys
                  if item.elevation_m is not None}
    assert {0.0, -2.7432, 2.7432, 5.4864} <= elevations, sorted(elevations)
    unstated = [item.key for item in equivalence.storeys
                if item.current_elevation_m is None]
    assert not unstated, f"the export stopped stating storey elevations for: {unstated}"
    # The datum is now resolved by the same rule the report uses, rather than re-derived
    # here with a test-local building filter that bypassed the last-wins bug.
    reference = {item.key: item.reference_elevation_m for item in equivalence.storeys
                 if item.reference_elevation_m is not None}
    for item in equivalence.storeys:
        if item.current_elevation_m is None or item.key not in reference:
            continue
        declared = DECLARED_STOREY_ELEVATION_MOVES.get(item.key)
        if declared is not None:
            expected, _reason = declared
            assert abs(item.current_elevation_m - expected) <= 0.05, item.as_dict()
        else:
            assert abs(item.current_elevation_m - reference[item.key]) <= 0.05, (
                item.as_dict())
    stale = [key for key, (expected, _reason) in DECLARED_STOREY_ELEVATION_MOVES.items()
             if key in reference and abs(expected - reference[key]) <= 0.05]
    assert not stale, ("DECLARED_STOREY_ELEVATION_MOVES lists storeys that no longer "
                       f"move — delete them: {stale}")


def test_every_reference_element_has_a_counterpart_or_a_declared_reason(equivalence):
    """Per-entity equivalence: nothing the old house had disappears unexplained."""
    unmatched = sorted(item.reference_name for item in equivalence.entities
                       if item.status == STATUS_ONLY_REFERENCE)
    undeclared = [name for name in unmatched if name not in DECLARED_DIVERGENCES]
    assert not undeclared, (
        "reference elements lost with no declared reason: " + ", ".join(undeclared))
    stale = [name for name in DECLARED_DIVERGENCES if name not in unmatched]
    assert not stale, ("DECLARED_DIVERGENCES lists elements that now match — delete them: "
                       + ", ".join(stale))


def test_paired_walls_stay_on_their_reference_wall_lines(equivalence):
    """Every reference wall line that still exists is within a construction-scale move."""
    pairs = _paired(equivalence, "wall")
    # 19, not 25: the garage's 7'-0" move deliberately unpairs three of its stud-wall runs,
    # *both* centerlines unpair because a stretch of each is an LVL rather than wall —
    # BM-S-HALL on second, BM-M-HALL on main — and the basement stair side wall unpaired
    # when it stopped being a pour at all (all recorded in DECLARED_DIVERGENCES).
    # Every wall that still pairs must still be within a construction-scale move of its
    # reference line, which the loop below asserts.
    assert len(pairs) >= 19, equivalence.status_counts()
    for item in pairs:
        assert item.placement_delta_m <= MAX_PAIRED_PLACEMENT_DELTA_M, item.as_dict()
        plan_delta = max(abs(item.size_delta_m[0]), abs(item.size_delta_m[1]))
        declared = DECLARED_WALL_EXTENT_CHANGES.get(item.reference_name)
        if declared is not None:
            expected, _reason = declared
            assert plan_delta <= expected, item.as_dict()
        else:
            assert plan_delta <= MAX_PAIRED_PLAN_EXTENT_DELTA_M, item.as_dict()
    # A declared stretch that no longer exceeds the ordinary tolerance is a line nobody
    # needs; the same guard DECLARED_STOREY_ELEVATION_MOVES carries.
    paired_deltas = {item.reference_name: max(abs(item.size_delta_m[0]),
                                              abs(item.size_delta_m[1]))
                     for item in pairs}
    stale = [name for name in DECLARED_WALL_EXTENT_CHANGES
             if paired_deltas.get(name, 0.0) <= MAX_PAIRED_PLAN_EXTENT_DELTA_M]
    assert not stale, ("DECLARED_WALL_EXTENT_CHANGES lists walls within the ordinary "
                       f"tolerance — delete them: {stale}")


def test_house_walls_gain_layers_rather_than_lose_them(equivalence):
    """The reference drew 7 layer-walls per exterior wall; the resolved stack carries 7.

    It carried 9 before the truss wall, and the two it gave up are the point of
    this test rather than a hole in it: the WRB went because closed-cell foam is the water
    plane now, and the two rigid-CI courses became sprayed bands plus a ``CavityFill`` inside
    the inner girt — a fill is not a layer, deliberately, because it is the other path
    through a depth and not a course of its own. The latex-paint film over the interior
    gypsum is still a layer the old model never drew (IRC R702.7 counts it as the wall's
    Class III warm-side vapour retarder), and the 4" of exterior insulation is still there.

    So the invariant this test defends is unchanged and is asserted below: never FEWER
    layer-walls than the reference. Comparing layer *counts* per run is what makes the
    layer-per-wall and layerset-per-wall conventions commensurable.
    """
    # ** THE FOUR ATTIC KNEE WALLS ARE OUT OF SCOPE. ** The reference drew
    # them as 7-layer exterior stud walls 5'-0" tall; what stands there now is
    # CATLIN_RAFTER_PLATE — one structure layer, 1 1/2" of 2x6 laid flat on the deck, with
    # no lining, sheathing or cladding because a plate on a subfloor has no faces. Comparing
    # its layer count to a stud wall's is a category error, not a regression: the wall did
    # not lose six layers, it stopped being a wall. The gables and every other storey are
    # still held to "never fewer than the reference", which is what this test defends.
    house_walls = [item for item in _paired(equivalence, "wall")
                   if item.reference_name.startswith("House ")
                   and "Centerline" not in item.reference_name
                   and "Knee" not in item.reference_name]
    assert house_walls
    for item in house_walls:
        assert item.current_layer_count >= item.reference_layer_count, item.as_dict()
    exterior = [item for item in house_walls if item.reference_layer_count == 7]
    assert exterior, [item.reference_name for item in house_walls]
    # EIGHT: paint, gwb, stud, sheathing, then THREE stand-off layers where the outrigger
    # band was one — 4" of foam in ONE band, the 1/2" vent gap, the girt — then the
    # cladding.
    #
    # The two that went are the inner girt and the 1" `foam-vent` slice in front of it. The
    # foam was authored as three bands so `analysis._layer_rsi` could parallel-path the inner
    # tier's wood rather than credit foam over 100% of the area; with that tier deleted there
    # is no wood in the foam to path, and one 4" INSULATION layer says the truth. What has
    # NOT changed is the depth (6" of stand-off) or the count's direction: still strictly
    # more layers than the seven-layer reference, which is what this test is about.
    #
    # The plant room's two exterior walls carry PLANT_EXT_2X6_HUMID: the same layers
    # outboard of the studs, with a three-layer sealed liner (PVC panel / drainage strapping
    # / Class I membrane) in place of the two-layer painted-gypsum lining. One more than the
    # rest.
    _HUMID_LINED = {"House Second Stud Wall 1", "House Second Stud Wall 4"}
    expected = {name: 9 for name in _HUMID_LINED}
    assert all(item.current_layer_count == expected.get(item.reference_name, 8)
               for item in exterior), [
        item.as_dict() for item in exterior
        if item.current_layer_count != expected.get(item.reference_name, 8)]


def test_house_footprint_still_measures_thirty_six_feet(reference_model, current_model):
    """The migration's headline dimension, measured on both models' own geometry.

    The longest wall run on a framed storey *is* the house's side: the garage and the garden
    sit outside the box and are shorter, so no tag or name is needed to find it.
    """
    def _longest_wall_run(model, storey: str) -> float:
        return max(item.plan_length_m for item in model.in_category("wall")
                   if item.storey_key == storey)

    for storey in ("main", "second"):
        reference_side = _longest_wall_run(reference_model, storey)
        current_side = _longest_wall_run(current_model, storey)
        assert reference_side >= ft(HOUSE_SIZE_FT).meters - 0.05, storey
        # Both sides lap their own cladding past the 36' structural box by a layer stack.
        assert current_side == pytest.approx(reference_side, abs=0.4), storey


def test_framing_survives_as_aggregated_members_and_only_grows(reference_model,
                                                               current_model, equivalence):
    """The old model framed studs only; the new one also frames openings, corners and roofs.

    Equivalence here is directional on purpose: a wall that the reference framed must still
    be framed, with at least as many members — losing framing is the regression to catch.
    """
    assert reference_model.framing_member_total() > 0
    assert current_model.framing_member_total() >= reference_model.framing_member_total()
    # "Knee" is excluded for the reason in test_house_walls_gain_layers_rather_than_lose_them:
    # a rafter plate frames one plate member where a 5'-0" stud wall framed 31, and that is
    # the change rather than a loss of framing. The house total still only grows.
    framed_pairs = [item for item in _paired(equivalence, "wall")
                    if item.reference_framing_count and "Knee" not in item.reference_name]
    assert framed_pairs
    for item in framed_pairs:
        assert item.current_framing_count >= item.reference_framing_count, item.as_dict()


def test_every_sweepable_framed_member_carries_real_geometry(current_ifc_path):
    """Framed-LOD members are real solids, not the bare identities they used to be.

    Member totals move whenever the framing solvers evolve, so nothing here pins a count.
    What must hold is *coverage*: every aggregated ``IfcMember`` whose profile a constant
    cross-section can honestly represent carries a Body representation. The only members
    allowed to stay bare are the plan-tapered boards no swept section can describe — the
    winder treads ("tapered tread") — and they must stay a sliver of the population.
    """
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.util.element

    from typehaus._meta import PSET_SOURCE

    f = ifcopenshell.open(str(current_ifc_path))
    members = f.by_type("IfcMember")
    assert members, "framed LOD should aggregate framing members"
    bare = [item for item in members if item.Representation is None]
    unexplained = []
    for item in bare:
        psets = ifcopenshell.util.element.get_psets(item, psets_only=True)
        profile = str(psets.get(PSET_SOURCE, {}).get("profile", ""))
        if profile != "tapered tread":
            unexplained.append((item.Name, profile))
    assert not unexplained, (
        f"members with a resolvable cross-section but no geometry: {unexplained[:10]}")
    coverage = (len(members) - len(bare)) / len(members)
    assert coverage >= 0.99, (
        f"member representation coverage regressed: {len(members) - len(bare)}"
        f"/{len(members)} = {coverage:.4f}")


def test_the_categories_the_reference_modelled_are_all_still_modelled(equivalence):
    """No whole category of the old house vanishes from a storey it occupied."""
    emptied = [row.as_dict() for row in equivalence.census
               if row.reference > 0 and row.current == 0]
    # Floor/ceiling finish slabs became IfcCovering (declared above), which the semantic
    # model censuses under its own category rather than as slabs.
    emptied = [row for row in emptied
               if not (row["category"] == "slab" and row["storey"] in ("attic", "garage"))]
    assert not emptied, emptied


def test_reference_openings_are_modelled_at_least_as_richly(reference_model, current_model):
    """The old export carried three doors and no windows; the port is not allowed to regress."""
    for category in ("door", "window"):
        assert (len(current_model.in_category(category))
                >= len(reference_model.in_category(category))), category
    assert len(current_model.in_category("window")) > 0


def test_equivalence_report_is_serializable_and_deterministic(equivalence, tmp_path):
    payload = equivalence.as_dict()
    assert set(payload) == {"models", "status_counts", "storeys", "census", "entities",
                            "class_census"}
    for row in payload["entities"]:
        assert {"category", "storey", "status", "reference", "current"} <= set(row)
    assert equivalence.to_json() == equivalence.to_json()
    written = equivalence.write(tmp_path / "equivalence.json")
    assert written.exists() and written.read_text() == equivalence.to_json()
