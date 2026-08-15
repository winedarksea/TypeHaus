"""Structured lumber/engineered-member cross-section catalog (→ 20 WP framing).

``FramedMember.profile`` strings are structural-check keys (see
``checks/structural/checks.py`` and ``cli/cmd_takeoff.py``'s ``haus takeoff`` counters) —
this module only *parses* them into real dimensions, it never rewrites a stored profile
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
from functools import lru_cache

from typehaus.model.assembly import FramingSpec
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
# Stair-landing deck surface, e.g. "deck 42x1.5": a platform-wide walking board whose
# ``width_m`` is the platform width (so it renders full-width, not as a 1.5" strip).
_RE_DECK = re.compile(r"^deck\s+(?P<width>\d+(?:\.\d+)?)x(?P<depth>\d+(?:\.\d+)?)$")
_RE_IJOIST = re.compile(r"^(?P<depth>\d+(?:\.\d+)?)\s+I-joist$")
_RE_MULTI_NOMINAL = re.compile(r"^(?P<plies>\d+)-(?P<nominal>\d+x\d+)$")
_RE_NOMINAL = re.compile(r"^\d+x\d+$")
# Actual (already-milled) rectangular dimensions, e.g. a custom 6.125x6.125 timber post.
# A decimal point is the tell: no nominal lumber size carries one, so "6.125x6.125" is
# stated dimensions, not a LUMBER_ACTUAL key — checked before the nominal fallback so a
# custom timber never resolves as a 1.5x5.5 stud.
_RE_ACTUAL = re.compile(
    r"^(?P<width>\d+\.\d+)x(?P<depth>\d+(?:\.\d+)?)$|^(?P<width2>\d+)x(?P<depth2>\d+\.\d+)$"
)
# Round column, e.g. a 12" sonotube-cast concrete pier: "12 round".
_RE_ROUND = re.compile(r"^(?P<dia>\d+(?:\.\d+)?)\s+round$")
# Sheet goods swept as a member rather than milled lumber — a soffit panel, or the
# sheathing/cladding band that closes a raised heel or a gable end. Written
# "<width>x<thickness> panel" in inches: ``width`` is the face the panel presents across
# its run, ``thickness`` its sheet thickness. Real panels come in arbitrary dimensions,
# so they cannot be spelled as a nominal lumber size.
_RE_PANEL = re.compile(
    r"^(?P<width>\d+(?:\.\d+)?)x(?P<thickness>\d+(?:\.\d+)?)\s+panel$"
)


def panel_profile(width_in: float, thickness_in: float) -> str:
    """The canonical ``"<width>x<thickness> panel"`` profile string for sheet goods."""
    return f"{width_in:g}x{thickness_in:g} panel"


@dataclass(frozen=True)
class CrossSection:
    """A resolved member cross-section, in meters.

    ``width_m``/``depth_m`` follow the orientation convention documented above for
    every shape, including ``"i_joist"`` (there, ``width_m`` is the flange width).
    """

    shape: str  # "rect" | "i_joist" | "round"
    width_m: float  # for "round": the diameter (width_m == depth_m)
    depth_m: float
    flange_width_m: float | None = None
    flange_thickness_m: float | None = None
    web_thickness_m: float | None = None
    plies: int = 1


def _rect(width_in: float, depth_in: float, plies: int = 1) -> CrossSection:
    return CrossSection(shape="rect", width_m=inch(width_in).meters,
                        depth_m=inch(depth_in).meters, plies=plies)


@lru_cache(maxsize=512)
def cross_section(profile: str) -> CrossSection:
    """Parse a ``FramedMember.profile`` string into a :class:`CrossSection`.

    Never mutates or re-derives the stored profile string — parse-only, with a safe
    rectangular fallback for anything unrecognized so callers never have to guard.

    Cached because it is a pure function of one string and the geometry stage calls it
    15,160 times per resolve of ``houses/catlin`` — for a few dozen distinct profiles,
    driving 116k regex matches underneath. :class:`CrossSection` is a frozen dataclass,
    so handing every caller the same instance is safe.
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

    if match := _RE_DECK.match(text):
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

    if match := _RE_ACTUAL.match(text):
        width_in = float(match["width"] or match["width2"])
        depth_in = float(match["depth"] or match["depth2"])
        return _rect(width_in, depth_in)

    if _RE_NOMINAL.match(text):
        thickness_in, depth_in = LUMBER_ACTUAL.get(text, _FALLBACK_ACTUAL_IN)
        return _rect(thickness_in, depth_in)

    if match := _RE_PANEL.match(text):
        return _rect(float(match["width"]), float(match["thickness"]))

    if match := _RE_ROUND.match(text):
        dia_m = inch(float(match["dia"])).meters
        return CrossSection(shape="round", width_m=dia_m, depth_m=dia_m)

    if text == "engineered-LVL":
        return _rect(*_ENGINEERED_LVL_ACTUAL_IN)

    # Stair hardware/carriage profiles (→ resolve/envelope.py stair members): parsed
    # explicitly so they never hit the silent 1.5x5.5 fallback.
    if text == "hanger":
        return _rect(1.5, 8.0)

    if text == "tapered tread":
        return _rect(1.5, 11.25)

    return _rect(*_FALLBACK_ACTUAL_IN)


def truss_chord_depth_m(spec: FramingSpec) -> float:
    """Depth of a truss chord: the chord member when specified, else the wall member.

    Lives here rather than in ``resolve.roof_geometry`` because both that module and
    ``resolve.framing.roof_gable`` need it, and ``roof_geometry`` already imports this
    one — hosting it there put a cycle between them one import-order change away.
    """
    return cross_section(spec.chord_member or spec.member).depth_m
