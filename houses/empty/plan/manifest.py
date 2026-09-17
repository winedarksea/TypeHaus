"""Empty house manifest — one storey with no walls yet, for drawing from scratch.

NOT ``# haus: editable``: the plain-Python assembler. The storey is wired here, so
``plan/storeys/main.py`` carries no ``STOREY =`` of its own.
"""

from __future__ import annotations

import uuid

from typehaus import Building, Library, PlanModel, Project, Storey, ft
from typehaus.library import (
    STARTER_APPLIANCE_TYPES,
    STARTER_FIXTURE_TYPES,
    STARTER_FURNITURE_TYPES,
)

from plan import assemblies, placeables, site
from plan.storeys import main

format_version = 1
requires_engine = ">=0.1,<0.2"

# Generated once by `haus new`; retained in source forever.
PROJECT_UUID = uuid.UUID("6f6e0000-0000-4000-8000-000000000002")

_library = Library(
    materials=tuple(assemblies.MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    door_types=tuple(main.DOOR_TYPES),
    window_types=tuple(main.WINDOW_TYPES),
    furniture_types=tuple(STARTER_FURNITURE_TYPES),
    fixture_types=tuple(STARTER_FIXTURE_TYPES),
    appliance_types=tuple(STARTER_APPLIANCE_TYPES),
)

_project = Project(
    name="Type:Haus Empty",
    project_uuid=PROJECT_UUID,
    site=site.SITE,
    building=Building(name="Empty House"),
    format_version=format_version,
    requires_engine=requires_engine,
)

_storeys = (
    Storey(uid="STMAINAAAA", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),
)

PLAN = PlanModel(project=_project, library=_library, storeys=_storeys).with_elements(
    "main",
    [*main.NODES, *main.WALLS, *main.OPENINGS, *main.ROOMS, *placeables.MAIN_PLACEABLES],
)
