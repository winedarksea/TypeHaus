"""Which hand-worked note independently verifies which part of this package.

The root ``CLAUDE.md`` rule is that every calculation is oracled against a note somebody
worked by hand, and that a calc which only agrees with itself is not verified. The
engineering tier states that as data (``engineering/registry.oracled_by``) so the calc
package can print it beside a result; this is the same declaration for the router, reusing
the same :class:`~typehaus.engineering.item.Oracle` record rather than inventing a second
shape for one idea.

``tests/test_calc_package.py`` lints that every engineering kind names a note that exists
on disk. Its sibling here does the same walk over :data:`ORACLES`, so a module added to
this package without a note fails a test rather than passing quietly.
"""

from __future__ import annotations

from typehaus.engineering.item import Oracle

#: Module name (without the package prefix) -> the notes that verify it.
#:
#: A module absent from this map is a module nothing independently checks, which is
#: exactly what the lint reports. The two that are deliberately absent are named below.
ORACLES: dict[str, tuple[Oracle, ...]] = {
    "gravity": (Oracle(note="mep_drain_routing_basis.md", section="§2",
                       test="tests/test_routing_oracle.py"),),
    "corridors": (Oracle(note="mep_drain_routing_basis.md", section="§3",
                         test="tests/test_routing_oracle.py"),
                  Oracle(note="mep_duct_routing_basis.md", section="§3",
                         test="tests/test_routing_oracle.py")),
    "graph": (Oracle(note="mep_drain_routing_basis.md", section="§4",
                     test="tests/test_routing_oracle.py"),),
    "search": (Oracle(note="mep_drain_routing_basis.md", section="§4",
                      test="tests/test_routing_oracle.py"),),
    "tree": (Oracle(note="mep_drain_routing_basis.md", section="§5",
                    test="tests/test_routing_oracle.py"),),
    "trades/duct": (Oracle(note="mep_duct_routing_basis.md", section="§1, §3",
                           test="tests/test_routing_oracle.py"),),
}

#: Modules that compute nothing and so oracle nothing, named so their absence is a
#: statement rather than a gap: ``space`` and ``obstacles`` assemble geometry the resolved
#: model already carries, ``cost`` is a table of house preferences, ``proposal`` is a
#: printer, and ``trades/{pipe,conduit}`` are adapters over the modules above.
NOT_A_CALCULATION = frozenset({
    "__init__", "space", "obstacles", "cost", "proposal", "oracle",
    "trades/__init__", "trades/pipe", "trades/conduit",
})


def oracles_for(module: str) -> tuple[Oracle, ...]:
    return ORACLES.get(module, ())
