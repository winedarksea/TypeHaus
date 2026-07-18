"""Catlin house manifest — the real house, four structures, one plan (WP3.1).

Structures (all in the shared project-north frame, house sheathing SW corner at 0,0):
- House: 36'x36' at sheathing; basement / main / second / attic storeys.
- Garage: freestanding 24'x24' ICF stem + 2x6 walls, 12' north of the house
  (its own ``garage`` storey at the stem top elevation).
- Sunken garden / porch / balcony: one freestanding arched concrete structure,
  5" south of the house (params/sunken_garden.py).
- Breezeway: roof on freestanding 6x6 posts between house and garage
  (params/foundations.py; posts + pads now, roof with WP3.11).

This file is NOT ``# haus: editable``: it is the plain-Python assembler. The engine
reads ``format_version``/``requires_engine`` via the dialect path (AST, no import).
"""

from __future__ import annotations

import uuid

from typehaus import Building, Library, PlanModel, Project, Storey, ft

from params import foundations, sunken_garden
from plan import assemblies, site
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
)

_project = Project(
    name="Catlin House",
    project_uuid=PROJECT_UUID,
    site=site.SITE,
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
    Storey(uid="STSECDAAAA", tag="second", elevation=ft(9),
           default_ceiling_height=ft(9)),
    Storey(uid="STATTCAAAA", tag="attic", elevation=ft(18),
           default_ceiling_height=ft(11)),
)

PLAN = (
    PlanModel(project=_project, library=_library, storeys=_storeys)
    .with_elements(
        "basement",
        [*basement.ELEMENTS, *sunken_garden.BASEMENT_ELEMENTS,
         *foundations.BASEMENT_ELEMENTS],
    )
    .with_elements(
        "main",
        [*main.ELEMENTS, *sunken_garden.MAIN_ELEMENTS, *foundations.MAIN_ELEMENTS],
    )
    .with_elements("garage", [*garage.ELEMENTS])
    .with_elements("second", [*second.ELEMENTS, *sunken_garden.SECOND_ELEMENTS])
    .with_elements("attic", [*attic.ELEMENTS])
)
