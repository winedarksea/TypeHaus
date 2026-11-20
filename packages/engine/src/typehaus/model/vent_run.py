"""``VentRun``: a chase riser bundling vent systems, and its optional increaser.

UPC 904.1 (MN 4714.0050, unamended) wants the vents open to atmosphere to total the
required building sewer's area; a 3" stack under a 4" sewer falls short. MN 4714.0906
subp. 3 then puts any change in diameter inside, in an insulated space, >= 12" below the
roof — so the step is a station on the interior riser, never on the exterior leg.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import PipeSystem
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class VentIncreaser(HausModel):
    """The VENT member of the bundle becomes ``diameter`` from ``elevation`` (project-frame
    absolute) up; other bundled systems (radon) keep the run's ``diameter``."""

    diameter: Length
    elevation: Length


def check_increaser(vent) -> None:
    """Raise unless the increaser sits on the interior riser: above the jog (or the start),
    below ``exit_elevation``, on a VENT member, and larger than the run."""
    inc = vent.vent_increaser
    if inc is None:
        return
    if PipeSystem.VENT not in vent.systems:
        raise ValueError(f"{vent.tag}: vent_increaser needs a PipeSystem.VENT member")
    if inc.diameter.meters <= vent.diameter.meters:
        raise ValueError(f"{vent.tag}: vent_increaser must be larger than diameter")
    jog = vent.chase_offset_elevation if vent.chase_offset is not None else None
    floor = (jog if jog is not None else vent.start_elevation).meters
    if not floor < inc.elevation.meters < vent.exit_elevation.meters:
        raise ValueError(f"{vent.tag}: vent_increaser must sit on the interior riser, "
                         "above the jog and below exit_elevation")


def increased_diameter(vent, system: object, z_m: float | None) -> Length:
    """The VENT member's size at ``z_m`` (``None``: its terminal); any other system's is
    the run's ``diameter``."""
    inc = vent.vent_increaser
    if inc is None or str(getattr(system, "value", system)) != PipeSystem.VENT.value:
        return vent.diameter
    if z_m is None or z_m >= inc.elevation.meters - 1e-9:
        return inc.diameter
    return vent.diameter


@register_element
class VentRun(Element):
    """A vertical vent riser bundling one or more systems up a shared mechanical chase.

    Encodes the Catlin routing intent: up the chase to ``exit_elevation`` (below the roof
    plane, so the jog stays inside), a 90° turn out through the wall by ``exit_offset``,
    then 90° back up the siding — clamped to the standing seam — terminating 12" above the
    roof. Optionally with one horizontal jog taken inside first (``chase_offset`` at
    ``chase_offset_elevation``), for a chase that surfaces where the roof leaves no height
    to rise in. The resolver derives the 3D polyline from these fields; it never invents
    the route. ``systems`` is typically (RADON, VENT).

    The termination height is *derived* from the roof plane at the exterior riser
    (resolve/vent_termination.py), not authored: an authored absolute cannot follow a rake
    it does not know about. ``roof_termination_elevation`` is therefore optional — supply
    it only where no roof is derivable, or as an assertion the ``mep.vent_termination_height``
    check validates against the derived value."""

    systems: tuple[PipeSystem, ...]
    diameter: Length
    chase_position: Point2D  # plan location of the chase
    start_elevation: Length  # where the riser starts (project-frame absolute)
    exit_elevation: Length  # below the roof plane at the chase, where it turns out
    exit_offset: Point2D  # horizontal delta chase top -> exterior riser plan location
    # An OPTIONAL horizontal jog taken *inside*, before the riser continues up to
    # ``exit_elevation`` and turns out through the wall — the same "rise to here, then step
    # sideways" pair ``exit_elevation``/``exit_offset`` already is, one storey earlier.
    #
    # A chase that is fine for its whole height can still surface somewhere it cannot rise:
    # under a story-and-a-half's rake the roof underside at the eave is inches above the
    # deck, and a riser in that chase has nowhere to go. Jogging it across the floor band to
    # a station with height is the cheap fix, and it is a fix the model could not express —
    # the alternative was moving ``chase_position`` and dragging the stack through every
    # storey below. Both fields must be set for the jog to take; ``None`` resolves the
    # original four-point route unchanged.
    chase_offset: Point2D | None = None
    chase_offset_elevation: Length | None = None
    roof_termination_elevation: Length | None = None  # optional; normally derived
    wall_ref: str | None = None  # exterior wall the riser penetrates / rides
    attachment: str = "standing_seam_clamp"  # how the exterior riser is fixed to the siding
    # Centre-to-centre between adjacent bundled risers; None is 1.6 diameters. Set it where
    # the bundle has to straddle a joist rather than share one bay.
    bundle_spacing: Length | None = None
    # Pitch for the exit and exterior legs, apart from the jog's; None keeps
    # ``bundle_spacing``. Negative swaps the pair's sides on the exit (the lanes cross at
    # two heights). Lets a fan's 24" circle (MN 1303.2402 subp. 5.D) clear the other leg.
    exit_bundle_spacing: Length | None = None
    # The ElectricalDevice that powers a future radon fan (MN 1303.2402 subp. 6).
    fan_power_ref: str | None = None
    # The VENT member's step up on the interior riser above the jog (UPC 904.1 aggregate
    # area); the roof clearance (MN 4714.0906 subp. 3) is graded at resolve.
    vent_increaser: VentIncreaser | None = None

    @model_validator(mode="after")
    def _increaser_on_the_riser(self):
        check_increaser(self)
        return self

    def diameter_of(self, system: object, z_m: float | None = None) -> Length:
        """Nominal size of one bundled pipe at ``z_m`` (``None``: at its terminal)."""
        return increased_diameter(self, system, z_m)


register_constructor("VentRun", VentRun)
register_constructor("VentIncreaser", VentIncreaser)
