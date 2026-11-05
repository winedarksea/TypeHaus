"""Wet-vent grading for ``mep.trap_arm_length`` — MN 4714 (UPC) 908, pure of the model.

The rule lives in ``resolve/mep_trap_arm`` since 2026-11-03, where the router reads it too;
this module keeps the name the check and its tests import.

A child drain joining the arm's path that carries its own vent tee may end the arm only if
the wet vent is legal. The section is that child (tee to join) plus the parent from the join
downstream. Data and sources: ``takeoff.plumbing_calc.WET_VENT_*``;
``houses/catlin/notes/wet_vent_basis.md`` works a case by hand.

Plain data in: ``fx`` maps fixture tag -> ``(leaf drain run, DFU, plan symbol, storey)``;
``parents`` maps a run to ``(parent run, segment index, t)`` where its end stands.
"""

from __future__ import annotations

from typehaus.resolve.mep_trap_arm import Fx, Order, grade_wet_vent  # noqa: F401
