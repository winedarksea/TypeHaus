"""Is the ridge beam deep enough for the rafters hung on it (→ 12 §checks/structural)?

Nothing graded a ridge beam until this module. ``structural.rafter_span`` opts out of a
ridge-beam roof outright, ``structural.deck_beam_span`` only fires on an R507 deck and has
no LVL row anyway, ``structural.ridge_support`` fires only when *no* beam is authored at
all, and ``structural.member_interference`` explicitly excuses the ``ridge_beam`` x
``stud``/``plate`` pair so the centre wall running up inside the beam draws nothing. A
ridge could therefore be any depth at all and the report stayed clean.

**The rule is geometric and it is about the hanger, not the beam's bending.** The resolver
pins the beam's top to ``roof.ridge_z_m`` and trims each rafter back by half the beam width
(``resolve/framing/roof.py``), so the rafter is cut PLUMB at the beam's face and hung there
on a sloped face-mount hanger. The hanger's seat is at the bottom of that cut. If the beam's
soffit is above it, the seat and the hanger's lowest fasteners have no wood behind them —
the connection is drawn, priced and unbuildable.

Catlin ran that way: 11 7/8" I-joist rafters at 4:12 make a **12.52"** plumb face, which on
a 5 1/4"-wide beam starts another 0.875" down the roof plane, against an 11 7/8" beam. The
joist's bottom flange hung 1.52" past the soffit.

**Why this computes the plumb depth itself rather than reading the member.**
``_roof_rafters`` sets ``z0_end_m = z1_end_m - depth`` where ``depth`` is the STRUCTURE
layer's thickness — a dimension measured PERPENDICULAR to the roof plane, used here as if it
were vertical. The resolved rafter box is therefore 11.875" tall at the ridge where the real
plumb face is 12.517", and a check that trusted ``z0_end_m`` would have reported catlin's
old ridge as adequate with 0.64" to spare. The honest root fix is for the resolver to carry
a true plumb vertical extent at both ends, but that moves the eave seat, the interference
candidates and the hanger detection together; until it happens this module multiplies by
``roof_slope_factor`` and is correct either way.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import Beam
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.roof_geometry import roof_slope_factor

CHECK_ID = "structural.ridge_beam_depth"

# The beam soffit may sit this far ABOVE the plumb cut's bottom and still pass. It is not a
# construction tolerance — it is the arithmetic's own noise, since both elevations are
# derived from the same plane. A sixteenth, like the bearing-seat check next door.
_TOL_IN = 0.0625


def _ridge_beam_tag(ctx: CheckContext, parent_uid: str) -> str | None:
    """The authored ``Beam``'s tag behind a resolved ``ridge_beam`` member."""
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if isinstance(element, Beam) and element.uid == parent_uid:
                return element.tag
    return None


def _plumb_bottom(member, factor: float) -> float | None:
    """A hung rafter's real bottom-of-plumb-cut elevation at the carrier's face.

    ``z1_end_m`` (the ridge-end TOP) is on the roof plane and is trustworthy; the vertical
    extent below it is not, so it is rebuilt from the section.
    """
    top = member.z1_end_m
    if top is None:
        return None
    return top - cross_section(member.profile).depth_m * factor


@check(Tier.STRUCTURAL, CHECK_ID)
def ridge_beam_depth(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for roof in ctx.model.roofs:
        out.extend(_grade(ctx, roof))
    return out


def _grade(ctx: CheckContext, roof: ResolvedRoof) -> list[Finding]:
    beams = [m for m in roof.members if m.category == "ridge_beam"]
    rafters = [m for m in roof.members if m.category == "rafter"]
    if not beams or not rafters:
        return []  # a truss roof, or a roof with no authored ridge — not this check's business
    beam = beams[0]
    tag = _ridge_beam_tag(ctx, beam.parent_uid) or beam.parent_uid
    tags = (roof.tag, tag)
    factor = roof_slope_factor(roof)
    section = cross_section(beam.profile)

    bottoms = [b for b in (_plumb_bottom(m, factor) for m in rafters) if b is not None]
    if not bottoms:
        return [Finding(
            severity=Severity.WARN, check_id=CHECK_ID,
            message=(f"UNKNOWN — {roof.tag}'s rafters carry no ridge-end elevation, so the "
                     f"plumb cut {tag} has to back cannot be measured"),
            element_tags=tags, result=Result.UNKNOWN)]

    lowest = min(bottoms)
    margin_in = (lowest - beam.z0_m) / M_PER_IN
    rafter_depth_in = cross_section(rafters[0].profile).depth_m / M_PER_IN
    plumb_in = rafter_depth_in * factor
    needed_in = (roof.ridge_z_m - lowest) / M_PER_IN

    detail = (f"{rafter_depth_in:g}\" rafters at {factor:.4g}x slope cut "
              f"{plumb_in:.4g}\" plumb, {section.width_m / M_PER_IN:g}\" off the peak")
    if margin_in < -_TOL_IN:
        return [Finding(
            severity=Severity.ERROR, check_id=CHECK_ID,
            message=(f"ridge beam {tag} ({beam.profile}) soffits at "
                     f"{beam.z0_m / M_PER_IN:.4g}\" but {roof.tag}'s rafters cut down to "
                     f"{lowest / M_PER_IN:.4g}\" at its face — {-margin_in:.4g}\" of hanger "
                     f"seat and bottom flange with no beam behind it ({detail})"),
            element_tags=tags, result=Result.FAIL,
            fix_hint=(f"the beam has to be at least {needed_in:.4g}\" deep below the roof "
                      f"plane; LVL is made in 9.5/11.875/14/16/18\", so take the next depth "
                      f"up rather than trying to hit the number"))]
    return [Finding(
        severity=Severity.WARN, check_id=CHECK_ID,
        message=(f"ridge beam {tag} ({beam.profile}) backs {roof.tag}'s rafters with "
                 f"{margin_in:.4g}\" to spare — {needed_in:.4g}\" needed below the roof "
                 f"plane, {section.depth_m / M_PER_IN:g}\" provided ({detail})"),
        element_tags=tags, result=Result.PASS)]
