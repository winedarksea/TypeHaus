"""Shared test fixtures (→ AGENTS.md §3 shared fixtures)."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from _helpers import CATLIN, HOUSE_IGNORE, HOUSES, REPO_ROOT, STARTER, copy_house

__all__ = ["CATLIN", "HOUSE_IGNORE", "HOUSES", "REPO_ROOT", "STARTER", "copy_house"]

# The repo root, for tests that reach for a sibling tree (scripts/, houses/) by import.
# The shared catalog is NOT one of them any more: it ships inside the package as
# ``typehaus.library`` and resolves like any other engine module.
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


@pytest.fixture(scope="session")
def catlin_model_ro(catlin_plan):
    """The resolved catlin model, once for the whole suite — for **read-only** use.

    ``catlin_model`` below is module-scoped because ``ResolvedModel`` is mutable and one
    module's edits must not leak into another's. That is the right default, but it made the
    house resolve 112 times for a suite in which the large majority of consumers only read.
    Take this one when the test does not mutate the model (emitting, taking off, asserting
    on geometry); take ``catlin_model`` the moment it might.

    Handing this to a mutating test is the failure mode, and it is a quiet one — the damage
    lands in whatever module runs next. When in doubt use ``catlin_model``: a resolve is
    ~1.2 s idle (2026-09-24). A ``copy.deepcopy`` of the result is now about half that, but
    a copy only protects a test that remembers to take one.
    """
    from typehaus.resolve import resolve

    model, findings = resolve(catlin_plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


class _PlanWithTheBells:
    """``catlin_plan`` plus the two retired bell ``Footing``s, so ``spread_footing`` can find
    their mix (``PIER_BASE_12``, still an assembly on catlin's pads). Nothing else is read."""

    def __init__(self, plan, footings):
        self._plan = plan
        self._footings = footings

    def all_elements(self):
        return list(self._plan.all_elements()) + list(self._footings)

    def __getattr__(self, name):
        return getattr(self._plan, name)


def _retired_centre_column(tag: str, carried_dead_lb: float):
    """One of ``PT-SG-COL`` / ``PT-SG-FCOL`` as a ``_Pier``, from the note's own inputs.

    ** RETIRED FROM CATLIN 2026-09-22 ** (17'-0" court; both decks span wall to wall). The
    columns are rebuilt from ``notes/sunken_garden_piers.md`` §1-§2 so ``deck_post`` and
    ``spread_footing`` keep an oracle: 12" round, 128.1875" shaft, 119.17 ft² tributary
    (70.84 porch + 48.33 handed down by a centre pillar), the pillar's own 6x6 carried as
    dead load, (4) #5 + #3 @ 10" at 2" cover, 5,000 psi, on a 12" ``PIER_BASE_12`` pad.
    """
    from typehaus import inch
    from typehaus.engineering.pier_basis import _Pier
    from typehaus.model.rebar import BarSpec, ReinforcementSpec

    cage = ReinforcementSpec(
        bars=(BarSpec(role="vertical", bar=5, count=4),
              BarSpec(role="ties", bar=3, spacing=inch(10.0))),
        cover=inch(2.0), lap_class="B")
    return _Pier(
        tag=tag, diameter_in=12.0, round_section=True, height_in=128.1875,
        tributary_ft2=70.84 + 48.33, carried_dead_lb=carried_dead_lb,
        footing_tag=None, shared_wall_footing=False, lateral_system=False,
        wind_base_moment_lb_ft=0.0, guard_base_moment_lb_ft=0.0, moment_basis="",
        footing_width_in=0.0, footing_depth_in=0.0,
        base_thickness_in=12.0, base_kind="pad",
        vertical_reinforcement=('(4) #5 vertical, #3 ties @ 10" o.c., 2" cover, '
                                'galvanized (ASTM A767 after fabrication, or A1094)'),
        reinforcement=cage, specified_fc_psi=5000.0, specified_cover_in=2.0,
        base_fc_psi=5000.0, base_cover_in=3.0)


@pytest.fixture(scope="session")
def catlin_retired_columns():
    """The two retired centre columns on their pads, keyed by tag. §2: the rear pillar's
    6x6 is 79 lb, the front one's 78 (the rear row stands 1 27/32" proud)."""
    return {"PT-SG-COL": _retired_centre_column("PT-SG-COL", 78.71),
            "PT-SG-FCOL": _retired_centre_column("PT-SG-FCOL", 77.58)}


@pytest.fixture(scope="session")
def catlin_retired_bells(catlin_plan, catlin_retired_columns):
    """The same two columns on the 36" x 12" bells they carried until 2026-09-14.

    ``spread_footing`` is the only derivation in the engine for a bell, so its oracle
    (``notes/sunken_garden_piers.md`` §§3, 5) is kept alive on this reconstruction. The
    ``Footing``s ride on ``catlin_plan`` only so ``_section_states`` can read the mix.
    """
    import dataclasses

    from typehaus import Footing, ft, inch
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.model.structure import Post
    from typehaus.resolve import resolve

    # The guard: the day catlin grows either column back, read it off the house instead.
    assert not {e.tag for e in catlin_plan.all_elements() if isinstance(e, Post)} & set(
        catlin_retired_columns), "a retired centre column is back in catlin"

    model, _ = resolve(catlin_plan)
    footings = [
        Footing(uid=f"ZZZF19{i}AAA", tag=f"FT-{tag[3:]}", under=tag, width=inch(36.0),
                depth=inch(12.0), assembly="PIER_BASE_12", bottom_elevation=ft(-12.0))
        for i, tag in enumerate(sorted(catlin_retired_columns))]
    ctx = EngineeringContext(plan=_PlanWithTheBells(catlin_plan, footings),
                             model=model, soil_class="GM")
    piers = {tag: dataclasses.replace(pier, footing_tag=f"FT-{tag[3:]}",
                                      footing_width_in=36.0, footing_depth_in=12.0,
                                      base_kind="footing", base_fc_psi=None,
                                      base_cover_in=None)
             for tag, pier in catlin_retired_columns.items()}
    return ctx, piers


@pytest.fixture(scope="session")
def catlin_ifc_path(catlin_model_ro, tmp_path_factory) -> Path:
    """The framed-LOD catlin IFC, emitted once per xdist worker — **read-only**.

    IFC emission was the single largest cost in this suite: ~25 modules each emitted the
    *unmodified* catlin model at the default LOD, and ``--durations`` was a wall of them.
    Under ``-n 6 --dist loadfile`` a session fixture is per worker, so this collapses those
    to six emissions.

    Open it, never write to it — every test that takes this shares one file on disk. A test
    that emits a *mutated* model, another house, or a non-default LOD must call ``emit_ifc``
    itself; so must ``test_ifc_openings.py``'s self-diff, which emits twice on purpose.
    """
    from typehaus.emit.ifc import emit_ifc

    out = tmp_path_factory.mktemp("catlin-ifc") / "catlin.ifc"
    return emit_ifc(catlin_model_ro, out)


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


@pytest.fixture(scope="session")
def catlin_areas(catlin_model_ro):
    """The $/sf denominators, and what a ``space_summary.*`` allowance driver reads.

    Every production caller of ``estimate_costs`` passes these (see
    ``server/space_summary.estimate_areas``), because catlin drives two allowances off
    gross and conditioned area. A test that prices catlin's real ``prices.toml`` without
    them is testing a call shape nothing makes any more — and gets a ValueError saying so,
    which is the intended failure: a driven quantity must never quietly become zero.
    """
    from typehaus.server.space_summary import estimate_areas

    return estimate_areas(catlin_model_ro)


@pytest.fixture(scope="module")
def swinburne_model(catlin_plan):
    """A two-wall L of ``EXT_2X6_SWINBURNE`` walls with one window.

    The Swinburne truss wall is no longer a *catlin* wall — the house is on the catlin
    truss's horizontal girts now — but the vertical outrigger frame it defines is still
    real, and ``test_truss_wall_geometry.py`` keeps it honest via this smallest plan that
    exercises every piece of the pack (field outriggers on the module, a jamb outrigger and
    its filler, head and sill blocking, blocks, tabs, bucks, and one owned L corner).

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

    assembly = catlin_plan.library.resolve_assembly("EXT_2X6_SWINBURNE")
    assert assembly is not None, (
        "EXT_2X6_SWINBURNE is the documented one-swap revert from the catlin truss; "
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
             assembly="EXT_2X6_SWINBURNE", top=ft(9)),
        Wall(uid="W00000005b2", tag="W-E", start_node="N-SE", end_node="N-NE",
             assembly="EXT_2X6_SWINBURNE", top=ft(9)),
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


# --------------------------------------------------------------------------------------
# The expensive compositions, shared.
#
# A full ``run()`` on catlin is ~20 s and does not get cheaper on a repeat; composing the
# sheet index was ~19 s of hidden check run until ``build_sheet_index`` learned to take a
# report. Both were being paid dozens of times over for the same bytes (→ AGENTS.md §3:
# take the highest-scoped fixture you can).
#
# **Scoping rule.** Under ``-n 6 --dist loadfile`` a session fixture is built once *per
# worker*, and loadfile keeps a whole module on one worker. So a session fixture used by
# two modules or fewer saves nothing over module scope and only widens the window for a
# cross-module leak. Prefer module scope there.
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def catlin_ctx(catlin_plan):
    """``build_context(catlin_plan, CATLIN)[0]`` — once per worker, **read-only**.

    Holds the same mutable ``ResolvedModel`` that ``catlin_model_ro`` does, and carries the
    same rule in the same words: take this when the test does not mutate the model, and
    build your own context the moment it might. ``run_checks`` does not mutate it.

    ``ctx.engineering`` memoises each record on first read, which is *why* sharing pays:
    the engineering suite is computed once for every module that grades against it rather
    than once per test.

    Two contexts must NOT take this and build their own instead, for reasons that are about
    correctness and not about speed:

    * a test that edits ``ctx.model`` (``test_member_interference.py`` has one);
    * a test that asserts the results map is still lazy (``ctx.engineering._records == {}``)
      — this fixture has been read by then, so the map is populated;
    * any call with an explicit ``profile=``, or with no ``house_dir`` at all. Neither is
      this context: the first resolves a different jurisdiction, the second an empty
      ``Preferences`` and so a different suppression set.
    """
    from typehaus.checks.run import build_context

    ctx, _ = build_context(catlin_plan, CATLIN)
    return ctx


@pytest.fixture(scope="session")
def catlin_check_report(catlin_ctx):
    """A ``report(tier=None)`` **factory**, memoised per tier — once per worker.

    A factory rather than a value because ``tier`` varies across the suite and a re-run
    costs the full ~20 s; memoising on the tier gives every caller the value it asked for
    at the price of the first one.

    ``run(plan, house_dir, tier=t)`` *is* ``build_context(plan, house_dir)`` +
    ``run_checks(ctx, t)`` (``checks/run.py``), so what comes back is value-identical to
    what an un-fixtured call site computed for itself.

    ``CheckReport.findings`` is a plain list and this one is shared: read it, never sort or
    append to it. Do not take this for a call carrying an explicit ``profile=`` or no
    ``house_dir`` — see ``catlin_ctx`` for why those are different reports, not cheaper ones.
    """
    from typehaus.checks.registry import run_checks

    cache: dict[object, object] = {}

    def report(tier=None):
        if tier not in cache:
            cache[tier] = run_checks(catlin_ctx, tier)
        return cache[tier]

    return report


@pytest.fixture(scope="session")
def catlin_model_report(catlin_model_ro):
    """``run_from_model(catlin_model_ro, [], None)`` — the registry with **no house_dir**.

    Not the same report as ``catlin_check_report()``: with no directory there are no loaded
    ``Preferences``, so a different suppression set and a different jurisdiction. This is
    the one a bare ``build_sheet_index(model)`` computes for itself, and it exists so the
    composition can be handed it instead (→ ``catlin_sheet_index``).

    Shared and read-only, like every report here.
    """
    from typehaus.checks import run_from_model

    return run_from_model(catlin_model_ro, [], None)


@pytest.fixture(scope="session")
def catlin_sheet_index(catlin_model_ro, catlin_model_report):
    """An ``index(sets="full", details=None, paper=LEDGER)`` factory — tuples, read-only.

    Composed against ``catlin_model_ro``, which is why a module converting to this fixture
    converts to that model in the same change: the derived-detail specs close over slices
    built from the model they were composed against, and rendering a spec against a
    *different* model quietly mixes two.

    Returns a ``tuple``, not the list ``build_sheet_index`` returns. ``SheetSpec`` is frozen
    but the list was not, and one ``.sort()`` in one test would poison every later module on
    that worker. Every call site is tuple-compatible.

    The registry runs once, in ``catlin_model_report``, and is handed to every variant as
    ``report=`` — that is the same answer each call would have computed for itself (same
    model, same absent ``house_dir``), and it is what makes a composition 0.3 s, not 19 s.

    A call passing ``preferences=`` or ``house_dir=`` is not this fixture: both change what
    is composed, and a ``Preferences`` memo key would be a fragile one. Call the function.
    """
    from typehaus.emit.draw.sheet_writer import LEDGER
    from typehaus.emit.draw.sheets import build_sheet_index

    cache: dict[object, tuple] = {}

    def index(sets: str = "full", details: str | None = None, paper=LEDGER) -> tuple:
        key = (sets, details, tuple(paper))
        if key not in cache:
            cache[key] = tuple(build_sheet_index(catlin_model_ro, details=details,
                                                 paper=paper, sets=sets,
                                                 report=catlin_model_report))
        return cache[key]

    return index


@pytest.fixture(scope="session")
def catlin_details(catlin_model_ro):
    """``{key: (derived, scene, findings)}`` for every derived detail — once per worker.

    Genuinely immutable, unlike the fixtures above: ``DerivedDetail`` is a frozen dataclass
    and ``Scene``/IR are frozen pydantic. Share freely.

    Five modules were each sweeping all ~76 details, and one of them swept them five times
    over because its helper was uncached.
    """
    from typehaus.emit.draw.detail_derive import derive_detail_slices
    from typehaus.emit.draw.details import build_detail

    out = {}
    for derived in derive_detail_slices(catlin_model_ro):
        scene, findings = build_detail(catlin_model_ro, derived)
        out[derived.key] = (derived, scene, findings)
    return out


@pytest.fixture(scope="module")
def catlin_permit_set(catlin_model_ro, catlin_model_report, tmp_path_factory):
    """``(path, composed)`` from one ``write_permit_set`` — **module** scope, read-only.

    Module rather than session on purpose: only two modules consume it, and under
    ``--dist loadfile`` that makes session scope pure downside (see the scoping rule above).

    A real multi-page PDF on disk. Open it, never write to it.
    """
    from typehaus.emit.draw import write_permit_set

    out = tmp_path_factory.mktemp("catlin-permit-set") / "permit_set.pdf"
    return write_permit_set(catlin_model_ro, out, report=catlin_model_report)
