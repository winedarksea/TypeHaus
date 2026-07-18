"""Shared test fixtures (→ AGENTS.md §3 shared fixtures)."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
STARTER = REPO_ROOT / "houses" / "starter"

# The shared ``library`` package lives at the repo root; make it importable for tests that
# reference it directly (the loader discovers it on its own for plan imports).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def starter_dir() -> Path:
    return STARTER


@pytest.fixture
def project():
    from typehaus.model import Building, Project, Site, degF, ft

    return Project(
        name="test", project_uuid=uuid.UUID("00000000-0000-4000-8000-000000000abc"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15)),
        building=Building(name="T"),
    )


@pytest.fixture
def wall_assembly():
    from typehaus.model import (
        Assembly,
        FramingSpec,
        Layer,
        LayerFunction,
        Material,
        inch,
    )

    materials = (
        Material(tag="spf", name="SPF", r_per_inch=1.25),
        Material(tag="gwb", name="GWB", r_per_inch=0.9),
    )
    asm = Assembly(
        tag="EXT", layers=(
            Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        ),
        default_lining=(Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
                              function=LayerFunction.FINISH),),
    )
    return materials, asm
