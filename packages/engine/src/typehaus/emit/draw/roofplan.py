"""Roof-plan drawing from resolved roof planes (M3 A-106).

Beyond the plane outlines this now reads like a roof plan: dashed ridge lines,
downslope arrows with the authored pitch at each gable plane, the bearing-wall face
ghosted below the roof, and an eave-overhang dimension per distinct overhang value.
Valleys/hips are not drawn because the constrained roof vocabulary (gable/shed over
parallel bearing walls) cannot produce them — nothing is fabricated.
"""

from __future__ import annotations

from typehaus.emit.draw.scene import (
    ArchDimension,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, ResolvedRoof

# Half-length of a slope arrow in inches (the writers draw the glyph from its params).
_ARROW_HALF_IN = 24.0
# Overhang dimensions inset this far from the footprint corner along the edge.
_OVERHANG_INSET_M = 1.2
# The roof tag label steps this far (inches) off the ridge line so neither hides the other.
_LABEL_CLEAR_IN = 30.0
# Overhangs shorter than this (inches) are construction laps, not designed eaves.
_MIN_OVERHANG_IN = 1.0


def _in(p: tuple[float, float]) -> tuple[float, float]:
    return (p[0] / M_PER_IN, p[1] / M_PER_IN)


def build_roof_plan(model: ResolvedModel) -> Scene:
    """Draw gable/shed plane outlines, ridges, slope arrows, and eave dims."""
    b = SceneBuilder(name="roof-plan", units="in")
    for roof in model.roofs:
        footprint = tuple(_in(p) for p in roof.footprint)
        b.add(Polyline(points=footprint, layer="A-ROOF", closed=True, lineweight=0.45,
                       uid=roof.uid, tag=roof.tag))
        xs = [point[0] for point in roof.footprint]
        ys = [point[1] for point in roof.footprint]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        if roof.ridge_direction == "x":
            ridge = ((minx, (miny + maxy) / 2), (maxx, (miny + maxy) / 2))
        else:
            ridge = (((minx + maxx) / 2, miny), ((minx + maxx) / 2, maxy))
        b.add(Polyline(points=tuple(_in(p) for p in ridge), layer="A-ROOF",
                       lineweight=0.8, linetype="DASHED",
                       uid=roof.uid, tag=f"{roof.tag}-ridge"))
        authored = model.plan.by_tag(roof.tag)
        pitch = getattr(authored, "pitch", None)
        pitch_label = (f"{pitch.rise:g}:{pitch.run:g}" if pitch is not None
                       else "resolved")
        _emit_slope_arrows(b, roof, (minx, maxx, miny, maxy), pitch_label)
        _emit_overhangs(b, model, roof, (minx, maxx, miny, maxy))
        label_x, label_y = _in(((minx + maxx) / 2, (miny + maxy) / 2))
        if roof.ridge_direction == "x":
            label_y -= _LABEL_CLEAR_IN  # step below the horizontal ridge line
        else:
            label_x -= _LABEL_CLEAR_IN * 2  # step left of the vertical ridge line
            label_y -= _LABEL_CLEAR_IN  # ...and below the slope arrow's pitch note
        b.add(Text(anchor=(label_x, label_y), content=f"{roof.tag}  {pitch_label}",
                   height=3.5, align="center"))
    return b.build()


def _emit_slope_arrows(b: SceneBuilder, roof: ResolvedRoof,
                       bbox: tuple[float, float, float, float], pitch_label: str) -> None:
    """One downslope arrow + pitch note per plane (two for a gable, one for a shed).

    A shed's low side is not recorded on the resolved roof, so only gables — where both
    planes fall away from the synthesized mid ridge — get arrows; the pitch text at the
    roof center covers the rest.
    """
    if roof.form != "gable":
        return
    minx, maxx, miny, maxy = bbox
    midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
    if roof.ridge_direction == "x":
        # Planes north and south of the ridge; downslope is away from y = midy.
        planes = (((midx, (midy + miny) / 2), 270.0), ((midx, (midy + maxy) / 2), 90.0))
    else:
        planes = ((((midx + minx) / 2, midy), 180.0), (((midx + maxx) / 2, midy), 0.0))
    for center, rotation in planes:
        b.add(Symbol(name="span-arrow", insert=_in(center), rotation=rotation,
                     scale=_ARROW_HALF_IN, layer="A-ROOF", uid=roof.uid,
                     params={"width_in": _ARROW_HALF_IN}))
        cx, cy = _in(center)
        b.add(Text(anchor=(cx + 6.0, cy + 6.0), content=pitch_label, height=3.0,
                   layer="A-ANNO-TEXT", align="left"))


def _emit_overhangs(b: SceneBuilder, model: ResolvedModel, roof: ResolvedRoof,
                    bbox: tuple[float, float, float, float]) -> None:
    """Ghost the bearing-wall face and dimension wall face → roof edge per edge value.

    The wall face is the bearing walls' outermost resolved layer (the same cladding
    extent the footprint resolver laps), so the dimension measures the built overhang,
    not the authored axis offset. One ``ArchDimension`` per distinct value (to 1/4"),
    eave edges first, so a uniform overhang reads once instead of four times.
    """
    authored = model.plan.by_tag(roof.tag)
    bearing = [w for w in (model.wall(ref) for ref in
                           getattr(authored, "bearing_refs", ()) or ())
               if w is not None]
    if not bearing:
        return
    clad_pts = []
    for wall in bearing:
        layers = wall.depth_layers()
        clad_pts.extend(layers[-1].polygon if layers else wall.axis)
    if not clad_pts:
        return
    fx0, fx1, fy0, fy1 = bbox
    cx0 = max(min(p[0] for p in clad_pts), fx0)
    cx1 = min(max(p[0] for p in clad_pts), fx1)
    cy0 = max(min(p[1] for p in clad_pts), fy0)
    cy1 = min(max(p[1] for p in clad_pts), fy1)
    overhangs = {"west": cx0 - fx0, "east": fx1 - cx1,
                 "south": cy0 - fy0, "north": fy1 - cy1}
    if max(overhangs.values()) / M_PER_IN >= _MIN_OVERHANG_IN:
        b.add(Polyline(points=(_in((cx0, cy0)), _in((cx1, cy0)),
                               _in((cx1, cy1)), _in((cx0, cy1))),
                       layer="A-WALL-BELW", closed=True, lineweight=0.25,
                       linetype="DASHED", uid=roof.uid, tag=f"{roof.tag}-wall-below"))
    edge_order = (("south", "north", "west", "east") if roof.ridge_direction == "x"
                  else ("west", "east", "south", "north"))
    x_at = fx0 + min(_OVERHANG_INSET_M, (fx1 - fx0) / 2)
    y_at = fy0 + min(_OVERHANG_INSET_M, (fy1 - fy0) / 2)
    spans = {"south": ((x_at, fy0), (x_at, cy0)), "north": ((x_at, cy1), (x_at, fy1)),
             "west": ((fx0, y_at), (cx0, y_at)), "east": ((cx1, y_at), (fx1, y_at))}
    seen: set = set()
    for edge in edge_order:
        value_in = overhangs[edge] / M_PER_IN
        if value_in < _MIN_OVERHANG_IN:
            continue
        key = round(value_in * 4)  # distinct to the nearest 1/4"
        if key in seen:
            continue
        seen.add(key)
        p0, p1 = spans[edge]
        b.add(ArchDimension(
            kind="linear",
            ends=(NamedPoint(xy=_in(p0), name=f"{roof.tag}-{edge}-roof-edge"),
                  NamedPoint(xy=_in(p1), name=f"{roof.tag}-{edge}-wall-face")),
            p0=_in(p0), p1=_in(p1), offset=0.0, uid=roof.uid,
        ))
