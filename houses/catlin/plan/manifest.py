"""Catlin house manifest — the real house, four structures, one plan (WP3.1).

Structures (all in the shared project-north frame, house sheathing SW corner at 0,0):
- House: 36'x36' at sheathing; basement / main / second / attic storeys.
- Garage: freestanding 24'x24' ICF stem + 2x6 walls, 4' north of the house
  (its own ``garage`` storey at the stem top elevation).
- Sunken garden / porch / balcony: one freestanding arched concrete structure,
  5" south of the house (params/sunken_garden.py).
- Breezeway: enclosed 4'x8' polycarbonate shelter on freestanding 6x6 posts, spanning
  the 4'-0 1/8" gap between the house entry and the garage service door
  (params/breezeway.py — deck, posts, beams, rafters, glazing).

This file is NOT ``# haus: editable``: it is the plain-Python assembler. The engine
reads ``format_version``/``requires_engine`` via the dialect path (AST, no import).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from typehaus import Building, Library, PlanModel, Project, Storey, ft, load_basemap_geojson

from library import (STARTER_APPLIANCE_TYPES, STARTER_CASEWORK_TYPES, STARTER_DOOR_TYPES,
                     STARTER_FIXTURE_TYPES, STARTER_FURNITURE_TYPES, STARTER_RAILING_TYPES)

from params import (breezeway, foundations, main_deck, raised_garden, roof_trim,
                    second_deck, solar, sunken_garden)
from plan import (appliance_types, assemblies, circuits, electrical, electrical_attic,
                  fixture_types, fixtures, furniture_types, lighting, lighting_attic,
                  lighting_types, mep, millwork, placeables, products, site, transitions,
                  views, wind_clamps)
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
    railing_types=STARTER_RAILING_TYPES,
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

_project = Project(
    name="Catlin House",
    project_uuid=PROJECT_UUID,
    site=_site,
    building=Building(name="Catlin House"),
    format_version=format_version,
    requires_engine=requires_engine,
    # One pan-button click right + one down from the plain whole-building fit — the start
    # position the model is actually reviewed from (2026-08-03).
    default_view_pan=(1.0, 1.0),
    # 2026-08-29. Until this was set, EVERY ClearanceZone carrying a ``code_profile`` was
    # silently dropped by ``resolve/placeables.py::_resolved_clearance_zones`` — which in
    # this catalog is exactly one zone, the water-closet envelope, and therefore all five of
    # this house's water closets were graded against no clear space at all. RM-M-BATH1 sat
    # 1.06" inside UPC 402.5's 24" for weeks and reported 0 FAIL. The blast radius of turning
    # it on is that one zone family: ``grep -rn 'code_profile=' library/ houses/`` returns a
    # single hit.
    active_code_profile="MN/IRC",
)

_storeys = (
    # -9'-1 7/16": the bearing seat less an exactly 8'-0" pour. It was a literal ft(-9, -4)
    # here until 2026-08-23 — the one storey elevation not derived from the arithmetic that
    # sets it — which is how the basement floor and the walls standing on it could have
    # moved apart. It reads from ``params/main_deck.py`` now, the way ``main`` already reads
    # MAIN_DATUM from the same module.
    Storey(uid="STBASEAAAA", tag="basement", elevation=main_deck.BASEMENT_DATUM,
           default_ceiling_height=ft(9)),
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
    # the overhead door carries a negative sill (plan/storeys/garage.py). Plates grew to
    # 8'-4" on 2026-08-21 so the garage roof stayed put when grade took the storey down 4";
    # see the note on WALLS there.
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
         *placeables.BASEMENT_PLACEABLES, *millwork.BASEMENT_SHELVES],
    )
    .with_elements(
        "main",
        [*main.ELEMENTS, *fixtures.MAIN_FIXTURES, *fixtures.PORCH_HYDRANT,
         *sunken_garden.MAIN_ELEMENTS,
         *breezeway.MAIN_ELEMENTS, *main_deck.MAIN_ELEMENTS, *mep.MAIN_ELEMENTS,
         *electrical.MAIN_ELEMENTS, *lighting.MAIN_LIGHTING,
         *placeables.MAIN_PLACEABLES, *views.DETAIL_SLICES,
         *millwork.MILLWORK, *millwork.MAIN_SHELVES],
    )
    .with_elements("garage", [*garage.ELEMENTS, *foundations.GARAGE_ELEMENTS,
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
                                *millwork.SECOND_SHELVES])
    .with_elements("attic", [*attic.ELEMENTS, *attic_studio.ATTIC_ELEMENTS,
                             *fixtures.ATTIC_FIXTURES,
                             *roof_trim.ATTIC_ELEMENTS,
                             *mep.ATTIC_ELEMENTS, *electrical.ATTIC_ELEMENTS,
                             *solar.ATTIC_ELEMENTS, *lighting_attic.ATTIC_LIGHTING,
                             *electrical_attic.NEC_FILL_ATTIC,
                             *placeables.ATTIC_PLACEABLES,
                             *millwork.ATTIC_SHELVES])
)
