"""A truss's heel: what a truss order states, at the outside face of bearing (decision #108).

Beside ``profiles.truss_chord_depth_m`` and for the reason that one is there:
``roof_geometry`` anchors the deck plane on the heel and ``framing.roof_gable`` hands it to
the viewer, and only one module may own the number.
"""

from __future__ import annotations

import math

from typehaus.model.assembly import FramingSpec
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import truss_chord_depth_m

#: The butt cut most truss plants design a standard heel with: the bottom chord's end is cut
#: square this high under the top chord (SBCA "Raised Heels" Q&A, sbcindustry.com; MiTek
#: "Reading Truss Shop Drawings" — some plants use 3/8"). (decision #108)
STANDARD_TRUSS_BUTT_CUT_M = inch(0.25).meters


def standard_truss_heel_m(spec: FramingSpec, pitch) -> float:
    """SBCA's standard heel: the top chord's PLUMB depth plus the butt cut.

    Measured top of bearing to top of top chord at the outside face of bearing — the
    cheapest truss a plant builds, with no raised or energy heel. ``pitch`` is the roof's.
    """
    return truss_chord_depth_m(spec) * math.hypot(1.0, pitch.slope) + STANDARD_TRUSS_BUTT_CUT_M


def truss_heel_height_m(spec: FramingSpec, pitch) -> float:
    """Authored heel height, or the standard heel at this pitch: top of bearing to top of top
    chord at the OUTSIDE face of bearing, the dimension a truss order states."""
    if spec.heel_height is not None:
        return spec.heel_height.meters
    return standard_truss_heel_m(spec, pitch)
