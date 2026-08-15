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
from _helpers import CATLIN as CATLIN_DIR, REPO_ROOT

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
_GARAGE_MOVED = "the garage moved 7'-0\" south to close the breezeway gap to 4'-0 1/2\""

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
        "hall/living room, carrying FS-SECOND either side and BM-S-HALL's south reaction 8\" "
        "off its own bearing — so no single wall run spans the storey and the reference's "
        "one-piece centerline no longer pairs; the bearing stack itself is unbroken"
    ),
    "House Main Floor Ceiling Drywall": "ceiling finishes are IfcCovering now, not IfcSlab",
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
        "the two-tier arch stack became a single 16\" arched front wall with two 8' arches"
    ),
    "Sunken Garden Porch South Arch Wall (Upper)": (
        "the two-tier arch stack became a single 16\" arched front wall with two 8' arches"
    ),
    # "Sunken Garden North Wall Footing" was declared here until 2026-08-03 — the garden's
    # north wall was removed in the redesign and nothing stood on its footing line. It is
    # gone from this list because something does again: FT-B-BRICK, the plinth under the
    # glazed-brick veneer (params/foundations.py), lands 0.6 m from it and the matcher pairs
    # the two. They are not the same element and the north wall is still gone; a strip of
    # concrete simply runs along that line once more, which is all the matcher claims.
    # The garage moved 7'-0" south, from a 12' sheathing-plane gap to 5', so the breezeway
    # between it and the house is a 4'-0 1/2" slot sized to one polycarbonate panel. 7' is
    # far past MAX_PAIRED_PLACEMENT_DELTA_M — deliberately: an element that travelled that
    # far is not the same element in the same place, and the matcher is right to say so.
    # The garage itself is unchanged in size, section and framing; only its y is different.
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
DECLARED_WALL_EXTENT_CHANGES = {
    "House Basement Stair Side Wall (8\")": (
        1.03,
        "the stair shaft's west wall is 12\" concrete on x=10' now, not 8\" on x=11', and it "
        "runs the full north-row depth (14'-2 5/8\" of W-B-STR) instead of dying at the "
        "stair foot — 3'-4\" longer. 12\" on that line is what gives the shaft its "
        "code-minimum 7'-0\" clear well and the furnace room its 8'-6\", both measured off "
        "the same wall (reference basement plan). It read as an unpaired deletion until "
        "2026-08-02, when the ESS closet's two partitions and the W-B-CW split changed the "
        "basement's wall pool enough for the matcher to find the counterpart that was "
        "always there — the pairing is the right answer, and this is the size of it"
    ),
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
def current_ifc_path(tmp_path_factory):
    """The engine's own catlin IFC at framed LOD."""
    pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, [f.message for f in result.findings]
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return emit_ifc(model, tmp_path_factory.mktemp("current") / "catlin.ifc", lod="framed")


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
    "garage": (0.5588, "the garage storey sits at its ICF stem top, 1'-10\" above main"),
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
    # 20, not 25: the garage's 7'-0" move deliberately unpairs three of its stud-wall runs,
    # and *both* centerlines unpair because a stretch of each is an LVL rather than wall —
    # BM-S-HALL on second, BM-M-HALL on main (all recorded in DECLARED_DIVERGENCES). Every
    # wall that still pairs must still be within a construction-scale move of its reference
    # line, which the loop below asserts.
    assert len(pairs) >= 20, equivalence.status_counts()
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
    """The reference drew 7 layer-walls per exterior wall; the resolved stack carries 9.

    Two layers the old model never drew: the WRB, and the latex-paint film over the interior
    gypsum, which IRC R702.7 counts as the wall's Class III warm-side vapour retarder (drawing
    the lining as bare gypsum said the wall had no retarder at all). Comparing layer *counts*
    per run is what makes the layer-per-wall and layerset-per-wall conventions commensurable.
    """
    house_walls = [item for item in _paired(equivalence, "wall")
                   if item.reference_name.startswith("House ")
                   and "Centerline" not in item.reference_name]
    assert house_walls
    for item in house_walls:
        assert item.current_layer_count >= item.reference_layer_count, item.as_dict()
    exterior = [item for item in house_walls if item.reference_layer_count == 7]
    assert exterior, [item.reference_name for item in house_walls]
    assert all(item.current_layer_count == 9 for item in exterior), [
        item.as_dict() for item in exterior if item.current_layer_count != 9]


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
    framed_pairs = [item for item in _paired(equivalence, "wall")
                    if item.reference_framing_count]
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
