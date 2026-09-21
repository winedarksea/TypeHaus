"""Every leaf package in the engine, and the one file that says so.

Five packages are leaves, each for its own stated reason, and each rule used to live in its
own module: ``routing``/``engineering``/``analytical``, ``schedule``, ``joints``,
``hardware``. Four modules, four copies of the same AST walk, and — because the two
"nothing upstream reaches for me" sweeps each re-parse ``checks``/``resolve``/``takeoff``/
``emit``/``source``/``model`` — the whole source tree parsed twice over. Merged here so it
is parsed once: ``_typehaus_imports`` is cached, and one module is one worker under
``--dist loadfile``, which is what makes the cache reach.

The rules themselves are unchanged, and each keeps the prose that justifies it:

* **``routing`` proposes and never grades.** A search result is not a fact about the
  building, and a ``Finding`` whose verdict moves when a cost weight moves is not a
  finding. So nothing in ``checks/``, ``resolve/``, ``takeoff/`` or ``emit/`` may reach for
  a route, and ``routing`` may not reach back into them.
* **``engineering`` computes and never checks.** Its output is an ``EngineeringRecord`` —
  demand, capacity, ratio, governing limit state, citation — and ``Finding`` has nowhere to
  hold numbers. ``checks/_authoring.engineered()`` is the one bridge.
* **``analytical`` is the graph four readers share.** An import back into ``emit`` — or
  into ``checks``, whose Findings it is deliberately not made of — would be a cycle through
  the one file the IFC SAM, the DXF, the CSV and the PyNite script all read.
* **``schedule`` derives readiness, and readiness is not a fact about the building.** A
  visit is blocked because a ``Finding`` says a wall fails, not because this package decided
  anything about the wall. A verdict that moved when a sub rescheduled would not be a
  verdict.
* **``joints`` locates a fact.** A joint is a connection of some role at some point; a BOM
  row, a ``Finding`` and a marker solid are three readings of that one fact. A locator that
  could see any of them would be tempted to answer differently for each.
* **``hardware`` is products and rules, not buildings.** What a Simpson part *is* — its
  role, its allowable, the report the number was read out of — lived in ``takeoff/`` while
  ``checks/structural``, ``emit/draw``, ``joints/`` and ``schedule/handoff`` already
  imported it: a layering inversion that compiled.

The walk is over the AST rather than over ``sys.modules``: a lazy import inside a function
is still an import, and hiding a dependency behind ``def`` would be exactly the way these
rules get broken by somebody who means well. ``routing/obstacles.py`` imports
``resolve.mep_queries`` inside a function for start-up cost, and
``hardware/catalog.py`` imports ``library.hardware`` inside one to break the catalog/items
cycle — a rule that could not see either would be worth nothing.
"""

from __future__ import annotations

import ast
import pathlib
from functools import cache

import pytest

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus"

#: What each leaf may reach. Everything under ``typehaus`` outside its set is forbidden;
#: third-party and stdlib imports are not this test's business.
#:
#: ``schedule``'s set deliberately omits ``checks``: the package reads
#: ``checks.jurisdiction`` (an inspection is *data* on a profile) and is excused for exactly
#: that below, module by module, so nobody can reach the check registry by widening one line.
#: ``hardware`` joined ``schedule``'s set when the hardware tables were promoted out of
#: ``takeoff``: ``handoff.py`` was already reading them as ``takeoff.hardware_config``, so
#: this is the same dependency spelled honestly — and a strictly weaker one.
_ALLOWED: dict[str, set[str]] = {
    # ``loads`` is a top-level leaf of published design loads, the same class of thing as
    # ``wind``/``wind_tables``: pure data both ``checks`` and ``engineering`` must read, and
    # neither may import the other to get it. Added 2026-09-18, when the deck design load
    # stopped existing in three hand-synchronised copies.
    "analytical": {"model", "resolve", "quantities", "engineering", "wind", "wind_tables",
                   "loads", "findings", "analytical"},
    "routing": {"model", "resolve", "quantities", "routing"},
    "engineering": {"model", "resolve", "quantities", "wind", "wind_tables", "loads",
                    "engineering", "findings"},
    "schedule": {"model", "resolve", "quantities", "findings", "takeoff", "emit",
                 "schedule", "hardware"},
    "joints": {"model", "resolve", "quantities", "hardware", "joints"},
    #: ``library`` for the catalog items, the same split as ``Material`` /
    #: ``library/materials.py``; nothing else under ``typehaus``.
    "hardware": {"library", "hardware"},
}

#: Named and excused, with the reason, rather than silently permitted by a loose rule.
#: Every entry is a leaf reaching another leaf — never a package that reaches back — and the
#: "nothing upstream" tests are what keep that true in the other direction.
_EXCUSED: dict[str, set[str]] = {
    # One shape for one idea. ``Oracle`` is a frozen dataclass of three strings, and a
    # second copy of it here would mean the calc package and the router describing "who
    # checked this independently" in two different vocabularies.
    "routing/oracle.py": {"engineering"},
    # ** A PUBLISHED ALLOWABLE HAS ONE HOME AND IT IS `hardware/catalog`. **
    # ``lateral_system`` grades a shear panel's overturning against the uplift its hold-down
    # actually publishes — on catlin the ABU66SS standoff base already under each 6x6, 2,190
    # lb per ICC-ES ESR-1622 as extended by Simpson's stainless letter. The alternative was
    # to have the house author that number on ``ShearPanelSpec`` beside the product name,
    # which is two places for one fact and the exact drift ``hardware/catalog`` exists to
    # stop: a spec quoting 2,190 would keep quoting it after the catalog's own row was
    # re-read. ``hardware`` is itself a leaf (``library`` and nothing else), so this is a
    # leaf reaching a leaf — the same shape ``joints`` and ``schedule`` already have, and it
    # cannot become a cycle.
    "engineering/lateral_system.py": {"hardware"},
    # The same excuse for the same reason: a deck tie grades against the tie part's own
    # published F1/F2, which live in the catalog and nowhere else.
    "engineering/deck_tie.py": {"hardware"},
    # ``value_source`` is the dialect printer. A proposal has to be dialect-legal BY
    # CONSTRUCTION — 1-tuple commas, no operators, no frozenset — and a second printer in
    # this package would be a second definition of what the dialect accepts, drifting from
    # the one the loader actually enforces.
    "routing/proposal.py": {"source"},
    # ``InspectionSpec`` lives beside ``PermitItemSpec`` because the two are the same kind
    # of thing — a jurisdiction's own declared list — and a second copy of the shape here
    # would be a second definition of what a jurisdiction requires.
    "schedule/model.py": set(),
    "schedule/inspection_state.py": {"checks"},
    "schedule/milestones.py": set(),
    "schedule/readiness.py": set(),
}

#: Who may NOT reach for a given leaf, and the sentence that says why not.
_UPSTREAM = {
    "routing": (("checks", "resolve", "takeoff", "emit", "source", "model"),
                "only cli/ may import typehaus.routing — a search result is not a Finding"),
    "schedule": (("checks", "resolve", "takeoff", "emit", "source", "model",
                  "routing", "engineering"),
                 "only cli/ and server/ may import typehaus.schedule — a readiness state "
                 "is not a fact about the building"),
}


@cache
def _typehaus_imports(path: pathlib.Path) -> frozenset[str]:
    """Every ``typehaus.<top>`` a module names, from anywhere in the file.

    Cached, and returning a frozenset so a caller cannot mutate the cached value: the two
    upstream sweeps below walk overlapping trees and were parsing the same files twice.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] == "typehaus" and len(parts) > 1:
                found.add(parts[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "typehaus" and len(parts) > 1:
                    found.add(parts[1])
    return frozenset(found)


@pytest.mark.parametrize("package", sorted(_ALLOWED))
def test_the_package_is_a_leaf(package: str) -> None:
    root = _SRC / package
    assert root.is_dir(), f"typehaus.{package} is not a package"
    offences: list[str] = []
    for path in sorted(root.rglob("*.py")):
        allowed = _ALLOWED[package] | _EXCUSED.get(str(path.relative_to(_SRC)), set())
        for top in sorted(_typehaus_imports(path) - allowed):
            offences.append(f"{path.relative_to(_SRC)} imports typehaus.{top}")
    assert not offences, (
        f"typehaus.{package} is a leaf and may import only "
        f"{sorted(_ALLOWED[package])}:\n  " + "\n  ".join(offences))


def test_the_rebar_layout_is_a_leaf_of_resolve() -> None:
    """``resolve/rebar`` reads the model and resolved records and nothing else (decision #75).

    It sits inside ``resolve`` so the pipeline can run it, but a layout that reached for
    ``takeoff``, ``checks`` or ``engineering`` would make a bar's position depend on a bill
    or a verdict. Only ``pipeline.py`` and ``model.py`` (for the record type) may name it
    from the rest of ``resolve``.
    """
    root = _SRC / "resolve" / "rebar"
    offences = [f"{path.relative_to(_SRC)} imports typehaus.{top}"
                for path in sorted(root.rglob("*.py"))
                for top in sorted(_typehaus_imports(path) - {"model", "quantities", "resolve"})]
    assert not offences, "\n  ".join(offences)
    reachers = []
    for path in sorted((_SRC / "resolve").rglob("*.py")):
        if root in path.parents or path.name in ("pipeline.py", "model.py"):
            continue
        if "typehaus.resolve.rebar" in path.read_text():
            reachers.append(str(path.relative_to(_SRC)))
    assert not reachers, reachers


@pytest.mark.parametrize("leaf", sorted(_UPSTREAM))
def test_nothing_upstream_reaches_for_the_leaf(leaf: str) -> None:
    """The other direction, and the more important one.

    A check that consulted a router would be reporting a search result as a fact about the
    building. ``cli/`` is the one place ``checks`` and ``routing`` meet, and it sits above
    both, which is what keeps the leaf rule true rather than merely stated.
    """
    packages, why = _UPSTREAM[leaf]
    offenders: list[str] = []
    for package in packages:
        for path in sorted((_SRC / package).rglob("*.py")):
            if leaf in _typehaus_imports(path):
                offenders.append(str(path.relative_to(_SRC)))
    assert not offenders, f"{why}:\n  " + "\n  ".join(offenders)


def test_a_checks_import_names_only_the_jurisdiction_module() -> None:
    """The one excused ``checks`` edge in ``schedule`` must stay ``checks.jurisdiction``.

    Reaching ``checks.registry`` or ``checks.run`` from here would make a readiness state
    depend on running the checks, which is how "derived" quietly becomes "computed".
    """
    offenders: list[str] = []
    for path in sorted((_SRC / "schedule").rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            module = getattr(node, "module", None) if isinstance(node, ast.ImportFrom) else None
            if module and module.startswith("typehaus.checks") \
                    and not module.startswith("typehaus.checks.jurisdiction"):
                offenders.append(f"{path.relative_to(_SRC)} imports {module}")
    assert not offenders, "\n  ".join(offenders)


def test_the_locators_left_takeoff() -> None:
    """The point of the ``joints`` move: a joint is locatable from outside a bill of
    materials.

    ``resolve`` is upstream of ``takeoff`` and cannot import it, so while these functions
    lived there a derived tie could be specified, billed and graded — and never drawn. If
    one comes back, the marker stage silently loses its source of truth and starts agreeing
    with a second derivation instead of the first.
    """
    moved = {
        "takeoff/uplift.py": ["def bearing_connections(", "def bearing_line_tags(",
                              "class BearingSupport", "class BearingConnection"],
        "takeoff/hangers.py": ["def hung_connections(", "class CarryingElement",
                               "class HungConnection"],
        "takeoff/uplift_joints.py": ["def tags_covered_by(", "def authored_joints(",
                                     "def bears_on_concrete(", "def is_squash_block("],
        "takeoff/anchors.py": ["def strap_holdown_locations("],
    }
    offences = []
    for name, symbols in moved.items():
        text = (_SRC / name).read_text()
        offences += [f"{name} defines {symbol!r} again" for symbol in symbols
                     if symbol in text]
    assert not offences, (
        "these belong in typehaus.joints — a second definition is a second answer:\n  "
        + "\n  ".join(offences))


@pytest.mark.parametrize("module", ["config", "catalog", "plan_geometry"])
def test_the_promoted_hardware_modules_are_where_they_say_they_are(module: str) -> None:
    """No compatibility shim was left behind in ``takeoff/``.

    ``AGENTS.md`` §3 blesses the break: a shim would keep the inversion alive at the one
    place a reader would look to find out whether it was fixed.
    """
    assert (_SRC / "hardware" / f"{module}.py").is_file()
    stale = {"config": "hardware_config", "catalog": "hardware_catalog",
             "plan_geometry": "plan_geometry"}[module]
    assert not (_SRC / "takeoff" / f"{stale}.py").exists(), (
        f"takeoff/{stale}.py is back — import typehaus.hardware.{module} instead")
