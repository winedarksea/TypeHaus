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


def pytest_addoption(parser) -> None:
    """``--bless`` rewrites stored goldens instead of asserting against them.

    Only ``test_section_goldens.py`` reads it. Deliberately a flag rather than an env var
    so it shows up in ``pytest --help`` next to the other options a contributor sees.
    """
    parser.addoption("--bless", action="store_true", default=False,
                     help="rewrite stored goldens from the current build")



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


@pytest.fixture(scope="module")
def swinburne_model(catlin_plan):
    """A two-wall L of ``CATLIN_EXT_2X6_SWINBURNE`` walls with one window.

    The Swinburne truss wall stopped being a *catlin* wall on 2026-08-26 — the house is on
    the catlin truss's horizontal girts now — but nothing about the vertical outrigger frame
    was deleted, and ``test_truss_wall_geometry.py`` is what keeps it honest. So the geometry
    tests moved off ``catlin_model`` and onto this: the smallest plan that exercises every
    piece of the pack (field outriggers on the module, a jamb outrigger and its filler, head
    and sill blocking, blocks, tabs, bucks, and one owned L corner for the corner box).

    The assembly is the REAL retired tuple, read back out of the catlin library rather than
    restated here, which is the point: this fixture is a live test of the documented revert
    (``notes/outie_window_truss_detail.md``), not of a copy that can quietly drift from it.
    Two walls rather than four because an L is all the corner box needs and a smaller plan
    resolves faster; the component has no closed loop, so ``outward_sign`` is +1 and the
    stack resolves outward in the ordinary direction (→ memory: freestanding wall outward
    sign).
    """
    from typehaus.model import (
        Building,
        Library,
        Node,
        PlanModel,
        Project,
        Site,
        Storey,
        Wall,
        Window,
        WindowType,
        degF,
        ft,
        pt,
    )
    from typehaus.model.refs import centered
    from typehaus.resolve import resolve

    assembly = catlin_plan.library.resolve_assembly("CATLIN_EXT_2X6_SWINBURNE")
    assert assembly is not None, (
        "CATLIN_EXT_2X6_SWINBURNE is the documented one-swap revert from the catlin truss; "
        "if it is gone, the revert is gone with it")
    library = Library(materials=catlin_plan.library.materials, assemblies=(assembly,),
                      window_types=(WindowType(tag="WT-SW", width=ft(3), height=ft(4),
                                               u_factor=None, shgc=0.4),))
    project = Project(name="SWIN", project_uuid="00000000-0000-4000-8000-00000000005b",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="SWIN"))
    storey = Storey(uid="ST0000005b", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = (
        # ``open_end`` on the two free ends: an L is not a loop, and without it
        # ``integrity.wall_loop_open`` errors on both. The corner at N-SE is the one this
        # fixture exists for.
        Node(uid="N00000005b1", tag="N-SW", position=pt(ft(0), ft(0)), open_end=True),
        Node(uid="N00000005b2", tag="N-SE", position=pt(ft(24), ft(0))),
        Node(uid="N00000005b3", tag="N-NE", position=pt(ft(24), ft(24)), open_end=True),
    )
    walls = (
        Wall(uid="W00000005b1", tag="W-S", start_node="N-SW", end_node="N-SE",
             assembly="CATLIN_EXT_2X6_SWINBURNE", top=ft(9)),
        Wall(uid="W00000005b2", tag="W-E", start_node="N-SE", end_node="N-NE",
             assembly="CATLIN_EXT_2X6_SWINBURNE", top=ft(9)),
    )
    window = Window(uid="WN0000005b1", tag="WIN-SW", host="W-S", type_ref="WT-SW",
                    position=centered(), sill_height=ft(3))
    plan = PlanModel(project=project, library=library, storeys=(storey,)).with_elements(
        "main", (*nodes, *walls, window))
    model, findings = resolve(plan)
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
