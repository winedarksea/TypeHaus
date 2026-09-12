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

from library import (STARTER_APPLIANCE_TYPES, STARTER_CASEWORK_TYPES, STARTER_DOOR_TYPES,
                     STARTER_FIXTURE_TYPES, STARTER_FURNITURE_TYPES, STARTER_RAILING_TYPES)

from params import (breezeway, foundations, hp1_north_pad, hp3_pad, main_deck, raised_garden,
                    roof_trim, second_deck, solar, sunken_garden)
from plan import (appliance_types, assemblies, backing, circuits, countertops, electrical,
                  electrical_attic,
                  fixture_types, fixtures, furniture_types, lighting, lighting_attic,
                  lighting_types, mep, millwork, placeables, products, railing_types,
                  site, transitions, views, wind_clamps)
from plan.storeys import attic, attic_studio, basement, garage, main, second

format_version = 1
requires_engine = ">=0.1,<0.2"

# Generated once by `haus new`; retained in source forever.
PROJECT_UUID = uuid.UUID("c471a000-93b5-4e6e-8f5a-000000000002")

_library = Library(
    materials=tuple(assemblies.MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    # Brand and model for the products this house has actually chosen — identity only,
    # never a price (#28). The types above point at these by ``product_ref``.
    products=products.PRODUCTS,
    # The library's pocket family alongside the house's own catalog. Only the pocket
    # types are shared so far — the rest of `main.DOOR_TYPES` is a promotion for another
    # day, and `integrity.duplicate_catalog_tag` proves the two tag sets stay disjoint.
    door_types=(*STARTER_DOOR_TYPES, *main.DOOR_TYPES),
    window_types=tuple(main.WINDOW_TYPES),
    # The shared catalogs supply every plumbing fixture, appliance, and railing this house
    # uses; only the wall-fitted mudroom closets stay house-local. Tags are disjoint, and
    # `integrity.duplicate_catalog_tag` now proves it rather than asserting it.
    furniture_types=(*STARTER_FURNITURE_TYPES, *STARTER_CASEWORK_TYPES,
                     *furniture_types.FURNITURE_TYPES),
    # The library's fascia guard plus the house's own surface-mounted one — the porch
    # guard's baseplates land on concrete wall tops and buy no bracket kit, which is a
    # different order at a different rate. Tags are disjoint.
    railing_types=(*STARTER_RAILING_TYPES, *railing_types.RAILING_TYPES),
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
    register_types=mep.REGISTER_TYPES,
    equipment_types=(*mep.EQUIPMENT_TYPES, *electrical.EQUIPMENT_TYPES),
    electrical_device_types=(*mep.ELECTRICAL_DEVICE_TYPES, *electrical.DEVICE_TYPES,
                             *lighting_types.LIGHTING_TYPES),
    circuits=circuits.CIRCUITS,
    load_managements=circuits.LOAD_MANAGEMENTS,
    transitions=transitions.TRANSITIONS,
    construction_rules=tuple(assemblies.CONSTRUCTION_RULES),
)

# Survey basemap (parcel + contour topo) loaded from GeoJSON. The parcel/setbacks the user
# edits still live in the editable ``plan/site.py``; the GeoJSON only supplies the site-plan
# contour lines, so a real survey drops in without touching the editable source.
_basemap = load_basemap_geojson(Path(__file__).with_name("basemap.geojson"))
_site = site.SITE.model_copy(update={"contours": _basemap.contours})

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

_project = Project(
    name="Catlin House",
    project_uuid=PROJECT_UUID,
    site=_site,
    building=Building(name="Catlin House"),
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

_storeys = (
    # -9'-1 7/16": the bearing seat less an exactly 8'-0" pour. Reads from
    # ``params/main_deck.py``, the way ``main`` already reads MAIN_DATUM from the same
    # module — a literal here would let the basement floor and its walls drift apart.
    Storey(uid="STBASEAAAA", tag="basement", elevation=main_deck.BASEMENT_DATUM,
           # 8'-0 15/16", derived — NOT the 9'-0" nominal the other storeys carry. This
           # basement's ceiling is the deck's soffit, and it is 11" under a nominal 9'-0".
           default_ceiling_height=main_deck.BASEMENT_CEILING_HEIGHT),
    # The datum every other elevation in the house is measured from, and the plane
    # SL-M-DECK pins its cap to — so it lives beside that arithmetic in params/main_deck.py
    # rather than as a second literal here. Note it is the TOP OF JOISTS, not the walking
    # surface: the subfloor rides 3/4" above it.
    Storey(uid="STMAINAAAA", tag="main", elevation=main_deck.MAIN_DATUM,
           default_ceiling_height=ft(9)),
    # The garage storey *is* the stem top: its wood walls bear there. The stem tops out
    # GARAGE_STEM_REVEAL above *grade*, not above the house datum, because the garage is
    # driven into off the ground and the ground is 2'-6" below the main floor. The slab it
    # floors stays down at grade, one GARAGE_STEM_REVEAL below this storey — which is why
    # the overhead door carries a negative sill (plan/storeys/garage.py). Plates are 8'-4"
    # so the garage roof stays put as grade takes the storey down; see the note on WALLS
    # there.
    Storey(uid="STGARAAAAA", tag="garage",
           elevation=ft(foundations.SITE_GRADE.feet + garage.GARAGE_STEM_REVEAL.feet),
           default_ceiling_height=ft(8, 4)),
    # Platform framing: 9' stud wall plus the nominal 12" floor system above it.
    Storey(uid="STSECDAAAA", tag="second", elevation=ft(10),
           default_ceiling_height=ft(9)),
    Storey(uid="STATTCAAAA", tag="attic", elevation=ft(20),
           default_ceiling_height=ft(11)),
)

PLAN = (
    PlanModel(project=_project, library=_library, storeys=_storeys)
    .with_elements(
        "basement",
        [*basement.ELEMENTS, *fixtures.BASEMENT_FIXTURES,
         *sunken_garden.BASEMENT_ELEMENTS,
         *raised_garden.BASEMENT_ELEMENTS, *foundations.BASEMENT_ELEMENTS,
         *mep.BASEMENT_ELEMENTS, *electrical.BASEMENT_ELEMENTS,
         *lighting.BASEMENT_LIGHTING,
         *placeables.BASEMENT_PLACEABLES, *millwork.BASEMENT_SHELVES,
         *backing.BASEMENT_BACKING],
    )
    .with_elements(
        "main",
        [*main.ELEMENTS, *fixtures.MAIN_FIXTURES, *fixtures.PORCH_HYDRANT,
         *sunken_garden.MAIN_ELEMENTS,
         *breezeway.MAIN_ELEMENTS, *main_deck.MAIN_ELEMENTS, *mep.MAIN_ELEMENTS,
         # EQ-M-HP3-OD's pad and stand, in the slot north of the house (params/hp3_pad.py).
         *hp3_pad.MAIN_ELEMENTS,
         # EQ-M-HP1-OD's pad and stand, north face east of the garage
         # (params/hp1_north_pad.py) — it crossed from the south pocket on 2026-09-04.
         *hp1_north_pad.MAIN_ELEMENTS,
         # The four wall corners where the north/south board & batten meets the east/west
         # PBR. Filed on `main` (the run starts below the main datum) though the module
         # that derives them is the roof eave's — it owns the cladding-face constant.
         *roof_trim.MAIN_ELEMENTS,
         *electrical.MAIN_ELEMENTS, *lighting.MAIN_LIGHTING,
         *placeables.MAIN_PLACEABLES, *views.DETAIL_SLICES,
         *millwork.MILLWORK, *millwork.MAIN_SHELVES,
         *countertops.MAIN_COUNTERTOPS,
         *backing.MAIN_BACKING],
    )
    .with_elements("garage", [*garage.ELEMENTS, *foundations.GARAGE_ELEMENTS,
                              *breezeway.GARAGE_STOREY_ELEMENTS,
                              *backing.GARAGE_BACKING,
                              *electrical.GARAGE_ELEMENTS,
                              *fixtures.GARAGE_FIXTURES,
                              *lighting.GARAGE_LIGHTING,
                              *placeables.GARAGE_PLACEABLES,
                              *wind_clamps.GARAGE_WALL_WIND_CLAMPS,
                              *wind_clamps.GARAGE_ROOF_WIND_CLAMPS])
    .with_elements("second", [*second.ELEMENTS, *attic_studio.SECOND_ELEMENTS,
                                *fixtures.SECOND_FIXTURES,
                                *fixtures.BALCONY_HYDRANT,
                                *sunken_garden.SECOND_ELEMENTS, *mep.SECOND_ELEMENTS,
                                *electrical.SECOND_ELEMENTS, *lighting.SECOND_LIGHTING,
                                *placeables.SECOND_PLACEABLES,
                                *second_deck.SECOND_ELEMENTS,
                                *millwork.SECOND_SHELVES,
                                *countertops.SECOND_COUNTERTOPS,
                                *backing.SECOND_BACKING])
    .with_elements("attic", [*attic.ELEMENTS, *attic_studio.ATTIC_ELEMENTS,
                             *fixtures.ATTIC_FIXTURES,
                             *roof_trim.ATTIC_ELEMENTS,
                             *mep.ATTIC_ELEMENTS, *electrical.ATTIC_ELEMENTS,
                             *solar.ATTIC_ELEMENTS, *lighting_attic.ATTIC_LIGHTING,
                             *electrical_attic.NEC_FILL_ATTIC,
                             *placeables.ATTIC_PLACEABLES,
                             *millwork.ATTIC_SHELVES,
                             *backing.ATTIC_BACKING])
)
