"""Layer-label ladders for the section cut (→ 30 §Details, #36 true-dimension labels).

Split out of ``section.py`` unchanged. A ladder names every band of an assembly the cut
passes through: entries are collected per element, laid into a single text column left of
the crop, then dodged against every *other* element's column so two walls' ladders cannot
interleave. Emission happens once, after all cutting, which is why the collect/emit pair
lives here rather than inside the per-family cut handlers.
"""

from __future__ import annotations

from typing import NamedTuple

from typehaus.emit.draw.annotate import LEGACY_IN_PER_PT, LabelSpec, dodge, place_column
from typehaus.emit.draw.scene import Leader, NamedPoint
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.quantities import M_PER_IN

# Vertical step between successive layer labels, **points**. A rung step is a property of
# the lettering it separates, not of the building, which is why it stopped being the 2.6
# model inches it was authored as — that number is this one at the frameless conversion.
LABEL_RUNG_PT = 2.6 / LEGACY_IN_PER_PT


def wall_layer_ladder(wall, label_entries, wall_top, crop, ladder_labels,
                      scale: float | None = None) -> None:
    """Name every layer of a wall's assembly, hung from a single anchor at its top.

    The whole ladder hangs from one anchor: the wall's top as seen in the crop. Rungs step
    down at a uniform ``LABEL_RUNG_PT`` so a sloped/eave cut, where each layer terminates at
    its own height, cannot interleave rungs from different layers. Stacked vertically
    because at detail scale a membrane and its neighbours are hundredths of an inch apart —
    labels sharing one baseline overprint into a smear.
    """
    if not label_entries or ladder_labels is None:
        return
    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        z_top = min(wall_top, max(cz0, cz1))
        text_u = min(cu0, cu1) / M_PER_IN - 1.0
    else:
        z_top = wall_top
        text_u = min(mid_u for (_lab, mid_u) in label_entries.values()) - 14.0
    # Sorted by mid_u (innermost layer first): the text column sits left of the cut, so
    # ascending targets top-to-bottom keep the horizontal leader lines nested, not crossed.
    entries = [LabelSpec(text=label, target=(mid_u, 0.0), key=(wall.uid, name))
               for name, (label, mid_u) in
               sorted(label_entries.items(), key=lambda item: item[1][1])]
    ladder_labels.extend(place_column(entries, x=text_u, z_top=z_top / M_PER_IN - 1.0,
                                      step_pt=LABEL_RUNG_PT, height_pt=TEXT_PT,
                                      align="right", scale=scale))


class DrawnBand(NamedTuple):
    """One assembly band exactly as it reached the sheet.

    ``points`` is the outline in model **inches**, already sliced and cropped — the same
    tuple handed to the ``Polyline``/``Hatch`` node. ``thickness_in`` is the assembly's
    spec thickness, which is what the label says; it is deliberately *not* what the label
    points at, because a layer of a sloped roof is offset perpendicular to the slope and
    so occupies more than its own thickness of a plumb section.
    """

    name: str
    thickness_in: float
    points: tuple[tuple[float, float], ...]


def _span_at(points, u: float) -> tuple[float, float] | None:
    """Where the plumb line at ``u`` enters and leaves a band, or ``None`` if it misses."""
    zs: list[float] = []
    count = len(points)
    for index in range(count):
        (u0, z0), (u1, z1) = points[index], points[(index + 1) % count]
        if u0 == u1:
            if u0 == u:
                zs.extend((z0, z1))
        elif min(u0, u1) <= u <= max(u0, u1):
            zs.append(z0 + (z1 - z0) * (u - u0) / (u1 - u0))
    return (min(zs), max(zs)) if zs else None


def _point_on_band(outlines, probe: float) -> tuple[float, float] | None:
    """The point the leader lands on: mid-band, on the plumb line nearest ``probe``.

    A layer can reach the sheet as more than one outline — both planes of a gable, or a
    band the crop cut in two — so the nearest one to the shared probe station wins, and a
    band that stops short of the probe is pointed at inside its own u-range rather than
    somewhere off its end.
    """
    best = None
    for points in outlines:
        us = [u for (u, _z) in points]
        u = min(max(probe, min(us)), max(us))
        span = _span_at(points, u)
        if span is None:
            continue
        candidate = (abs(u - probe), u, (span[0] + span[1]) / 2.0)
        if best is None or candidate < best:
            best = candidate
    return None if best is None else (best[1], best[2])


def roof_layer_ladder(roof, bands, crop, z_at, ladder_labels,
                      scale: float | None = None) -> None:
    """Name every band of a roof's assembly, the way ``wall_layer_ladder`` names a wall's.

    Without this the one drawing whose subject is the roof-to-wall junction labelled the
    wall's nine layers and none of the roof's — the reader could see that something six
    inches thick sat above the rafters but not that it was two staggered courses of
    polyiso, nor which of the three thin dark bands above it was the vapour barrier and
    which the underlayment. On a nailbase roof that distinction is the whole assembly.

    Probed at one station up-slope of the eave rather than at the cut's own edge: the eave
    end is where the water chain, the corner trim and the wall head all crowd into two
    inches of drawing, and a fan of nine leaders into that is unreadable. Up-slope the
    bands are clear of everything.

    ``bands`` are :class:`DrawnBand` records — the outlines the caller actually drew — and every
    leader is aimed by measuring one, never by re-deriving where it ought to be. That is
    the point of taking them: the first version walked the assembly's own layer spans and
    stepped down from the roof plane by each layer's thickness, which is a *perpendicular*
    offset being spent as a vertical one. On catlin's 4:12 the two disagree by 5.4%, so the
    stack's labels drifted a growing fraction of an inch down into their neighbours: the
    roofing pointed at the vent mat, the vent mat and the underlayment both at the deck,
    the deck at the polyiso, and the vapour barrier at the ZIP below it. Five of nine named
    the wrong band, and none of them looked wrong — every leader landed cleanly on *a*
    layer. Measuring the drawn outline cannot drift, because there is nothing left to
    disagree with.
    """
    if ladder_labels is None or crop is None or not bands:
        return
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    # The up-slope end of the crop is the higher one; probe a fifth of the way in from it.
    up_is_hi = z_at(u_hi) >= z_at(u_lo)
    probe = (u_hi - 0.2 * (u_hi - u_lo)) if up_is_hi else (u_lo + 0.2 * (u_hi - u_lo))
    probe_in = probe / M_PER_IN
    z_hi = max(cz0, cz1)

    outlines: dict[str, list] = {}
    thickness: dict[str, float] = {}
    for band in bands:
        outlines.setdefault(band.name, []).append(band.points)
        thickness.setdefault(band.name, band.thickness_in)

    entries = []
    for name, band_outlines in outlines.items():
        point = _point_on_band(band_outlines, probe_in)
        if point is None:
            continue
        entries.append(LabelSpec(text=f'{name} {thickness[name]:.3g}"',
                                 target=point, key=(roof.uid, name)))
    if not entries:
        return
    # **Highest band first**, off the targets themselves — not off each band's offset from
    # the structure datum, which can disagree with where the band lands on a sloped cut.
    # ``place_column`` fills top-down, so sorting on drawn elevation is what makes rung
    # order and band order the same order, and it is the whole difference between a ladder
    # and a cat's cradle.
    entries.sort(key=lambda entry: -entry.target[1])
    ladder_labels.extend(place_column(
        entries, x=u_lo / M_PER_IN - 1.0, z_top=z_hi / M_PER_IN - 1.0,
        step_pt=LABEL_RUNG_PT, height_pt=TEXT_PT, align="right", scale=scale))


def emit_ladders(b, ladder_labels, scale: float | None = None) -> None:
    """Draw the collected ladders last, over the cut geometry and dodged against each other.

    Two walls' ladders share the text column at the crop's left edge and would otherwise
    interleave.

    **``to`` is where the arrowhead goes, and it is the only end any renderer draws.** All
    three back ends — matplotlib's ``annotate`` in ``pdf_writer``, ``add_leader`` in
    ``dxf_writer``, and the viewer's ``DetailCanvas`` — draw the single segment ``at → to``
    and never read ``anchor``, which is provenance for hit-testing. ``to`` must aim at the
    band itself so the leader runs as one diagonal; it cannot tangle because
    ``roof_layer_ladder`` sorts by target elevation and ``place_column`` steps rungs down in
    that same order, so the two sequences descend together and order-preserving lines do
    not cross.
    """
    for placed in dodge(ladder_labels, scale=scale):
        mid_u, target_z = placed.spec.target
        rung_z = placed.at[1]
        # A wall's layers separate in *u* and run the full height of the cut, so a flat rung
        # at the label's own elevation already lands inside the band; ``target_z`` is 0 to
        # say so. A roof's separate in *z*, and nothing but the band's own elevation will do.
        tip = (mid_u, target_z if target_z else rung_z)
        b.add(Leader(anchor=NamedPoint(xy=tip), at=placed.at, to=tip,
                     text=placed.spec.text, height_pt=placed.height_pt,
                     layer="A-ANNO-TEXT"))
