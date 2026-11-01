"""Detail chrome: the material legend band (dimension strings: ``stack_dimensions``).

The legend reads the resolved layer thicknesses rather than authored numbers, so a change to
an assembly re-labels the drawing instead of leaving a stale legend on the sheet.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    LAYER,
    LEGEND_ROW_PITCH_IN,
    LEGEND_SWATCH_IN,
    TEXT_HEIGHT_IN,
)
from typehaus.emit.draw.detail_components.geometry import rect_points
from typehaus.emit.draw.lineweights import LIGHT
from typehaus.emit.draw.plan_labels import inches_fraction
from typehaus.emit.draw.scene import Hatch, IRNode, Polyline, Text
from typehaus.quantities import M_PER_IN


def _participating_layers(model, derived):
    """``(material_ref, thickness_in, function)`` for every cut layer in this detail."""
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    out: list[tuple[str, float, str]] = []
    for wall in condition_walls(model, derived.condition):
        for layer in wall.layers:
            # Cavity fills are included: a cavity IS drawn in the cut (``section_cavity``
            # emits it from the assembly since the IR gives it no solid), so leaving it out
            # would break this module's rule that the strip names what the cut is made of.
            # ``_paper_legend`` intersects this list with what the scene drew, so nothing
            # here can over-name.
            thickness = layer.film_m if layer.coating else layer.thickness_m
            out.append((layer.material_ref, thickness / M_PER_IN, layer.function))
    tags = derived.condition.element_tags
    for roof in model.roofs:
        # By **assembly** as well as by element tag. A wall/roof condition is keyed on the
        # two assemblies it joins (``EXT_2X6|ROOF``), never on the roof
        # element's own tag (``RF-HOUSE``), so matching tag alone misses roof-heavy details
        # like the eave, dropping layers such as the underlayment and the vent mat.
        if roof.tag not in tags and roof.assembly not in tags:
            continue
        asm = model.plan.library.resolve_assembly(roof.assembly)
        if asm is None:
            continue
        for layer in asm.layers:
            out.append((layer.material_ref, layer.thickness.meters / M_PER_IN,
                        layer.function))
            # A roof's fills reach no ``ResolvedLayer`` at all — the wall loop above gets
            # them for free, this one has to ask the assembly — and on a flash-and-batt roof
            # they are the two thickest things in the drawing.
            for fill in layer.cavity_fills:
                out.append((fill.material_ref,
                            layer.cavity_thickness(fill).meters / M_PER_IN,
                            layer.function))
    return out


#: Materials a detail **component** draws with rather than an assembly layer, so
#: :func:`_participating_layers` — which walks walls and roofs — can never see them and the
#: legend never named them. The dark red band lapping the cladding head is the drawing's
#: answer to "where does the water go", and until this list existed a reader had no way to
#: learn what it was.
#:
#: **They carry no thickness, deliberately.** Every other row states its layer's resolved
#: thickness; these are drawn at ``SHEET_METAL.thickness_in``, which is a *schematic* 0.5"
#: against real flashing's ~0.025" (``config.SheetMetalConfig`` says so in as many words).
#: Printing that number would put one twenty-fold lie on a sheet of true ones. The swatch and
#: the name are what the reader needs; the gauge belongs in the notes.
#:
#: Bounded on purpose: ``metal`` (which is hardware — the ridge hanger), ``sealant``, ``soil``
#: and the rest stay out. The strip is finite, and it says what the CUT is made of rather than
#: what every schematic overlay in the drawing happens to be drawn with.
_COMPONENT_MATERIALS = ("flashing", "gutter")


def _cut_trim_materials(model, derived) -> tuple[str, ...]:
    """Materials of the resolved trim this condition's elements own (opening or wall base).

    Candidates only: ``_with_component_materials`` keeps the ones the scene actually draws.
    """
    tags = set(derived.condition.element_tags)
    return tuple(dict.fromkeys(
        s.material for s in model.solids
        if s.category == "cladding_trim" and s.host_ref in tags and s.material
        and s.body_mesh is not None))


def _with_component_materials(seen: dict[str, float | None], drawn: set[str] | None,
                              extra: tuple[str, ...] = ()) -> None:
    """Append the component materials this drawing actually reached, in a fixed order.

    ``extra`` carries the cut's resolved trim materials, so a catalog head that replaces the
    flashing still gets a swatch. Only when ``drawn`` is known: a legend may name nothing the
    cut did not reach
    (``test_detail_legibility.test_the_legend_only_names_materials_the_cut_actually_reached``),
    and without the scene there is no way to tell.
    """
    if drawn is None:
        return
    for material in (*_COMPONENT_MATERIALS, *extra):
        if material in drawn and material not in seen:
            seen[material] = None


def _legend_label(material: str, thickness: float | None) -> str:
    return material if thickness is None else f'{material}  {inches_fraction(thickness)}'


def drawn_materials(scene) -> set[str]:
    """Every material that actually reaches the page, off the ``Hatch`` nodes themselves.

    ``_participating_layers`` reads the *assemblies* in the condition, which is not the same
    question: a layer whose band falls outside the crop, or which the cut misses entirely,
    is in the assembly and not in the drawing. Legending it invites a reader to look for
    something that is not there, and it is why the band ran a third longer than it needed to.
    """
    from typehaus.emit.draw.scene import Hatch, Polyline

    return {node.material for node in getattr(scene, "nodes", ())
            if isinstance(node, (Hatch, Polyline)) and node.material}


def material_legend(model, derived, u_left: float, z_top: float,
                    band=None, drawn: set[str] | None = None) -> list[IRNode]:
    """One swatch + label per distinct material in the cut, with its resolved thickness.

    With a ``band`` — ``(x, y, w, h)`` paper inches out of ``Frame.bands`` — the legend is
    laid out **in paper space**, in a strip whose size is a property of the card. It runs in
    columns across the strip rather than down a single tall list, because a legend that grew
    downward was the thing measuring itself against the drawing.
    """
    if band is not None:
        return _paper_legend(model, derived, band, drawn)
    seen: dict[str, float | None] = {}
    order: list[str] = []
    for material, thickness, _function in _participating_layers(model, derived):
        if material and material not in seen:
            seen[material] = thickness
            order.append(material)
    _with_component_materials(seen, drawn, _cut_trim_materials(model, derived))
    order.extend(m for m in seen if m not in order)
    if not order:
        return []
    from typehaus.emit.draw.palette import library_fill, library_hatch

    nodes: list[IRNode] = [
        Text(anchor=(u_left, z_top + 3.0), content="MATERIALS", height=TEXT_HEIGHT_IN,
             layer="A-ANNO-TEXT")
    ]
    for index, material in enumerate(order):
        y1 = z_top - index * LEGEND_ROW_PITCH_IN
        y0 = y1 - LEGEND_SWATCH_IN
        # ``metal`` maps to a no-overlay fill in both writers (and the UI), so the swatch
        # reads as its material fill when the material has no hatch family of its own.
        pattern = library_hatch(model.plan.library, material) or "metal"
        boundary = rect_points(u_left, y0, u_left + LEGEND_SWATCH_IN, y1)
        nodes.append(Hatch(boundary=boundary, pattern=pattern, layer=LAYER,
                           material=material, fill=library_fill(model.plan.library, material)))
        nodes.append(Polyline(points=boundary, layer=LAYER, closed=True, lineweight=LIGHT))
        nodes.append(Text(anchor=(u_left + LEGEND_SWATCH_IN + 1.5, (y0 + y1) / 2),
                          content=_legend_label(material, seen[material]),
                          height=TEXT_HEIGHT_IN, layer="A-ANNO-TEXT"))
    return nodes


#: Paper-space legend metrics, inches.
_SWATCH_IN = 0.14
_ROW_PITCH_IN = 0.17
#: Three columns across a 6.45" strip. The widest label the catalog produces is
#: ``roof-underlayment-synthetic  0.06"`` — 33 monospace characters, 1.85" at _LEGEND_PT,
#: which clears this with the swatch and its gap.
_COL_W_IN = 2.15
_LEGEND_PT = 6.5


def _paper_legend(model, derived, band, drawn=None) -> list[IRNode]:
    from typehaus.emit.draw.palette import library_fill, library_hatch

    seen: dict[str, float | None] = {}
    for material, thickness, _function in _participating_layers(model, derived):
        if material and material not in seen and (drawn is None or material in drawn):
            seen[material] = thickness
    _with_component_materials(seen, drawn, _cut_trim_materials(model, derived))
    if not seen:
        return []
    x, y, w, h = band
    rows = max(1, int(h / _ROW_PITCH_IN) - 1)
    nodes: list[IRNode] = [
        Text(anchor=(x, y + h - _ROW_PITCH_IN * 0.4), content="MATERIALS",
             height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper")
    ]
    for index, (material, thickness) in enumerate(seen.items()):
        column, row = divmod(index, rows)
        cx = x + column * _COL_W_IN
        if cx + _COL_W_IN > x + w + 1e-9:
            # The strip is full — a legend may not push the drawing off its own card. Say so
            # rather than stopping mid-list: a legend that quietly ends is read as complete,
            # and a reader then goes looking for a material the drawing never named.
            nodes.append(Text(
                anchor=(x + w, y + h - _ROW_PITCH_IN * 0.4), align="right",
                content=f"+{len(seen) - index} more (see notes)",
                height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper"))
            break
        cy = y + h - _ROW_PITCH_IN * (row + 1.6)
        boundary = rect_points(cx, cy, cx + _SWATCH_IN, cy + _SWATCH_IN)
        library = model.plan.library
        nodes.append(Hatch(boundary=boundary, pattern=library_hatch(library, material) or "metal",
                           layer=LAYER, material=material, space="paper",
                           fill=library_fill(library, material)))
        nodes.append(Polyline(points=boundary, layer=LAYER, closed=True, lineweight=LIGHT,
                              space="paper"))
        nodes.append(Text(anchor=(cx + _SWATCH_IN + 0.06, cy + _SWATCH_IN / 2),
                          content=_legend_label(material, thickness),
                          height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper"))
    return nodes
