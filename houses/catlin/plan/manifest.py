"""Catlin house manifest — the real house, four structures, one plan (WP3.1).

Structures (all in the shared project-north frame, house sheathing SW corner at 0,0):
- House: 36'x36' at sheathing; basement / main / second / attic storeys.
- Garage: 24'x24' frost-depth ICF, shifted 30in north; full-width 6ft south gable extrusion.
- Sunken garden / porch / balcony: freestanding arched concrete structure south of house.
- North entry: shared composite bridge landing and interior garage continuation, broad
  east tiers and an on-edge wood screen; roof structure is an explicit off-model package.

This file is NOT ``# haus: editable``: it is the plain-Python assembler. The engine
reads ``format_version``/``requires_engine`` via the dialect path (AST, no import).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from typehaus import Building, Library, PlanModel, Project, Storey, ft, load_basemap_geojson

from library import (
    ALL_DUCT_PRODUCT_TYPES, ALL_ELECTRICAL_DEVICE_TYPES, ALL_RAILING_TYPES,
    ALL_REGISTER_TYPES, ALL_VENTILATION_EQUIPMENT_TYPES, DT_POCKET_INT_48,
    SEKTION_CASEWORK_TYPES, STANDARD_DOOR_TYPES, STARTER_APPLIANCE_TYPES,
    STARTER_CASEWORK_TYPES, STARTER_FIXTURE_TYPES, STARTER_FURNITURE_TYPES,
    WINDOW_TYPES_16_INCH_MODULE,
)

from params import (breezeway, foundations, hp1_north_pad, hp3_pad, landscape_gardens,
                    landscape_walk, main_deck, raised_garden, roof_trim, second_deck, solar,
                    sunken_garden)
from plan import (appliance_types, assemblies, backing, backing_wet, braced_walls,
                  circuits, countertops,
                  electrical, electrical_attic, equipment_types,
                  fixture_types, fixtures, furniture_types, landscape, lighting,
                  lighting_attic, lighting_types, mep, millwork, placeables, plant_types,
                  products,
                  site, transitions, views, wind_clamps)
from plan.storeys import attic, attic_studio, basement, garage, main, second

format_version = 1
requires_engine = ">=0.1,<0.2"

# Generated once by `haus new`; retained in source forever.
PROJECT_UUID = uuid.UUID("c471a000-93b5-4e6e-8f5a-000000000002")

_library = Library(
    materials=(*assemblies.MATERIALS, *plant_types.FOLIAGE_MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    # Brand and model for the products this house has actually chosen — identity only,
    # never a price (#28). The types above point at these by ``product_ref``.
    products=products.PRODUCTS,
    # The one library pocket size this house hangs, alongside the house's own catalog. Only
    # the pocket types are shared so far — the rest of `main.DOOR_TYPES` is a promotion for
    # another day, and `integrity.duplicate_catalog_tag` proves the tag sets stay disjoint.
    #
    # ** THE CATALOG CARRIES WHAT THE HOUSE HANGS, NOT THE WHOLE LADDER (2026-09-12). ** This
    # was the whole pocket ladder, which pulled all six Johnson 1500PF sizes in and left five of
    # them with no door, no price row and nothing to bill — the same dead weight the two
    # retired house types in `main.DOOR_TYPES` carried. D-M-LAUN is the only pocket in the
    # house. A second pocket door adds its size back here by name.
    door_types=(DT_POCKET_INT_48, *STANDARD_DOOR_TYPES, *main.LOCAL_DOOR_TYPES),
    window_types=WINDOW_TYPES_16_INCH_MODULE,
    # The shared catalogs supply every plumbing fixture, appliance, and railing this house
    # uses; only the wall-fitted mudroom closets stay house-local. Tags are disjoint, and
    # `integrity.duplicate_catalog_tag` now proves it rather than asserting it.
    furniture_types=(*STARTER_FURNITURE_TYPES, *STARTER_CASEWORK_TYPES,
                     *SEKTION_CASEWORK_TYPES, *furniture_types.FURNITURE_TYPES),
    # The library's fascia guard plus the house's own surface-mounted one — the porch
    # guard's baseplates land on concrete wall tops and buy no bracket kit, which is a
    # different order at a different rate. Tags are disjoint.
    railing_types=ALL_RAILING_TYPES,
    # The library's plumbing catalog is a planning ALLOWANCE (its own header says final
    # selection is the owner's). `plan/fixture_types.py` is that selection where one has
    # been made — so far the RM-M-BATH2 drop-in bath alone — and rides beside the
    # allowances rather than replacing them, the same split `appliance_types` uses.
    fixture_types=(*STARTER_FIXTURE_TYPES, *fixture_types.FIXTURE_TYPES),
    # The library's appliance catalog is a planning ALLOWANCE — its own header says final
    # selection is the owner's. `plan/appliance_types.py` is that selection, and rides
    # beside the allowances rather than replacing them: the disposer and the recirculating
    # hood are still unchosen and still correctly generic. Tags are disjoint (APPL-LG-*
    # vs APPL-*), which `integrity.duplicate_catalog_tag` proves rather than assumes.
    appliance_types=(*STARTER_APPLIANCE_TYPES, *appliance_types.APPLIANCE_TYPES),
    register_types=(*ALL_REGISTER_TYPES, *mep.REGISTER_TYPES),
    duct_product_types=ALL_DUCT_PRODUCT_TYPES,
    equipment_types=(*ALL_VENTILATION_EQUIPMENT_TYPES, *mep.EQUIPMENT_TYPES,
                     *equipment_types.EQUIPMENT_TYPES),
    electrical_device_types=(*ALL_ELECTRICAL_DEVICE_TYPES, *mep.ELECTRICAL_DEVICE_TYPES,
                             *electrical.DEVICE_TYPES, *lighting_types.LIGHTING_TYPES),
    circuits=circuits.CIRCUITS,
    # No ``load_managements``: retired 2026-09-12 with the Class 320 service. See the
    # block at the foot of plan/circuits.py.
    transitions=transitions.TRANSITIONS,
    construction_rules=tuple(assemblies.CONSTRUCTION_RULES),
    # Illustrative planting — counted in the takeoff's `planting` table, never priced.
    plant_types=plant_types.PLANT_TYPES,
)

# Survey basemap (parcel + contour topo) loaded from GeoJSON. The parcel/setbacks the user
# edits still live in the editable ``plan/site.py``; the GeoJSON only supplies the site-plan
# contour lines, so a real survey drops in without touching the editable source.
_basemap = load_basemap_geojson(Path(__file__).with_name("basemap.geojson"))
# The sidewalk's surfaces carry its fall (params/landscape_walk.py); merged here so the
# editable site file never hand-copies a derived outline.
_site = site.SITE.model_copy(update={
    "contours": _basemap.contours,
    "impervious_surfaces": (*site.SITE.impervious_surfaces, *landscape_walk.IMPERVIOUS),
})

# ``plan/site.py`` is ``# haus: editable`` and may hold only literals, so finished grade is
# written there as a literal and again in ``params/foundations.py`` as the value everything
# pinned to soil derives from. This is the only place the two meet; if they ever disagree,
# the garage would float or bury itself relative to the ground it stands on.
assert _site.grade is not None and (
    abs(_site.grade.meters - foundations.SITE_GRADE.meters) < 1e-9
), (f"plan/site.py grade {_site.grade.meters}m disagrees with "
    f"params/foundations.py SITE_GRADE {foundations.SITE_GRADE.meters}m")

# ``params/sunken_garden.py`` transcribes the same number a THIRD time, as
# ``SPEC.site_grade_in``, and for the same reason: a params module cannot import the plan
# that imports it. That constant carried a comment claiming ``test_retaining_court``
# asserted the two agreed — **it never did**, and the claim had stood through two grade
# moves. This is that assertion, beside the one it always said it was beside.
assert abs(_site.grade.meters - sunken_garden.SPEC.site_grade_in * 0.0254) < 1e-9, (
    f"plan/site.py grade {_site.grade.meters}m disagrees with "
    f"params/sunken_garden.py SPEC.site_grade_in {sunken_garden.SPEC.site_grade_in}in")

# ``LOCAL_YARD_GRADE_IN`` is the SOUTH YARD, and it is a fourth transcription of a plane —
# the one the sunken-garden retaining walls actually stand in, which is **not** the -2'-10"
# global bench above. It is a hard literal in ``params/sunken_garden.py``
# (``-RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN``) bound to ``plan/site.py``'s spot elevations
# by nothing but ``test_retaining_court``, while its two siblings above are asserted here.
#
# ** IT NOW CARRIES REAL ENGINEERING. ** Since 2026-09-14 the courtyard study derives its
# ordinary retained height from these same spot elevations
# (``engineering/sunken_garden/model_inputs.py``), so a spot that moves without this
# constant moving makes the study and the params file describe two different yards — which
# is precisely the split that pass was written to close. Asserted at load, beside the
# others, so it is loud rather than a test somebody runs.
_yard_spots = [spot.elevation.meters for spot in _site.spot_elevations
               if spot.kind == "grade"]
assert _yard_spots, "plan/site.py authors no grade spot elevations"
assert abs(min(_yard_spots) - sunken_garden.LOCAL_YARD_GRADE_IN * 0.0254) < 1e-9, (
    f"plan/site.py's lowest grade spot {min(_yard_spots)}m disagrees with "
    f"params/sunken_garden.py LOCAL_YARD_GRADE_IN "
    f"{sunken_garden.LOCAL_YARD_GRADE_IN}in")

# --- The structures on this site ---------------------------------------------------------
#
# A STOREY IS A DATUM PLANE; THE CONTAINER IS THE BUILDING. Revit's Level, IFC's
# ``IfcBuildingStorey`` and SketchUp's absence of levels all agree on this, and this file spent
# its life disagreeing: ``garage`` was a storey, which made one key carry both "which level"
# and "which of the four structures". Nothing downstream could ask "how big is this building"
# without re-deriving the answer — ``resolve/orientation.py``, ``server/space_summary.py`` and
# ``checks/code/mn_energy.py`` each derived it their own way, three times.
#
# Order is SHEET order: the A-1xx block, the storey tabs and the ``(building_order, elevation)``
# sort all read it, so the dwelling comes first and the sitework last.
#
# NOT ``Project.building``, which stays exactly what it was — the title-block name. Conflating
# the two would re-create the overload this pair exists to undo.
_buildings = (
    Building(uid="ABN42C8JSD", tag="house", name="House", kind="dwelling"),
    # Its own structure, four feet of outdoor air from the dwelling, on its own frost-depth
    # ICF: no common wall, no common roof plane, no opening between the two. MN classifies a
    # garage as IRC-4 accessory occupancy rather than part of the IRC-1 dwelling.
    Building(uid="8JB41G4FNP", tag="garage", name="Garage", kind="accessory"),
    Building(uid="4RASW24NKX", tag="court", name="Sunken garden, porch and balcony",
             kind="accessory"),
    # The north bridge landing and its screen. Strapped to the GARAGE (seven LSTA24s) and
    # bearing nothing at the house end, which is a movement joint. Its own building precisely
    # because it is physically continuous with both and belongs to neither — which is also why
    # membership here is AUTHORED and then verified, never derived from the wall graph.
    Building(uid="EX66NZS4P1", tag="entry", name="North entry", kind="accessory"),
    # Heat-pump pads and the raised garden bed. ``sitework`` is not an occupancy: it is how a
    # check that only reaches dwellings knows to stop here.
    Building(uid="BXG6W3G5W8", tag="yard", name="Yard structures", kind="sitework"),
)

_project = Project(
    name="Catlin House",
    project_uuid=PROJECT_UUID,
    site=_site,
    building=Building(name="Catlin House"),
    # The structure axis (above). ``building`` on the line before is the title block; these
    # are the buildings storeys belong to. Two different facts, deliberately two fields.
    buildings=_buildings,
    format_version=format_version,
    requires_engine=requires_engine,
    # Title-block identity, printed on every sheet. No firm or architect row: Minn. Stat.
    # 326.03 exempts a one- or two-family dwelling from needing a design professional, and
    # this set is drawn by the owner. ``preparer`` is whoever drew it, licensed or not — the
    # PE seal, when it comes, covers the S-sheets and lives in ``engineering.toml``.
    number="CAT-2026-001",
    owner="Colin Catlin",
    preparer="Colin Catlin (owner-drawn, Type:Haus)",
    # The start position the model is reviewed from.
    default_view_pan=(1.0, 1.0),
    # Required: any ClearanceZone carrying a ``code_profile`` (in this catalog, only the
    # water-closet envelope) is silently dropped by
    # ``resolve/placeables.py::_resolved_clearance_zones`` without it, and every water closet
    # grades against no clear space at all. Blast radius is that one zone family —
    # ``grep -rn 'code_profile=' library/ houses/`` returns a single hit.
    active_code_profile="MN/IRC",
)

# --- The levels, per building -------------------------------------------------------------
#
# ** EVERY NEW STOREY TAKES ITS ELEVATION FROM THE SAME CONSTANT OBJECT THE OLD ONE READ. **
# That rule is what makes the re-filing below a pure re-grouping: ``g-deck`` reads
# ``main_deck.MAIN_DATUM``, never a re-derived ``ft(0)``; ``court-low`` reads
# ``main_deck.BASEMENT_DATUM``. Delta zero — and ``tests/test_elevation_goldens.py`` proves it
# over every resolved z in the house rather than by a per-element audit.
#
# Two buildings holding a level at one elevation is the whole point, and is exactly what a flat
# storey list could not say: ``main``, ``g-deck``, ``court-main``, ``entry`` and ``yard-grade``
# are all at 0'-0". Any rationalization of the datums themselves — collapsing the garage's
# three planes, re-basing the entry — is a separate commit with its own delta analysis.
_storeys = (
    # -9'-1 7/16": the bearing seat less an exactly 8'-0" pour. Reads from
    # ``params/main_deck.py``, the way ``main`` already reads MAIN_DATUM from the same
    # module — a literal here would let the basement floor and its walls drift apart.
    Storey(uid="STBASEAAAA", tag="basement", building="house", elevation=main_deck.BASEMENT_DATUM,
           # 8'-0 15/16", derived — NOT the 9'-0" nominal the other storeys carry. This
           # basement's ceiling is the deck's soffit, and it is 11" under a nominal 9'-0".
           default_ceiling_height=main_deck.BASEMENT_CEILING_HEIGHT),
    # The datum every other elevation in the house is measured from, and the plane
    # SL-M-DECK pins its cap to — so it lives beside that arithmetic in params/main_deck.py
    # rather than as a second literal here. Note it is the TOP OF JOISTS, not the walking
    # surface: the subfloor rides 3/4" above it.
    Storey(uid="STMAINAAAA", tag="main", building="house", elevation=main_deck.MAIN_DATUM,
           default_ceiling_height=ft(9)),
    # The garage storey *is* the stem top: its wood walls bear there. The stem tops out
    # GARAGE_STEM_REVEAL above *grade*, not above the house datum, because the garage is
    # driven into off the ground and the ground is 2'-6" below the main floor. The slab it
    # floors stays down at grade, one GARAGE_STEM_REVEAL below this storey — which is why
    # the overhead door carries a negative sill (plan/storeys/garage.py). Plates are 8'-4"
    # so the garage roof stays put as grade takes the storey down; see the note on WALLS
    # there.
    # DRAWN WITH THE MAIN FLOOR. The garage bears its wood walls on the ICF stem top a foot
    # below the house's deck, and a foot is a step, not a storey: the garage is attached to
    # the house, a door connects them, and a reader holding the main floor plan needs to see
    # both. `level=` groups the sheet and the work package without moving the datum, which
    # stays the real bearing elevation every wall and sleeve here is resolved against.
    Storey(uid="STGARAAAAA", tag="garage", building="garage", level="main",
           elevation=ft(foundations.SITE_GRADE.feet + garage.GARAGE_STEM_REVEAL.feet),
           default_ceiling_height=ft(8, 4)),
    # Platform framing: 9' stud wall plus the nominal 12" floor system above it.
    Storey(uid="STSECDAAAA", tag="second", building="house", elevation=ft(10),
           default_ceiling_height=ft(9)),
    Storey(uid="STATTCAAAA", tag="attic", building="house", elevation=ft(20),
           default_ceiling_height=ft(11)),
    # --- garage ---------------------------------------------------------------------------
    # The frost-depth ICF stems, their footings and the hydrant drywell. These rode `basement`
    # because that is the level they are poured at; they are the GARAGE's foundation and never
    # the house's, and `foundations.BASEMENT_ELEMENTS` bundled them with the house footings.
    Storey(uid="9Q2NHMYFBC", tag="g-foundation", building="garage",
           elevation=main_deck.BASEMENT_DATUM,
           default_ceiling_height=main_deck.BASEMENT_CEILING_HEIGHT),
    # The garage's level AT THE MAIN DATUM — the plane the service-door threshold and the entry
    # landing share, and where the garage's own sleeves and supply devices sit. It is not
    # `garage` (-1'-0", the stem top where the wood walls bear) and not the slab (-2'-10", the
    # surface you park on): three distinct planes the one `garage` key stood in for. See
    # plan/mep.py's GARAGE_DECK_ELEMENTS for what a naive re-file onto `garage` would cost.
    Storey(uid="32KZP05FCA", tag="g-deck", building="garage",
           elevation=main_deck.MAIN_DATUM, default_ceiling_height=ft(9)),
    # --- court (sunken garden / porch / balcony) ------------------------------------------
    # The freestanding arched concrete structure south of the house: one building, three
    # levels, and the `sunken_garden.BASEMENT_/MAIN_/SECOND_ELEMENTS` split already named them.
    Storey(uid="PVEZTJYS9Z", tag="court-low", building="court",
           elevation=main_deck.BASEMENT_DATUM,
           default_ceiling_height=main_deck.BASEMENT_CEILING_HEIGHT),
    Storey(uid="NNYT3PHSZM", tag="court-main", building="court",
           elevation=main_deck.MAIN_DATUM, default_ceiling_height=ft(9)),
    Storey(uid="XX5J0ZSNDQ", tag="court-upper", building="court",
           elevation=ft(10), default_ceiling_height=ft(9)),
    # --- entry (north bridge) --------------------------------------------------------------
    # TWO levels, because the entry really does have two. `entry-low` is the shear panel's
    # own level: `W-BW-SCREEN` and `W-BW-SCREEN-SKIRT` were filed on the `garage` STOREY
    # (params/breezeway.py:279 explains why — on `main` the panel joined the HOUSE's braced
    # wall lines and stretched its dimension chain to 43'-2 5/8"). That workaround is exactly
    # what the building axis replaces: the panel is the ENTRY's west lateral system, so it
    # says so, and nothing about the house's braced-wall derivation can reach it either way.
    #
    # ** THE ELEVATION IS THE GARAGE STOREY'S OWN EXPRESSION, CHARACTER FOR CHARACTER. ** Not
    # a literal -1'-0": the stem tops out GARAGE_STEM_REVEAL above GRADE, and a literal here
    # would drift the panel off the stem the first time grade moved. Delta zero.
    # Same floor, same reason — and this is the split the whole exercise was aimed at: the
    # screen wall stands on the garage's datum while the landing it encloses is at 0'-0", so
    # without this the north entry appears on two sheets and on neither of them whole.
    Storey(uid="E1V1RZ6S8B", tag="entry-low", building="entry", level="main",
           elevation=ft(foundations.SITE_GRADE.feet + garage.GARAGE_STEM_REVEAL.feet),
           default_ceiling_height=ft(8, 4)),
    # The landing level: the bridge deck, its beams, piers, tiers and guards, at the main
    # datum the service-door threshold shares.
    Storey(uid="3FYD4882GK", tag="entry", building="entry",
           elevation=main_deck.MAIN_DATUM, default_ceiling_height=ft(9)),
    # --- yard -----------------------------------------------------------------------------
    Storey(uid="XRMKTA1PNF", tag="yard-grade", building="yard",
           elevation=main_deck.MAIN_DATUM, default_ceiling_height=ft(9)),
    Storey(uid="4C808V8ER0", tag="yard-low", building="yard",
           elevation=main_deck.BASEMENT_DATUM,
           default_ceiling_height=main_deck.BASEMENT_CEILING_HEIGHT),
)

PLAN = (
    PlanModel(project=_project, library=_library, storeys=_storeys)
    # --- house -----------------------------------------------------------------------------
    #
    # The bulk of the model, and NONE of it moves: the four house storeys keep their tags,
    # their elevations and their element lists. What left each list below is named, so the
    # diff is readable as "these four groups became their own buildings" rather than as a
    # whole-house re-file.
    .with_elements(
        "basement",
        # `foundations.BASEMENT_ELEMENTS` was the house footings AND the garage's stems,
        # footings and hydrant drywell in one list; the four garage names are spread onto
        # `g-foundation` below instead. Spread by name rather than by editing params/, which
        # already named all four at module level.
        [*basement.ELEMENTS, *fixtures.BASEMENT_FIXTURES,
         *foundations.HOUSE_FOOTINGS, *foundations.HOUSE_FOOTING_BEDDING,
         *foundations.VENEER_PLINTH, *foundations.VENEER_PLINTH_BEDDING,
         *mep.BASEMENT_ELEMENTS, *electrical.BASEMENT_ELEMENTS,
         *lighting.BASEMENT_LIGHTING,
         *placeables.BASEMENT_PLACEABLES, *millwork.BASEMENT_SHELVES,
         *backing.BASEMENT_BACKING, *backing_wet.BASEMENT_WET_BACKING],
    )
    .with_elements(
        "main",
        # `fixtures.PORCH_HYDRANT` stays HOUSE, and the tag is the trap: it is bolted
        # through `W-M-S1`, the house's own south wall, and names `RM-M-BED` behind it. A
        # hydrant you reach from the porch still belongs to the wall it penetrates. Same for
        # `BALCONY_HYDRANT` on `second` (`W-S-S1`, `RM-S-PLANT`).
        [*main.ELEMENTS, *fixtures.MAIN_FIXTURES, *fixtures.PORCH_HYDRANT,
         *main_deck.MAIN_ELEMENTS, *mep.MAIN_ELEMENTS,
         # The four wall corners where the north/south board & batten meets the east/west
         # PBR. Filed on `main` (the run starts below the main datum) though the module
         # that derives them is the roof eave's — it owns the cladding-face constant.
         *roof_trim.MAIN_ELEMENTS,
         *electrical.MAIN_ELEMENTS, *lighting.MAIN_LIGHTING,
         *placeables.MAIN_PLACEABLES, *views.DETAIL_SLICES,
         *millwork.MILLWORK, *millwork.MAIN_SHELVES,
         *countertops.MAIN_COUNTERTOPS,
         *backing.MAIN_BACKING, *backing_wet.MAIN_WET_BACKING,
         *braced_walls.MAIN_BRACED_WALLS, *braced_walls.MAIN_BRACED_CONNECTORS],
    )
    .with_elements("second", [*second.ELEMENTS, *attic_studio.SECOND_ELEMENTS,
                                *fixtures.SECOND_FIXTURES,
                                *fixtures.BALCONY_HYDRANT,
                                *mep.SECOND_ELEMENTS,
                                *electrical.SECOND_ELEMENTS, *lighting.SECOND_LIGHTING,
                                *placeables.SECOND_PLACEABLES,
                                *second_deck.SECOND_ELEMENTS,
                                *millwork.SECOND_SHELVES,
                                *countertops.SECOND_COUNTERTOPS,
                                *backing.SECOND_BACKING,
                                *backing_wet.SECOND_WET_BACKING,
                                *braced_walls.SECOND_BRACED_WALLS,
                                *braced_walls.SECOND_BRACED_CONNECTORS])
    .with_elements("attic", [*attic.ELEMENTS, *attic_studio.ATTIC_ELEMENTS,
                             *fixtures.ATTIC_FIXTURES,
                             *roof_trim.ATTIC_ELEMENTS,
                             *mep.ATTIC_ELEMENTS, *electrical.ATTIC_ELEMENTS,
                             *solar.ATTIC_ELEMENTS, *lighting_attic.ATTIC_LIGHTING,
                             *electrical_attic.NEC_FILL_ATTIC,
                             *placeables.ATTIC_PLACEABLES,
                             *millwork.ATTIC_SHELVES,
                             *backing.ATTIC_BACKING,
                             *backing_wet.ATTIC_WET_BACKING])
    # --- garage ----------------------------------------------------------------------------
    .with_elements("g-foundation", [*foundations.GARAGE_STEM_NODES,
                                    *foundations.GARAGE_STEM_WALLS,
                                    *foundations.GARAGE_FOOTINGS,
                                    foundations.GARAGE_HYDRANT_DRYWELL])
    .with_elements("garage", [*garage.ELEMENTS, *foundations.GARAGE_ELEMENTS,
                              *backing.GARAGE_BACKING,
                              *electrical.GARAGE_ELEMENTS,
                              *fixtures.GARAGE_FIXTURES,
                              *lighting.GARAGE_LIGHTING,
                              *placeables.GARAGE_PLACEABLES,
                              *wind_clamps.GARAGE_WALL_WIND_CLAMPS,
                              *wind_clamps.GARAGE_ROOF_WIND_CLAMPS,
                              *braced_walls.GARAGE_BRACED_WALLS,
                              *braced_walls.GARAGE_BRACED_CONNECTORS])
    .with_elements("g-deck", [*mep.GARAGE_DECK_ELEMENTS])
    # --- court (sunken garden / porch / balcony) --------------------------------------------
    .with_elements("court-low", [*sunken_garden.BASEMENT_ELEMENTS])
    .with_elements("court-main", [*sunken_garden.MAIN_ELEMENTS])
    .with_elements("court-upper", [*sunken_garden.SECOND_ELEMENTS])
    # --- entry (north bridge) --------------------------------------------------------------
    #
    # What this buys at the seam, for free: `W-BW-SCREEN`/`-SKIRT`, `FS-BW-GARAGE`,
    # `RL-BW-GARAGE-E` and `SC-BW-WEST` now sit in one cell with the screen that supports
    # them, so a sheet can draw the entry whole. And the `params/breezeway.py:279` workaround —
    # keep the screen off the house's braced-wall lines by the storey it is filed on — is
    # satisfied BY THE MODEL rather than by the filing.
    # `GARAGE_STOREY_ELEMENTS` is the screen panel, its skirt and their four nodes — the list
    # is `[]` at line 288 and `.extend()`ed twice further down the module, so read it at
    # import time, not at its assignment.
    .with_elements("entry-low", [*breezeway.GARAGE_STOREY_ELEMENTS])
    .with_elements("entry", [*breezeway.MAIN_ELEMENTS])
    # --- yard (sitework) -------------------------------------------------------------------
    .with_elements("yard-grade", [*hp3_pad.MAIN_ELEMENTS, *hp1_north_pad.MAIN_ELEMENTS,
                                  *landscape_gardens.MAIN_ELEMENTS, *landscape.APPLES,
                                  *landscape_walk.MAIN_ELEMENTS])
    .with_elements("yard-low", [*raised_garden.BASEMENT_ELEMENTS])
)
