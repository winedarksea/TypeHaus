"""A ``VentRun``'s increaser: the VENT pipe steps up before it leaves the building.

UPC 904.1 (MN 4714.0050, unamended) wants the vents open to atmosphere to total the
required building sewer's area; a 3" stack under a 4" sewer falls short. MN 4714.0906
subp. 3 then puts any change in diameter inside, in an insulated space, >= 12" below the
roof — so the step is a station on the interior riser, never on the exterior leg.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import PipeSystem
from typehaus.quantities import Length


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
