"""Starter house manifest — assembles the Project from editable modules + params/.

This file is NOT ``# haus: editable``: it is the plain-Python assembler that wires the
declarative modules together. The engine reads ``format_version``/``requires_engine``
from here via the dialect path (AST, no import) before ever executing it (#31).
"""

from __future__ import annotations

import uuid

from typehaus import Building, Library, PlanModel, Project, Storey, ft

from plan import assemblies, site, views
from plan.storeys import main, upper

format_version = 1
requires_engine = ">=0.1,<0.2"

# Generated once by `haus new`; retained in source forever.
PROJECT_UUID = uuid.UUID("6f6e0000-0000-4000-8000-000000000001")

_library = Library(
    materials=tuple(assemblies.MATERIALS),
    assemblies=tuple(assemblies.ASSEMBLIES),
    door_types=tuple(main.DOOR_TYPES),
    window_types=tuple(main.WINDOW_TYPES),
)

_project = Project(
    name="Type:Haus Starter",
    project_uuid=PROJECT_UUID,
    site=site.SITE,
    building=Building(name="Starter House"),
    format_version=format_version,
    requires_engine=requires_engine,
)

_storeys = (
    Storey(uid="STMAINAAAA", tag="main", elevation=ft(0), default_ceiling_height=ft(9)),
    Storey(uid="STUPPRAAAA", tag="upper", elevation=ft(9), default_ceiling_height=ft(9)),
)

PLAN = (
    PlanModel(project=_project, library=_library, storeys=_storeys)
    .with_elements(
        "main",
        [*main.NODES, *main.WALLS, *main.OPENINGS, *main.ROOMS, *main.FLOOR,
         *views.DETAIL_SLICES],
    )
    .with_elements(
        "upper",
        [*upper.NODES, *upper.WALLS, *upper.OPENINGS, *upper.ROOMS, *upper.ALARMS],
    )
)
