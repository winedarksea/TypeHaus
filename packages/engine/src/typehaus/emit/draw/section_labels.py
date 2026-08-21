"""Layer-label ladders for the section cut (→ 30 §Details, #36 true-dimension labels).

Split out of ``section.py`` unchanged. A ladder names every band of an assembly the cut
passes through: entries are collected per element, laid into a single text column left of
the crop, then dodged against every *other* element's column so two walls' ladders cannot
interleave. Emission happens once, after all cutting, which is why the collect/emit pair
lives here rather than inside the per-family cut handlers.
"""

from __future__ import annotations

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


def roof_layer_ladder(roof, detail_layers, crop, z_at, ladder_labels,
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
    """
    if ladder_labels is None or crop is None or not detail_layers:
        return
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    # The up-slope end of the crop is the higher one; probe a fifth of the way in from it.
    up_is_hi = z_at(u_hi) >= z_at(u_lo)
    probe = (u_hi - 0.2 * (u_hi - u_lo)) if up_is_hi else (u_lo + 0.2 * (u_hi - u_lo))
    z_probe = z_at(probe)
    z_lo, z_hi = min(cz0, cz1), max(cz0, cz1)

    entries = []
    for (layer, d0, d1) in detail_layers:
        mid_z = z_probe - (d0 + d1) / 2.0
        if not (z_lo <= mid_z <= z_hi):  # band off the sheet — labelling it points at nothing
            continue
        inches = (d1 - d0) / M_PER_IN
        entries.append(LabelSpec(
            text=f'{layer.name} {inches:.3g}"',
            target=(probe / M_PER_IN, mid_z / M_PER_IN),
            key=(roof.uid, layer.name)))
    if not entries:
        return
    # Outermost first, so the column reads top-down in the same order as the drawing.
    entries.reverse()
    ladder_labels.extend(place_column(
        entries, x=u_lo / M_PER_IN - 1.0, z_top=z_hi / M_PER_IN - 1.0,
        step_pt=LABEL_RUNG_PT, height_pt=TEXT_PT, align="right", scale=scale))


def emit_ladders(b, ladder_labels, scale: float | None = None) -> None:
    """Draw the collected ladders last, over the cut geometry and dodged against each other.

    Two walls' ladders share the text column at the crop's left edge and would otherwise
    interleave.
    """
    for placed in dodge(ladder_labels, scale=scale):
        mid_u, target_z = placed.spec.target
        rung_z = placed.at[1]
        if target_z:
            # A roof layer is a sloped band: its layers separate in *z* at a given u, so a
            # flat rung cannot tell them apart the way it can a wall's vertical layers. The
            # rung stays horizontal out to the band's own u and then elbows to the point on
            # it, which keeps the text column aligned while the pointers fan.
            b.add(Leader(anchor=NamedPoint(xy=(mid_u, target_z)), at=placed.at,
                         to=(mid_u, rung_z), text=placed.spec.text,
                         height_pt=placed.height_pt, layer="A-ANNO-TEXT"))
            continue
        # Horizontal, leadered back to the layer at the rung's own height — the rung moves
        # with the label when dodged, so the leader line stays flat and never crosses text.
        b.add(Leader(anchor=NamedPoint(xy=(mid_u, rung_z)), at=placed.at,
                     to=(mid_u, rung_z), text=placed.spec.text,
                     height_pt=placed.height_pt, layer="A-ANNO-TEXT"))
