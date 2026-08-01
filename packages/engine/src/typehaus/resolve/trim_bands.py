"""Cross-section recipes shared by the derived and the authored trim runs.

A gutter — or a drip edge — is the same piece of formed metal whether it is derived off a
roof plane (:mod:`typehaus.resolve.roof_trim`) or authored as an edge run on a deck
(:mod:`typehaus.resolve.accessories`). The member IR and the solid IR are both boxes-only,
so the section has to be *composed* out of thin bands either way — and if each resolver
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


def drip_edge_bands(thickness_m: float, depth_m: float) -> tuple[Band, Band]:
    """The two legs of a drip edge ``thickness_m`` out from the roof edge, ``depth_m`` deep.

    A drip edge is a bent angle, not a bar: a flat leg nailed to the roof furring under the
    roofing, and a leg turned down at the outboard end so the water leaves the roof clear of
    everything behind it. Drawn as one solid box the piece reads as a length of stock hung in
    front of the roof edge — it laps nothing, and nothing can be seen to lap it, which is the
    whole point of the piece.

    Same frame as :func:`open_channel_bands`: offsets run across the thickness from the
    *inboard* (roof) end, drops run down from the run's top. The lap leg occupies the top of
    the section across the full thickness; the turn-down hangs off its outboard end for the
    rest of the depth. Both are a shell thick, clamped like the channel's so a shallow or
    narrow run still resolves as an angle rather than as a solid.
    """
    shell = min(GUTTER_SHELL_M, thickness_m / 3.0, depth_m / 3.0)
    return (
        ("lap", 0.0, thickness_m, shell, 0.0),
        ("drip", thickness_m - shell, shell, depth_m, shell),
    )


def formed_edge_bands(thickness_m: float, depth_m: float) -> tuple[Band, Band, Band]:
    """A formed edge trim ``thickness_m`` deep in plan, ``depth_m`` tall: cleat, face, hem.

    The piece capping a wrapped (continuous standing-seam) roof edge. Drawn as one solid box
    it is a billet of aluminium as wide as the joint is deep — the same misreading the gutter
    had before it became a channel. Sheet metal is a *surface*: what the eye reads at this
    edge is a cleat lying on the roof plane, a face turning down over the joint, and the hem
    the fabricator folds back under that face's bottom edge.

    That hem is not decoration. A raw cut edge of sheet metal is sharp, it oil-cans, and it
    holds a bead of water against the wall by surface tension; folding it back stiffens the
    leg and throws the drip clear. It is the single most characteristic feature of formed
    trim, and a flat band shows none of it.

    Same frame as :func:`open_channel_bands`: offsets run across the thickness from the
    *inboard* end, drops run down from the top. The cleat spans the full thickness at the
    top; the face hangs off its outboard end for the rest of the depth; the hem returns
    inboard along the bottom, stopping at the face's inner surface so the fold reads as a
    fold rather than as two solids sharing a corner. The return is clamped so a shallow or
    narrow run still resolves rather than folding back past its own cleat.
    """
    shell = min(GUTTER_SHELL_M, thickness_m / 3.0, depth_m / 3.0)
    hem = min(2.0 * shell, max(0.0, thickness_m - 2.0 * shell))
    return (
        ("cleat", 0.0, thickness_m, shell, 0.0),
        ("face", thickness_m - shell, shell, depth_m, shell),
        ("hem", thickness_m - shell - hem, hem, depth_m, depth_m - shell),
    )
