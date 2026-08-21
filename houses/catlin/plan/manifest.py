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
                     STARTER_FURNITURE_TYPES, STARTER_RAILING_TYPES)

from params import breezeway, foundations, raised_garden, roof_trim, solar, sunken_garden
from plan import (assemblies, circuits, electrical, fixtures, furniture_types,
                  lighting, lighting_types, mep, placeables, site, transitions,
                  views, wind_clamps)
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
    # The shared catalogs supply every plumbing fixture, appliance, and railing this house
    # uses; only the wall-fitted mudroom closets stay house-local. Tags are disjoint, and
    # `integrity.duplicate_catalog_tag` now proves it rather than asserting it.
    furniture_types=(*STARTER_FURNITURE_TYPES, *STARTER_CASEWORK_TYPES,
                     *furniture_types.FURNITURE_TYPES),
    railing_types=STARTER_RAILING_TYPES,
    fixture_types=STARTER_FIXTURE_TYPES,
    appliance_types=STARTER_APPLIANCE_TYPES,
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
)

_storeys = (
    Storey(uid="STBASEAAAA", tag="basement", elevation=ft(-9),
           default_ceiling_height=ft(9)),
    Storey(uid="STMAINAAAA", tag="main", elevation=ft(0),
           default_ceiling_height=ft(9)),
    # The garage storey *is* the stem top: its wood walls bear there. The stem tops out
    # GARAGE_STEM_REVEAL above *grade*, not above the house datum, because the garage is
    # driven into off the ground and the ground is 2'-6" below the main floor. The slab it
    # floors stays down at grade, one GARAGE_STEM_REVEAL below this storey — which is why
    # the overhead door carries a negative sill (plan/storeys/garage.py).
    Storey(uid="STGARAAAAA", tag="garage",
           elevation=ft(foundations.SITE_GRADE.feet + garage.GARAGE_STEM_REVEAL.feet),
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
        [*basement.ELEMENTS, *fixtures.BASEMENT_FIXTURES,
         *sunken_garden.BASEMENT_ELEMENTS,
         *raised_garden.BASEMENT_ELEMENTS, *foundations.BASEMENT_ELEMENTS,
         *mep.BASEMENT_ELEMENTS, *electrical.BASEMENT_ELEMENTS,
         *lighting.BASEMENT_LIGHTING,
         *placeables.BASEMENT_PLACEABLES],
    )
    .with_elements(
        "main",
        [*main.ELEMENTS, *fixtures.MAIN_FIXTURES, *fixtures.PORCH_HYDRANT,
         *sunken_garden.MAIN_ELEMENTS,
         *breezeway.MAIN_ELEMENTS, *mep.MAIN_ELEMENTS,
         *electrical.MAIN_ELEMENTS, *lighting.MAIN_LIGHTING,
         *placeables.MAIN_PLACEABLES, *views.DETAIL_SLICES,
         *wind_clamps.MAIN_WIND_CLAMPS],
    )
    .with_elements("garage", [*garage.ELEMENTS, *foundations.GARAGE_ELEMENTS,
                              *electrical.GARAGE_ELEMENTS,
                              *fixtures.GARAGE_FIXTURES,
                              *lighting.GARAGE_LIGHTING,
                              *placeables.GARAGE_PLACEABLES,
                              *wind_clamps.GARAGE_WALL_WIND_CLAMPS,
                              *wind_clamps.GARAGE_ROOF_WIND_CLAMPS])
    .with_elements("second", [*second.ELEMENTS, *fixtures.SECOND_FIXTURES,
                                *fixtures.BALCONY_HYDRANT,
                                *sunken_garden.SECOND_ELEMENTS, *mep.SECOND_ELEMENTS,
                                *electrical.SECOND_ELEMENTS, *lighting.SECOND_LIGHTING,
                                *placeables.SECOND_PLACEABLES,
                                *wind_clamps.SECOND_WIND_CLAMPS])
    .with_elements("attic", [*attic.ELEMENTS, *roof_trim.ATTIC_ELEMENTS,
                             *mep.ATTIC_ELEMENTS, *electrical.ATTIC_ELEMENTS,
                             *solar.ATTIC_ELEMENTS, *lighting.ATTIC_LIGHTING,
                             *placeables.ATTIC_PLACEABLES,
                             *wind_clamps.ATTIC_WIND_CLAMPS])
)
