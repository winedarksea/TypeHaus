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
                       test="tests/test_routing_oracle.py"),
                # -- W3-SLOPE --
                # Condensate: 1/4 target, IMC 307.2.1 floor 1/8; PR-M-COND-HEADS 8.000 ft owes
                # 2.000 / 1.500 / 1.000" at 1/4 / 3/16 / 1/8, and the penalty picks (§5.1).
                Oracle(note="mep_condensate_routing_basis.md", section="§4, §5, §5.1, §8",
                       test="tests/test_routing_minor_systems.py"),
                # -- /W3-SLOPE --
                Oracle(note="mep_drain_routing_basis.md", section="§14",
                       test="tests/test_routing_trap_vent.py"),),
    "corridors": (Oracle(note="mep_drain_routing_basis.md", section="§3",
                         test="tests/test_routing_oracle.py"),
                  Oracle(note="mep_duct_routing_basis.md", section="§3",
                         test="tests/test_routing_oracle.py")),
    "graph": (Oracle(note="mep_drain_routing_basis.md", section="§4",
                     test="tests/test_routing_oracle.py"),
              Oracle(note="mep_drain_routing_basis.md", section="§11",
                     test="tests/test_routing_supply.py"),
              Oracle(note="mep_duct_routing_basis.md", section="§5",
                     test="tests/test_routing_graph.py"),
              # A port stub's tip loses its lattice step back toward the port (no 180).
              Oracle(note="mep_drain_routing_basis.md", section="§11",
                     test="tests/test_routing_port_lead.py")),
    "search": (Oracle(note="mep_drain_routing_basis.md", section="§4",
                      test="tests/test_routing_oracle.py"),
               Oracle(note="vent_grade_basis.md", section="§5",
                      test="tests/test_routing_vent.py"),
               Oracle(note="mep_drain_routing_basis.md", section="§11",
                      test="tests/test_routing_supply.py")),
    "tree": (Oracle(note="mep_drain_routing_basis.md", section="§5",
                    test="tests/test_routing_oracle.py"),),
    "alternatives": (Oracle(note="mep_drain_routing_basis.md", section="§7",
                            test="tests/test_routing_alternatives.py"),),
    "gravity_search": (Oracle(note="mep_drain_routing_basis.md", section="§8",
                              test="tests/test_gravity_search.py"),
                       Oracle(note="mep_drain_routing_basis.md", section="§13",
                              test="tests/test_gravity_search.py"),),
    "gravity_band": (Oracle(note="mep_drain_routing_basis.md", section="§8a",
                            test="tests/test_gravity_search.py"),
                     Oracle(note="mep_drain_routing_basis.md", section="§13",
                            test="tests/test_gravity_search.py"),),
    "gravity_webs": (Oracle(note="framing_bore_limits.md", section="§13",
                            test="tests/test_gravity_search.py"),
                     Oracle(note="framing_bore_limits.md", section="§13",
                            test="tests/test_open_web_shape.py"),),
    "compaction": (Oracle(note="mep_drain_routing_basis.md", section="§10",
                          test="tests/test_routing_compaction.py"),),
    "fitting_room": (Oracle(note="mep_drain_routing_basis.md", section="§10",
                            test="tests/test_routing_compaction.py"),),
    "trap_vent": (Oracle(note="mep_drain_routing_basis.md", section="§9",
                         test="tests/test_routing_trap_vent.py"),
                  Oracle(note="mep_drain_routing_basis.md", section="§14",
                         test="tests/test_routing_trap_vent.py"),),
    "rack": (Oracle(note="mep_drain_routing_basis.md", section="§12",
                    test="tests/test_routing_supply.py"),),
    "members": (Oracle(note="framing_bore_limits.md", section="§10",
                       test="tests/test_routing_members.py"),),
    "holes": (Oracle(note="framing_bore_limits.md", section="§10, §11, §14",
                     test="tests/test_routing_hole_spacing.py"),),
    "floor_bars": (Oracle(note="framing_bore_limits.md", section="§15",
                          test="tests/test_routing_members.py"),),
    "trades/duct": (Oracle(note="mep_duct_routing_basis.md", section="§1, §3",
                           test="tests/test_routing_oracle.py"),),
    "corridor_lanes": (Oracle(note="mep_duct_routing_basis.md", section="§3",
                              test="tests/test_corridor_lanes.py"),),
    # -- E0 --
    # -- /E0 --
    # -- E1 --
    "tree_ripup": (Oracle(note="mep_tree_ripup_basis.md", section="§1, §2",
                          test="tests/test_routing_tree_ripup.py"),),
    "gravity_grid": (Oracle(note="mep_drain_routing_basis.md", section="§13",
                            test="tests/test_gravity_search.py"),),
    # -- /E1 --
    # -- E2 --
    "group_order": (Oracle(note="mep_group_wet_vent_basis.md", section="§3, §4, §5",
                           test="tests/test_routing_group.py"),),
    # -- /E2 --
    # -- E3 --
    "duct_fittings": (Oracle(note="mep_duct_routing_basis.md", section="§7, §8",
                             test="tests/test_routing_duct_fittings.py"),),
    "duct_search": (Oracle(note="mep_duct_routing_basis.md", section="§7.2",
                           test="tests/test_routing_duct_fittings.py"),),
    # -- /E3 --
    # -- E4 --
    "supply_tree": (Oracle(note="mep_supply_trunk_basis.md", section="§2, §4, §5",
                           test="tests/test_routing_supply_tree.py"),
                    # Riser stations as gate holes; a served body excuses a riser in it.
                    Oracle(note="mep_supply_trunk_basis.md", section="§5a",
                           test="tests/test_routing_riser_terminal.py"),),
    # -- /E4 --
    # -- E5 --
    # -- /E5 --
}

#: Modules that compute nothing and so oracle nothing, named so their absence is a
#: statement rather than a gap: ``space`` and ``obstacles`` assemble geometry the resolved
#: model already carries, ``cost`` is a table of house preferences, ``proposal`` is a
#: printer, ``timing`` is a stopwatch, ``diagnostics`` reads back the space the
#: search was given, and ``trades/{pipe,conduit}`` are adapters over the modules above.
#:
#: ``counterfactual`` is the one that deserves a sentence. It runs a real search and so
#: looks like a calculation, but every number it reports is the ALREADY-ORACLED search's
#: own cost over a world with one prism lifted — there is no arithmetic of its own to work
#: by hand, and a note reproducing one would be reproducing ``search``'s §4. What it adds
#: is a policy (relax only ``Mobility.MOVABLE``, one at a time, bounded), and a policy is
#: argued in prose, which its docstring does.
#:
#: ``campaign`` is the second one worth a sentence. It runs no search — ``propose`` is a
#: parameter — and every route it reports is the already-oracled search's own. What it adds
#: is an ORDER and a rip-up policy, and an order is argued rather than worked: a note
#: reproducing "drains first, deepest first" by hand would be reproducing the sentence that
#: chose it. ``tests/test_routing_campaign.py`` pins the order and the policy instead.
#: ``space_view`` computes an area and so looks like a third candidate. It is not: every
#: polygon it reports is a prism ``obstacles`` already built, classified by the mapping
#: ``diagnostics`` already declares, and green is derived by SUBTRACTION from the search
#: bbox — so there is no number to work by hand that is not already somebody else's. What it
#: adds is a vocabulary (four classes, each naming the action it implies), and a vocabulary
#: is argued rather than reproduced.
NOT_A_CALCULATION = frozenset({
    "__init__", "space", "obstacles", "cost", "proposal", "oracle", "timing",
    "diagnostics", "counterfactual", "campaign", "space_view",
    "graph_batch",  # vectorised queries for graph: same answers, oracled through it
    "rails",  # floor members as rails: geometry the model carries, like ``space``
    # ``blocking_parts``' own box (its constants, ``crossing_runs``' reading) over
    # ``floor_blocking.bearing_bays``: a check's rule restated, no arithmetic of its own.
    "bearing_bays",
    "terminal_block",  # a search for a clear point along a wall: geometry, no calculation
    "terminal_band",  # a vent's z band read off storey datums: a selection, no arithmetic
    "trades/__init__", "trades/pipe", "trades/conduit",
    # -- E0 --
    # -- /E0 --
    # -- E1 --
    # -- /E1 --
    # -- E2 --
    # -- /E2 --
    # -- E3 --
    # -- /E3 --
    # -- E4 --
    # -- /E4 --
    # -- E5 --
    # -- /E5 --
})


def oracles_for(module: str) -> tuple[Oracle, ...]:
    return ORACLES.get(module, ())


# -- W3-FLEX --
ORACLES["duct_fittings"] += (Oracle(note="flex_lead_bend_basis.md", section="§1-§4",
                                    test="tests/test_flex_lead_bend.py"),)
# -- /W3-FLEX --
