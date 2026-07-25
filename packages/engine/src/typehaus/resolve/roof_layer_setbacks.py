"""Roof-plane datum + per-layer edge setbacks shared by the resolver and both 3D emitters.

Distinct from :mod:`typehaus.resolve.roof_edge` (B2), which emits wall→roof closure and
fascia/soffit trim *members* during the framing stage: this module computes the pure
geometry the envelope stage and the roof-shell emitters (glTF + three.js) share.

Two derived quantities keep the 3D roof integrated with the wall stacks, per the golden
eave reference (``tests/fixtures/catlin_reference/scripts/roof_wall_eave_detail_ifc.py``
and ``houses/catlin/notes/roof_wall_eave_detail.md``):

* :func:`deck_rise_m` — how far the rafter-top (deck) plane sits **above** the bearing
  plate top. Only the birdsmouth seat sinks below the plate; the rest of the structure
  depth rises above it. ``ResolvedRoof.eave_z_m`` is the deck plane at the footprint
  edge; ``ResolvedRoof.bearing_z_m`` is the plate top.
* :func:`layer_edge_setbacks` — per-layer plan setbacks from the roof footprint edge
  (the wall cladding outer face) so each above-structure roof layer clips at its own
  wall-stack face: the deck at the wall-sheathing face, the foam at the wall-furring
  inner face, the batten/furring at the wall-furring outer face, and the metal roofing
  0.6" proud of the furring. Serialized setbacks are final *plan* positions; the
  emitters compensate for the horizontal drift the perpendicular (mitered) layer
  offsetting introduces at the eaves (see the emitter's ``_layer_inset_rect``).

Vertical measurement convention: the birdsmouth depth is measured vertically (matching
the member IR's vertical ``z0_m``/``z1_m``), ~0.6" from a strict perpendicular reading —
accepted. Rake clip rules are extrapolated from the eave-only reference drawing.
"""

from __future__ import annotations

from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch

# Reference birdsmouth fallback when the bearing wall's stud depth is unknown.
_BIRDSMOUTH_FALLBACK_M = inch(1.17).meters
# The metal roofing runs 0.6" past the wall furring's outer face (reference drip lap).
_METAL_PROUD_M = inch(0.6).meters


def above_structure_layers(assembly) -> list:
    """The assembly layers outboard of the structure — everything the sky sees.

    Single source of truth for the layer ordering the setbacks are keyed to; the glTF
    emitter and the three.js viewer (``roofGeometry.ts aboveStructureLayers``) mirror it.
    """
    if assembly is None:
        return []
    last = -1
    for index, layer in enumerate(assembly.layers):
        if layer.function is LayerFunction.STRUCTURE:
            last = index
    return list(assembly.layers[last + 1:])


def deck_rise_m(roof_assembly, bearing_wall_assembly, pitch) -> float | None:
    """Deck-plane rise above the bearing plate top for a rafter-framed roof.

    ``structure depth − birdsmouth`` where ``birdsmouth = bearing stud depth × (rise/run)``
    (fallback: the reference 1.17"). Returns ``None`` for truss-framed roofs and roofs
    without a framed STRUCTURE layer — those keep ``eave_z_m == plate top`` (the truss
    framer self-corrects via its raised-heel delta).
    """
    if roof_assembly is None:
        return None
    structure = next((layer for layer in roof_assembly.layers
                      if layer.function is LayerFunction.STRUCTURE
                      and layer.framing is not None), None)
    if structure is None or structure.framing.roof_frame == "truss":
        return None
    birdsmouth = _BIRDSMOUTH_FALLBACK_M
    if bearing_wall_assembly is not None and pitch is not None:
        stud = next((layer for layer in bearing_wall_assembly.layers
                     if layer.function is LayerFunction.STRUCTURE), None)
        if stud is not None:
            birdsmouth = stud.thickness.meters * (pitch.rise / pitch.run)
    return max(structure.thickness.meters - birdsmouth, 0.0)


# --- per-layer edge setbacks ---------------------------------------------------------

def _wall_clip_setbacks(wall) -> dict[str, float]:
    """Setbacks (m, positive inward) from a wall's cladding outer face per clip rule.

    ``wall`` is a ``ResolvedWall``; its resolved depth layers run interior → exterior.
    """
    layers = list(wall.depth_layers())
    sheathing_index = max((index for index, layer in enumerate(layers)
                           if layer.function == "sheathing"), default=None)
    furring_index = max((index for index, layer in enumerate(layers)
                         if layer.function == "furring"), default=None)
    cladding = sum(layer.thickness_m for layer in layers if layer.function == "cladding")
    if furring_index is not None:
        batten = sum(layer.thickness_m for layer in layers[furring_index + 1:])
        foam = sum(layer.thickness_m for layer in layers[furring_index:])
    else:
        batten = foam = cladding
    if sheathing_index is not None:
        deck = sum(layer.thickness_m for layer in layers[sheathing_index + 1:])
    else:
        deck = foam
    return {"deck": deck, "foam": foam, "batten": batten, "metal": batten - _METAL_PROUD_M}


def _layer_group(function: LayerFunction, previous: str | None) -> str | None:
    """Clip-rule group of one above-structure layer (membranes ride the layer below)."""
    if function is LayerFunction.SHEATHING:
        return "deck"
    if function is LayerFunction.INSULATION:
        return "foam"
    if function in (LayerFunction.AIRGAP, LayerFunction.FURRING):
        return "batten"
    if function is LayerFunction.CLADDING:
        return "metal"
    if function is LayerFunction.MEMBRANE:
        return previous or "deck"
    return previous


def _edge_wall(model, roof, edge: str, bearing_walls: list):
    """The wall whose stack governs one footprint edge.

    Eave edges use the nearest bearing wall. Rake edges use the exterior wall whose
    outermost-layer polygon touches that footprint edge (the same cladding polygon
    ``_resolve_roof`` laps the footprint out to); fallback: the first bearing wall.
    """
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    bounds = {"west": min(xs), "east": max(xs), "south": min(ys), "north": max(ys)}
    axis = 0 if edge in ("west", "east") else 1
    eave_edges = (("south", "north") if roof.ridge_direction == "x" else ("west", "east"))
    if edge in eave_edges:
        if not bearing_walls:
            return None
        return min(bearing_walls,
                   key=lambda wall: abs(wall.axis[0][axis] - bounds[edge]))
    tolerance = 0.02
    for wall in model.walls:
        if wall.storey != roof.storey or not wall.depth_layers():
            continue
        outer = wall.depth_layers()[-1].polygon
        if outer and all(abs(point[axis] - bounds[edge]) > tolerance for point in outer):
            continue
        if outer and any(abs(point[axis] - bounds[edge]) <= tolerance for point in outer):
            return wall
    return bearing_walls[0] if bearing_walls else None


def layer_edge_setbacks(model, roof) -> tuple[dict, ...]:
    """Per-layer plan setbacks (m) from the footprint edge, one dict per layer.

    Entries follow the ``above_structure_layers`` ordering:
    ``{"layer": name, "west": m, "east": m, "south": m, "north": m}``. Positive is
    inward from the footprint edge; the metal roofing's may be negative (an outset).
    """
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    layers = above_structure_layers(assembly)
    if not layers:
        return ()
    element = model.plan.by_tag(roof.tag)
    bearing_refs = getattr(element, "bearing_refs", ()) or ()
    bearing_walls = [wall for tag in bearing_refs if (wall := model.wall(tag)) is not None]
    clips: dict[str, dict[str, float]] = {}
    for edge in ("west", "east", "south", "north"):
        wall = _edge_wall(model, roof, edge, bearing_walls)
        clips[edge] = (_wall_clip_setbacks(wall) if wall is not None
                       else {"deck": 0.0, "foam": 0.0, "batten": 0.0, "metal": 0.0})
    entries: list[dict] = []
    group: str | None = None
    for layer in layers:
        group = _layer_group(layer.function, group)
        entries.append({
            "layer": layer.name,
            **{edge: (clips[edge][group] if group is not None else 0.0)
               for edge in ("west", "east", "south", "north")},
        })
    return tuple(entries)
