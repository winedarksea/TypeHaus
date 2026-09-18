"""How much of a channel is left once the runs already in it are stood side by side.

Two places in this tree answered "what does a corridor have left" and both answered it by
**summing every occupant's width**: ``routing/corridors._remaining_taken`` for a soffit, and
``mep.duct_joist_bay_occupancy``'s pairwise loop for a bay. Summing is right for two runs at
the same height and wrong for two that are not, and the second case is the ordinary one —
an 11 7/8" open-web floor stacks a 3" radial over another with room to spare, and a 2'-8"
soffit carries the air handler's case low and a 4" branch over the top of it. Summed, those
pairs report a bay that is full when it is half empty, which is how a perfectly routable
lane comes back priced out.

**The packing is a stack, and the governing tier is what a new run has to fit beside.**
Occupants that overlap in z must share the corridor's width; occupants that do not, do not.
So the width taken is the **largest total width over any elevation**, found by a sweep over
the z-band edges, and the remaining width is the clear width less that. The tier is carried
with its elevation so a finding can say *where* the pinch is — "6 1/2" left at z = 2.31 m,
against FS-S-STUDY and FS-S-LAUNDRY" is actionable and "the bay is full" is not.

**What this deliberately does not claim.** The model gives a run one centreline per channel
and no across-channel station, so this cannot say a run is at the left edge or the right. It
says how much width is spoken for at the worst height, which is a *capacity* statement and
true regardless of where anybody slides the runs. Whether two runs drawn on the same
centreline are literally interpenetrating is ``mep.run_interference``'s question, asked
against real envelopes; this one is "does the channel hold them all", and the distinction is
why an over-subscribed tier is a FAIL and a merely-shared one is not.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Bands closer than this are the same elevation. A sixteenth of an inch — the grid a
#: proposal is snapped to, so two runs that resolve a hair apart are not called stacked.
_Z_EPS = 0.0254 / 16.0


@dataclass(frozen=True)
class Occupant:
    """One run's claim on a channel: how wide it is across, and over what z band.

    ``width_m`` is the dimension ACROSS the corridor's travel axis, which for a rectangular
    duct is not always its ``width`` — a duct turned on edge in a bay is its depth across.
    The caller resolves that, because only the caller knows which way the leg runs.
    """

    tag: str
    width_m: float
    z0_m: float
    z1_m: float


@dataclass(frozen=True)
class Packing:
    """What a channel has left, and the tier that decides it."""

    clear_width_m: float
    taken_m: float
    #: Tags in the governing tier, sorted. Empty when the channel is untouched.
    tier: tuple[str, ...]
    #: The elevation the tier was measured at — where the pinch is.
    z_m: float

    @property
    def remaining_m(self) -> float:
        return self.clear_width_m - self.taken_m

    def admits(self, width_m: float) -> bool:
        return width_m <= self.remaining_m + 1e-9

    def oversubscribed(self) -> bool:
        """The tier already asks for more width than the channel has."""
        return self.remaining_m < -1e-9

    def basis(self) -> str:
        from typehaus.quantities import M_PER_IN
        if not self.tier:
            return f'{self.clear_width_m / M_PER_IN:.2f}" clear and nothing in it'
        return (f'{self.remaining_m / M_PER_IN:.2f}" of {self.clear_width_m / M_PER_IN:.2f}"'
                f" left beside {', '.join(self.tier)} "
                f"({self.taken_m / M_PER_IN:.2f}\" wide together at the tightest tier)")


def pack(clear_width_m: float, occupants: list[Occupant] | tuple[Occupant, ...]) -> Packing:
    """The governing tier of ``occupants`` in a channel ``clear_width_m`` wide.

    A sweep, not a bin-packing: the answer is the maximum over elevation of the summed
    widths of the occupants present there, which is exact for the one-dimensional question
    being asked and needs no search. Zero-width and inverted bands are dropped rather than
    raising — an unresolved run is a coverage gap for the caller, not an error here.
    """
    live = [o for o in occupants if o.width_m > 0 and o.z1_m - o.z0_m > -_Z_EPS]
    if not live:
        return Packing(clear_width_m, 0.0, (), 0.0)

    best_total, best_tier, best_z = 0.0, (), live[0].z0_m
    #: Every band's own floor is a candidate station: the tier can only change where one
    #: starts, so testing the starts tests every distinct tier exactly once.
    for station in sorted({o.z0_m for o in live}):
        present = [o for o in live
                   if o.z0_m <= station + _Z_EPS <= o.z1_m + _Z_EPS or
                   abs(o.z0_m - station) <= _Z_EPS]
        total = sum(o.width_m for o in present)
        if total > best_total:
            best_total, best_tier, best_z = (total, tuple(sorted(o.tag for o in present)),
                                             station)
    return Packing(clear_width_m, best_total, best_tier, best_z)


def run_occupants(model, *, channel_ref: str,
                  attr: str = "soffit_ref") -> list[Occupant]:
    """Every duct and pipe naming ``channel_ref`` through ``attr``, as occupants.

    A run travelling along a channel presents its plan ``width`` across it and its ``depth``
    vertically, which is the pair ``DuctRun`` is authored in; a round run is its real
    outside diameter (insulation included, via ``run_sections``) either way.
    """
    from typehaus.resolve.mep_envelopes import run_sections

    sections = run_sections(model)
    out: list[Occupant] = []
    for run in (*model.ducts, *model.pipe_runs):
        if getattr(run, attr, None) != channel_ref:
            continue
        across, deep = _across_and_depth(run, sections.get(run.tag))
        if across <= 0:
            continue
        z = [v for v in (getattr(run, "z_m", None) or ()) if v is not None]
        mid = (sum(z) / len(z)) if z else 0.0
        out.append(Occupant(run.tag, across, mid - deep / 2.0, mid + deep / 2.0))
    return out


def _across_and_depth(run,
                      section: tuple[float, float, str | None] | None) -> tuple[float, float]:
    """``(width across the channel, vertical depth)`` for one run."""
    diameter = getattr(run, "diameter_m", None)
    if diameter:
        outside = section[0] * 2.0 if section else diameter
        return outside, outside
    return getattr(run, "width_m", 0.0) or 0.0, getattr(run, "depth_m", 0.0) or 0.0
