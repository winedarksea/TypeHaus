"""Cross-section recipes shared by the derived and the authored trim runs.

A gutter is the same piece of formed metal whether it is derived off a roof plane
(:mod:`typehaus.resolve.roof_trim`) or authored as an edge run on a deck
(:mod:`typehaus.resolve.accessories`). The member IR and the solid IR are both boxes-only,
so the channel has to be *composed* out of thin bands either way — and if each resolver
rolled its own the two would drift into different-looking gutters on the same house.
"""

from __future__ import annotations

from typehaus.quantities import inch

# The gutter channel is modelled as three thin bands (back / bottom / front) so it reads as
# an open-top U instead of a solid bar of aluminum. Real formed gutter stock is ~0.03" —
# too thin to survive as display geometry — so the shell is drawn at a nominal half inch,
# clamped so a narrow authored channel still keeps an open trough.
GUTTER_SHELL_M = inch(0.5).meters

# (key, offset of the band's inner face from the channel's inner side, band thickness,
#  band bottom / top as drops below the channel top)
Band = tuple[str, float, float, float, float]


def open_channel_bands(thickness_m: float, depth_m: float) -> tuple[Band, Band, Band]:
    """The three bands of an open-top U channel ``thickness_m`` wide, ``depth_m`` deep.

    Pure geometry in the channel's own cross-section frame: offsets run across the
    thickness from the back (house/fascia) face, drops run down from the channel rim. The
    back and front sheets run the full depth; the bottom spans between them and is only a
    shell thick, sitting at the floor of the trough — which is what leaves the top open.

    The shell is clamped to a third of each dimension so a channel narrower or shallower
    than the nominal half-inch stock still resolves as a trough rather than as three bands
    that meet in the middle and re-close it.
    """
    shell = min(GUTTER_SHELL_M, thickness_m / 3.0, depth_m / 3.0)
    return (
        ("back", 0.0, shell, depth_m, 0.0),
        ("bottom", shell, thickness_m - 2.0 * shell, depth_m, depth_m - shell),
        ("front", thickness_m - shell, shell, depth_m, 0.0),
    )
