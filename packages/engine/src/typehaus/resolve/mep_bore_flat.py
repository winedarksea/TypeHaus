"""Cuts no chart limits: a flat nonbearing header (R602.7.4) and an I-joist flange."""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_bore_verdict import BoreVerdict


def flat_header_cut(profile: str, cut_in: float) -> BoreVerdict:
    """A cut in an IRC R602.7.4 flat nonbearing header — a nailer, not a beam.

    "Load-bearing headers are not required in interior or exterior nonbearing walls": the
    flat 2x carries no tributary load, so ``header_bore``'s question (what a hole costs a
    bending member) is not asked of it and no table limits the cut. What it still does is
    give the jamb head and the finish a nailing surface, so the one thing graded is whether
    wood is left at the station: a cut through its whole 1 1/2" thickness is UNKNOWN.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    if section is None:
        return BoreVerdict(None, "notch", cut_in, None,
                           f"{profile!r} resolves no cross-section, so nothing can be "
                           "measured against it")
    thickness_in = min(section.width_m, section.depth_m) / M_PER_IN
    if cut_in >= thickness_in - 1e-6:
        return BoreVerdict(
            None, "notch", cut_in, thickness_in,
            f'a {cut_in:.2f}" run takes the whole {thickness_in:.2f}" of a flat {profile} '
            "nonbearing header (IRC R602.7.4): nothing is carried, but the door's head "
            "nailing is severed at this station",
            remedy="take the run above the nailer, or add a second flat member clear of it")
    return BoreVerdict(
        True, "notch", cut_in, thickness_in,
        f'IRC R602.7.4: a flat {profile} nonbearing header carries no load, so no rule '
        f'limits a cut in it; {cut_in:.2f}" off it leaves '
        f'{thickness_in - cut_in:.2f}" of the {thickness_in:.2f}" nailer at the head')


#: Every I-joist maker (TJI, LPI, BCI, AJS) forbids cutting, notching or boring a FLANGE, at
#: any station and any size: the one I-joist rule that needs no chart.
I_JOIST_FLANGE_CUT_IN = 0.0


def i_joist_flange_cut(profile: str, cut_in: float) -> BoreVerdict:
    """A run's surface ``cut_in`` into an I-joist flange: FAIL for anything above zero."""
    if cut_in <= I_JOIST_FLANGE_CUT_IN + 1e-9:
        return BoreVerdict(True, "notch", cut_in, I_JOIST_FLANGE_CUT_IN,
                           f"clear of both flanges of the {profile}")
    return BoreVerdict(
        False, "notch", cut_in, I_JOIST_FLANGE_CUT_IN,
        f'{cut_in:.3f}" into a flange of a {profile}: I-joist makers forbid cutting, '
        "notching or boring a flange at any size or station, so no chart permits it",
        remedy="move the run clear of the flange, or through the web inside the maker's "
               "hole zone")
