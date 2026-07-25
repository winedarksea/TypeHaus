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

from library import (STARTER_APPLIANCE_TYPES, STARTER_CASEWORK_TYPES, STARTER_FIXTURE_TYPES,
                     STARTER_FURNITURE_TYPES)

from params import breezeway, foundations, raised_garden, roof_trim, sunken_garden
from plan import assemblies, fixture_types, fixtures, mep, placeables, site, transitions, views
from plan.storeys import attic, basement, garage, main, second

format_version = 1
requires_engine = ">=0.1,<0.2"

# Generated once by `haus new`; retained in source forever.
PROJECT_UUID = uuid.UUID("c471a000-93b5-4e6e-8f5a-000000000002")

_library = Library(
    materials=tuple(assemblies.MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    door_types=tuple(main.DOOR_TYPES),
    window_types=tuple(main.WINDOW_TYPES),
    # House-local catalogs first, then the shared starter set; the tags are disjoint by
    # design (the shared plumbing fixtures use -STD/-24/-36 suffixes so nothing collides).
    furniture_types=(*STARTER_FURNITURE_TYPES, *STARTER_CASEWORK_TYPES),
    fixture_types=(*fixture_types.FIXTURE_TYPES, *STARTER_FIXTURE_TYPES),
    appliance_types=(*fixture_types.APPLIANCE_TYPES, *STARTER_APPLIANCE_TYPES),
    register_types=mep.REGISTER_TYPES,
    equipment_types=mep.EQUIPMENT_TYPES,
    electrical_device_types=mep.ELECTRICAL_DEVICE_TYPES,
    transitions=transitions.TRANSITIONS,
    construction_rules=tuple(assemblies.CONSTRUCTION_RULES),
)

# Survey basemap (parcel + contour topo) loaded from GeoJSON. The parcel/setbacks the user
# edits still live in the editable ``plan/site.py``; the GeoJSON only supplies the site-plan
# contour lines, so a real survey drops in without touching the editable source.
_basemap = load_basemap_geojson(Path(__file__).with_name("basemap.geojson"))
_site = site.SITE.model_copy(update={"contours": _basemap.contours})

_project = Project(
    name="Catlin House",
    project_uuid=PROJECT_UUID,
    site=_site,
    building=Building(name="Catlin House"),
    format_version=format_version,
    requires_engine=requires_engine,
)

_storeys = (
    Storey(uid="STBASEAAAA", tag="basement", elevation=ft(-9),
           default_ceiling_height=ft(9)),
    Storey(uid="STMAINAAAA", tag="main", elevation=ft(0),
           default_ceiling_height=ft(9)),
    Storey(uid="STGARAAAAA", tag="garage", elevation=ft(1, 10),
           default_ceiling_height=ft(8)),
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
        [*basement.ELEMENTS, *sunken_garden.BASEMENT_ELEMENTS,
         *raised_garden.BASEMENT_ELEMENTS, *foundations.BASEMENT_ELEMENTS,
         *mep.BASEMENT_ELEMENTS, *placeables.BASEMENT_PLACEABLES],
    )
    .with_elements(
        "main",
        [*main.ELEMENTS, *fixtures.MAIN_FIXTURES, *sunken_garden.MAIN_ELEMENTS,
         *foundations.MAIN_ELEMENTS, *breezeway.MAIN_ELEMENTS, *mep.MAIN_ELEMENTS,
         *placeables.MAIN_PLACEABLES, *views.DETAIL_SLICES],
    )
    .with_elements("garage", [*garage.ELEMENTS, *placeables.GARAGE_PLACEABLES])
    .with_elements("second", [*second.ELEMENTS, *fixtures.SECOND_FIXTURES,
                                *sunken_garden.SECOND_ELEMENTS, *mep.SECOND_ELEMENTS, *placeables.SECOND_PLACEABLES])
    .with_elements("attic", [*attic.ELEMENTS, *roof_trim.ATTIC_ELEMENTS,
                             *mep.ATTIC_ELEMENTS, *placeables.ATTIC_PLACEABLES])
)
