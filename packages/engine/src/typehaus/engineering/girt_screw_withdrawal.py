"""The girt crossing screw's arithmetic — thread bookkeeping, withdrawal, pull-through.

Pure numbers, no model types, for the same reason ``checks/structural/cladding_fastener.py``
is: this is the part a reviewer checks line by line against a report, and it should be
readable without a house in hand.

**The thing this module exists to say is that a screw has two lengths.** Overall length is
what the box prints; THREAD length is what decides whether the screw works, and the two are
independent — IAPMO UES ER-192 Table 7 gives every SDWS22 a 3" thread whether it is 3" or
8" long. A lag-type screw draws a stack together only if the members being clamped are
spanned by plain SHANK: thread biting in the near member jacks it away from the far one and
the joint stands open, whatever the withdrawal number says. So::

    plain shank   = length - thread              must span the CLAMPED STACK
    thread in the stack = thread - (length - stack)     must be <= 0

which are the same statement twice, and the second is what the audit found unanswered.

The capacities here are READ, never derived. Withdrawal per inch of embedded thread and
head pull-through are published test values in the screw's own evaluation report; NDS
§12.2's ``W = 2850 G^2 D`` is computed alongside only as a cross-check, the way the panel
note prints ER-309's DFL row beside its own arithmetic.
"""

from __future__ import annotations

#: NDS 2018 §12.2.1, lb per inch of thread penetration — the CROSS-CHECK coefficient only.
#: Nothing here grades against it; a tested report value supersedes a code equation.
NDS_WITHDRAWAL_COEFFICIENT = 2850.0

#: NDS 2018 §12.1.4.6: a wood screw's thread must penetrate the main member at least 6D.
MINIMUM_PENETRATION_DIAMETERS = 6.0


def plain_shank_in(length_in: float, thread_in: float) -> float:
    """The unthreaded run below the head — what has to span the clamped stack."""
    return length_in - thread_in


def thread_in_side_member(length_in: float, thread_in: float,
                          clamped_stack_in: float) -> float:
    """Thread standing INSIDE the members being clamped. Anything above zero is a jack.

    Zero is the target and the only acceptable answer, not a margin to be maximised: the
    ideal screw's last thread starts exactly at the far face of the stack.
    """
    return max(thread_in - (length_in - clamped_stack_in), 0.0)


def thread_in_main_member(length_in: float, thread_in: float, through_in: float,
                          tip_in: float = 0.0) -> float:
    """Embedded thread in the member the screw lands in — the withdrawal length.

    ``through_in`` is everything the screw crosses before it arrives: on a girt wall that is
    the clamped stack PLUS the sheathing, which is nailed to the stud and therefore counts
    on the stud's side of the joint rather than as something being drawn together.

    ``tip_in`` defaults to 0.0 because ESR-1078 tabulates withdrawal against *embedded
    thread length* measured to the point; deducting a tapered tip as well would take the
    same steel off twice. A report that measured its thread from the end of the taper would
    pass its own taper here.
    """
    return max(min(thread_in, length_in - through_in - tip_in), 0.0)


def withdrawal_lb(withdrawal_per_in: float, thread_in: float, c_d: float = 1.0) -> float:
    """Published withdrawal per inch x embedded thread, adjusted.

    ``c_d`` is 1.0 by default and deliberately: the load-duration factor belongs to the
    *report's* own adjustment clause, not to NDS Table 2.3.2 by analogy, and applying 1.6 to
    a tested allowable whose report does not permit it would inflate a capacity by 60% on a
    reading nobody made. A caller that has verified the clause passes the factor.
    """
    return withdrawal_per_in * thread_in * c_d


def nds_withdrawal_per_in(specific_gravity: float, diameter_in: float) -> float:
    """W = 2850 G^2 D, NDS 2018 §12.2.1 — printed beside the report value, never instead."""
    return NDS_WITHDRAWAL_COEFFICIENT * specific_gravity ** 2 * diameter_in


def minimum_penetration_in(diameter_in: float) -> float:
    """6D, NDS 2018 §12.1.4.6 — an input check on the thread in the main member."""
    return MINIMUM_PENETRATION_DIAMETERS * diameter_in


def tributary_area_ft2(block_spacing_in: float, course_spacing_in: float) -> float:
    """One crossing's share of the wall: the block module by the course module.

    One screw per crossing is the whole pattern, so there is nothing else to divide by.
    """
    return (block_spacing_in / 12.0) * (course_spacing_in / 12.0)


def crossing_demand_lb(pressure_psf: float, block_spacing_in: float,
                       course_spacing_in: float) -> float:
    return pressure_psf * tributary_area_ft2(block_spacing_in, course_spacing_in)
