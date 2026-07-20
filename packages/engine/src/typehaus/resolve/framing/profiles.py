"""Structured lumber/engineered-member cross-section catalog (→ 20 WP framing).

``FramedMember.profile`` strings are structural-check keys (see
``checks/structural/checks.py`` and ``cli/app.py``'s ``haus ls`` counters) — this
module only *parses* them into real dimensions, it never rewrites a stored profile
string. ``tables.py`` keeps its existing ``LUMBER_ACTUAL``/``member_actual`` for its
existing consumers; this module is the new, fuller catalog consumed by serialization
(WP5) and the UI (WP6-8).

Orientation convention (defined once, mirrored in ``ui/src/model/types.ts``):
``width_m`` is always the *thickness* face — 1.5" for a stud along the wall axis, the
narrow face of a joist/rafter along its span. ``depth_m`` is always the *wide* face —
3.5"+ through a wall, or the vertical depth of a joist/rafter/beam. This holds
regardless of the member's plan orientation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from typehaus.quantities import inch
from typehaus.resolve.framing.tables import LUMBER_ACTUAL

# Multi-ply ridge/girder LVL beam approximating the user's "6x12" ask: 3 plies of
# 1.75" LVL stock (5.25" combined width) x 11.875" depth.
RIDGE_BEAM_DEFAULT = "3-1.75x11.875 LVL"

# Matches tables.member_actual's fallback for an unrecognized nominal size.
_FALLBACK_ACTUAL_IN = (1.5, 5.5)
# Safe default for the "engineered-LVL" beyond-prescriptive placeholder (tables.py
# emits this literal for headers wider than the prescriptive table covers).
_ENGINEERED_LVL_ACTUAL_IN = (3.5, 11.25)

_RE_MULTI_LVL = re.compile(
    r"^(?P<plies>\d+)-(?P<width>\d+(?:\.\d+)?)x(?P<depth>\d+(?:\.\d+)?)\s+LVL$"
)
_RE_SINGLE_LVL = re.compile(
    r"^(?P<width>\d+(?:\.\d+)?)x(?P<depth>\d+(?:\.\d+)?)\s+LVL$"
)
_RE_RIM = re.compile(r"^(?P<width>\d+(?:\.\d+)?)x(?P<depth>\d+(?:\.\d+)?)\s+rim$")
_RE_IJOIST = re.compile(r"^(?P<depth>\d+(?:\.\d+)?)\s+I-joist$")
_RE_MULTI_NOMINAL = re.compile(r"^(?P<plies>\d+)-(?P<nominal>\d+x\d+)$")
_RE_NOMINAL = re.compile(r"^\d+x\d+$")


@dataclass(frozen=True)
class CrossSection:
    """A resolved member cross-section, in meters.

    ``width_m``/``depth_m`` follow the orientation convention documented above for
    every shape, including ``"i_joist"`` (there, ``width_m`` is the flange width).
    """

    shape: str  # "rect" | "i_joist"
    width_m: float
    depth_m: float
    flange_width_m: float | None = None
    flange_thickness_m: float | None = None
    web_thickness_m: float | None = None
    plies: int = 1


def _rect(width_in: float, depth_in: float, plies: int = 1) -> CrossSection:
    return CrossSection(shape="rect", width_m=inch(width_in).meters,
                        depth_m=inch(depth_in).meters, plies=plies)


def cross_section(profile: str) -> CrossSection:
    """Parse a ``FramedMember.profile`` string into a :class:`CrossSection`.

    Never mutates or re-derives the stored profile string — parse-only, with a safe
    rectangular fallback for anything unrecognized so callers never have to guard.
    """
    text = profile.strip()

    if match := _RE_MULTI_LVL.match(text):
        plies = int(match["plies"])
        ply_width = float(match["width"])
        depth = float(match["depth"])
        return _rect(ply_width * plies, depth, plies=plies)

    if match := _RE_SINGLE_LVL.match(text):
        return _rect(float(match["width"]), float(match["depth"]))

    if match := _RE_RIM.match(text):
        return _rect(float(match["width"]), float(match["depth"]))

    if match := _RE_IJOIST.match(text):
        depth_in = float(match["depth"])
        flange_width_in = 3.5 if depth_in >= 14.0 else 2.5
        return CrossSection(
            shape="i_joist", width_m=inch(flange_width_in).meters,
            depth_m=inch(depth_in).meters, flange_width_m=inch(flange_width_in).meters,
            flange_thickness_m=inch(1.375).meters, web_thickness_m=inch(0.375).meters,
        )

    if match := _RE_MULTI_NOMINAL.match(text):
        plies = int(match["plies"])
        thickness_in, depth_in = LUMBER_ACTUAL.get(match["nominal"], _FALLBACK_ACTUAL_IN)
        return _rect(thickness_in * plies, depth_in, plies=plies)

    if _RE_NOMINAL.match(text):
        thickness_in, depth_in = LUMBER_ACTUAL.get(text, _FALLBACK_ACTUAL_IN)
        return _rect(thickness_in, depth_in)

    if text == "engineered-LVL":
        return _rect(*_ENGINEERED_LVL_ACTUAL_IN)

    return _rect(*_FALLBACK_ACTUAL_IN)
