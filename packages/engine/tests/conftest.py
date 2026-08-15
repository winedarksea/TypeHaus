"""Shared test fixtures (→ AGENTS.md §3 shared fixtures)."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

from _helpers import CATLIN, HOUSE_IGNORE, HOUSES, REPO_ROOT, STARTER, copy_house

__all__ = ["CATLIN", "HOUSE_IGNORE", "HOUSES", "REPO_ROOT", "STARTER", "copy_house"]

# The shared ``library`` package lives at the repo root; make it importable for tests that
# reference it directly (the loader discovers it on its own for plan imports).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))



@pytest.fixture(scope="session")
def starter_dir() -> Path:
    return STARTER


@pytest.fixture(scope="session")
def catlin_plan():
    """The loaded catlin plan — once for the whole suite.

    ``PlanModel`` is a frozen pydantic model, so one instance is safe to share across
    every test that only reads it, and ``load_plan`` is the expensive half of the pair.
    Forty test modules were each paying their own full load for the same bytes.

    Tests that *mutate* house source must not take this: they copy the house to a
    ``tmp_path`` sandbox (→ ``copy_house``) and load from there, which they already do.
    """
    from typehaus.source import load_plan

    result = load_plan(CATLIN)
    assert result.plan is not None, [f.message for f in result.findings]
    errors = [f for f in result.findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return result.plan


@pytest.fixture(scope="module")
def catlin_model(catlin_plan):
    """The resolved catlin model, per test module.

    Module-scoped rather than session-scoped on purpose: ``ResolvedModel`` is a *mutable*
    dataclass with list fields, so a session-wide instance would let one module's test
    leak into another's. Re-resolving is the cheap half; the plan above is the shared one.
    """
    from typehaus.resolve import resolve

    model, findings = resolve(catlin_plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


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
