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

# Default ridge/girder section: 2 plies of 1.75" LVL stock (3.5" combined) x 14" deep.
#
# The depth is a HANGER dimension, not a bending one, and 14" is not a round number picked
# for comfort. A ridge beam's top is pinned to the roof plane at the peak, the rafters are
# cut plumb at its face and hung there, and the hanger's seat is at the bottom of that cut —
# so the beam must reach at least the plumb-cut depth below the ridge line or the seat has no
# wood behind it. An 11 7/8" I-joist rafter at 4:12 cuts 12.52" plumb (11.875 x 1.0541) and
# its face sits half a beam width off the peak, another 0.58" down the plane: 13.10" needed,
# and LVL is made in 9.5/11.875/14/16/18". ``checks/structural/ridge.py`` grades it.
#
# This was "3-1.75x11.875 LVL" until 2026-08-28, and the comment here recorded the reason
# honestly enough to convict it: *approximating the user's "6x12" ask*. Three plies were
# never a load answer, and the depth they came with was 1.5" short.
RIDGE_BEAM_DEFAULT = "2-1.75x14 LVL"

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
# Open-web trimmable floor truss, fabricated to depth: "11.875 floor truss".
_RE_FLOOR_TRUSS = re.compile(r"^(?P<depth>\d+(?:\.\d+)?)\s+floor truss$")
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
# The optional ``label`` word (e.g. "corner") is a BOM-facing distinction only — two panels
# of the same width and thickness still parse to the identical ``CrossSection`` regardless of
# label, so ``takeoff/cost_codes.py`` can key a specific pattern off it without this module
# caring what the label means.
_RE_PANEL = re.compile(
    r"^(?P<width>\d+(?:\.\d+)?)x(?P<thickness>\d+(?:\.\d+)?)\s+(?:(?P<label>[a-z]+)\s+)?panel$"
)


def panel_profile(width_in: float, thickness_in: float, label: str | None = None) -> str:
    """The canonical ``"<width>x<thickness>[ <label>] panel"`` profile string for sheet goods."""
    prefix = f"{label} " if label else ""
    return f"{width_in:g}x{thickness_in:g} {prefix}panel"


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


# How far the member's own vertical extent may miss its section thickness and still count as
# flat-laid. The house's flat members land within 1e-8 m of their thickness and the nearest
# on-edge member is 0.021 m away, so 0.1 mm separates the two cases with three orders of
# margin on both sides.
FLAT_LAID_TOLERANCE_M = 1e-4


def plan_cross_section_m(section: CrossSection, vertical_extent_m: float) -> float:
    """The section dimension a plan cut sees *across* a horizontal member's run.

    The one place the flat-vs-on-edge question is answered — the 2D framing plan, the
    interference check, the glTF/IFC solids and the viewer all read it from here. A member
    lying flat (a plate, a rough sill, a blocking course) shows its wide ``depth_m`` face in
    plan and stands only ``width_m`` tall; one on edge (a header, a joist, a rafter) shows
    the narrow ``width_m`` and stands ``depth_m`` tall.

    Classifying by *category* instead — the rule this replaced — silently missed every flat
    category nobody remembered to list, drawing 5.5" blocking and rough sills as 1.5"
    ribbons. The member's own vertical extent already states which way it was laid, so read
    that: it cannot go stale when a new flat category appears.

    ``vertical_extent_m`` is the member's z-extent at one station (``z1_m - z0_m``), not the
    full span of a raked member — a rafter rises meters end to end while its section never
    changes.
    """
    if abs(vertical_extent_m - section.width_m) <= FLAT_LAID_TOLERANCE_M:
        return section.depth_m
    return section.width_m


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

    if match := _RE_FLOOR_TRUSS.match(text):
        depth_in = float(match["depth"])
        # Chords reuse the i_joist "flange_*" fields deliberately: every existing
        # consumer of "two lines inboard of the edges" (section drawing, the UI
        # inspector) works unchanged. width_m/flange_width_m are the 2x4-flat chord's
        # 3 1/2" wide face; flange_thickness_m/web_thickness_m are the chord's 1 1/2"
        # depth, which is also what open_web_opening_m subtracts twice.
        return CrossSection(
            shape="floor_truss", width_m=inch(3.5).meters,
            depth_m=inch(depth_in).meters, flange_width_m=inch(3.5).meters,
            flange_thickness_m=inch(1.5).meters, web_thickness_m=inch(1.5).meters,
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


def open_web_opening_m(section: CrossSection) -> float | None:
    """Clear chord-to-chord opening of an open-web member; None if it has no web space.

    The single place the 8 7/8" number (11 7/8" depth minus two 1 1/2" chords) is
    derived. Nothing else may restate it.
    """
    if section.shape != "floor_truss" or section.flange_thickness_m is None:
        return None
    return section.depth_m - 2 * section.flange_thickness_m
