"""Duct. Two things differ from pipe, and both come from the section rather than the trade.

**The radius is half the LARGER plan dimension.** A rectangular duct turning a corner
sweeps its own diagonal, and this package has no fitting model to say otherwise, so the
inflation is the conservative one. A round duct is the degenerate case and comes out right
by the same rule.

**A crossing is admissible only within ``open_web_opening_m``** — the round hole a truss's
own web geometry permits — and that is *smaller* than the chord-to-chord gap a pipe may
use. ``mep.duct_bay_occupancy`` already grades this after the fact; reusing the pipe rule
here would propose crossings a fabricator refuses.

``houses/catlin/notes/mep_duct_routing_basis.md`` is the oracle, and §3 says the thing this
module must not paper over: the model gives each run **one centreline per bay**, so it
cannot place two lanes side by side, and a proposal into an occupied bay has to say so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.routing.corridors import Corridor

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedFloor, ResolvedModel


def radius_m(*, diameter_m: float | None = None, width_m: float = 0.0,
             depth_m: float = 0.0) -> float:
    """Half the larger plan dimension. See the module note on why not the smaller."""
    if diameter_m:
        return diameter_m / 2.0
    return max(width_m, depth_m) / 2.0


def crossing_admissible(model: ResolvedModel, floor: ResolvedFloor, *,
                        diameter_m: float | None = None,
                        width_m: float = 0.0, depth_m: float = 0.0) -> bool:
    """Whether a duct of this section may pass through this floor's members.

    The test is the round opening, not the chord window: a duct goes through a hole, and a
    hole in an open web is bounded by the web's own geometry. A floor whose member profile
    this build cannot read answers **False** — refusing to propose a crossing it cannot
    justify is the conservative direction, and the caller sees a route round rather than a
    route through.
    """
    del model  # the floor carries its own members; the model is the caller's handle
    from typehaus.routing.corridors import _open_web_opening

    members = [m for m in floor.members if m.z0_m is not None]
    opening = _open_web_opening(members[0].profile) if members else None
    if not opening:
        return False
    return opening >= 2.0 * radius_m(diameter_m=diameter_m, width_m=width_m,
                                     depth_m=depth_m) - 1e-9


def bay_occupancy_note(corridor: Corridor, radius_m_value: float) -> str | None:
    """A disclosure when a proposal shares a bay, or None when it has the bay to itself.

    ``corridors.soffit_corridors`` and ``floor_corridors`` report the width that is LEFT,
    so a route that still fits an occupied channel is legal and is not silent about it.
    """
    if 2.0 * radius_m_value <= corridor.clear_width_m - 1e-9:
        return None
    return (f"{corridor.tag} has {corridor.clear_width_m / 0.0254:.1f}\" of clear section "
            f"left and this run wants {2 * radius_m_value / 0.0254:.1f}\" — the model "
            "gives each run one centreline per channel, so it cannot place two lanes side "
            "by side and neither can this proposal")
