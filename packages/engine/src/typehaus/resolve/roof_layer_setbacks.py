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

# Reference bearing-plate DEPTH for the birdsmouth when the bearing wall's own structure
# layer cannot be read — a nominal 2x4 laid flat. It was written as `inch(1.17)`, which is
# this depth times a 4:12 pitch: the PITCH WAS FUSED INTO THE CONSTANT, so a roof at any
# other pitch whose bearing wall did not resolve got a 4:12 seat cut and nothing said so.
# The two only ever agreed by the accident of this repo having had one roof pitch. Every
# roof here resolves a STRUCTURE layer, so splitting them changes no result today — it
# stops the fallback from being silently wrong the first time one does not.
_BIRDSMOUTH_FALLBACK_PLATE_M = inch(3.5).meters
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


def assembly_layer_spans(assembly) -> list[tuple[object, float, float]]:
    """``(layer, c0_m, c1_m)`` for every layer, cumulative depth interior → exterior.

    The companion to :func:`above_structure_layers`: where that answers *which* layers the
    sky sees, this answers *where each one is*. Four modules ran their own cumulative walk
    over ``assembly.layers`` — the section cut, the joint plan, the eave detail's band
    finder and the vent intake — and each one then re-derived the structure datum from it
    with its own sign convention. Three of the four disagreed at some point in their life.
    """
    if assembly is None:
        return []
    spans: list[tuple[object, float, float]] = []
    cumulative = 0.0
    for layer in assembly.layers:
        thickness = layer.thickness.meters
        spans.append((layer, cumulative, cumulative + thickness))
        cumulative += thickness
    return spans


def structure_datum_m(assembly) -> float:
    """Depth from the assembly's interior face to the *outboard* face of its structure.

    This is the plane ``ResolvedRoof.eave_z_m`` and ``roof_geometry.roof_height_at`` sit on:
    the structure hangs below it, the above-structure stack rises above it. ``0.0`` for an
    assembly with no STRUCTURE layer, which is all such a roof ever had.
    """
    return next((c1 for (layer, _c0, c1) in reversed(assembly_layer_spans(assembly))
                 if layer.function is LayerFunction.STRUCTURE), 0.0)


def deck_rise_m(roof_assembly, bearing_wall_assembly, pitch) -> float | None:
    """Deck-plane rise above the bearing plate top for a rafter-framed roof.

    ``structure depth − birdsmouth`` where ``birdsmouth = bearing stud depth × (rise/run)``
    (fallback depth: a nominal 2x4 plate, taken at the roof's own pitch). Returns ``None``
    for truss-framed roofs, roofs without a framed STRUCTURE layer, and roofs with no pitch
    — those keep ``eave_z_m == plate top`` (the truss framer self-corrects via its
    raised-heel delta).
    """
    if roof_assembly is None:
        return None
    structure = next((layer for layer in roof_assembly.layers
                      if layer.function is LayerFunction.STRUCTURE
                      and layer.framing is not None), None)
    if structure is None or structure.framing.roof_frame == "truss" or pitch is None:
        # No pitch, no seat cut: the birdsmouth IS the plate depth times the slope, so a
        # missing pitch cannot be defaulted without inventing one. Falling back to 4:12
        # here is the same fusion this module just removed from the plate constant.
        return None
    slope = pitch.rise / pitch.run
    depth = _BIRDSMOUTH_FALLBACK_PLATE_M
    if bearing_wall_assembly is not None:
        stud = next((layer for layer in bearing_wall_assembly.layers
                     if layer.function is LayerFunction.STRUCTURE), None)
        if stud is not None:
            depth = stud.thickness.meters
    birdsmouth = depth * slope
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
        # The roof's foam runs out to the back of the wall's VENT, not to the back of the
        # band that holds it open. On a plain rainscreen those are the same plane, because
        # the band is empty. On a truss wall they are not, and in two different ways:
        #
        # * the SWINBURNE outrigger band is 3-1/2" deep with closed-cell foam packed behind
        #   the stick, so the vent is the front 1". Clipping the roof foam at the band's
        #   inner face would hold it 4" back from the footprint edge to clear a gap that is
        #   only 1" — a 3" thermal notch all round the eave that is not in the building;
        # * the CATLIN TRUSS's outer girt is 1-1/2" of SOLID KDAT with its 1/2" vent
        #   authored BEHIND it as its own AIRGAP layer. Read band-minus-fill, that wall
        #   reports 1-1/2" of wood as vent and misses the half inch of actual air, holding
        #   the roof foam half an inch proud of the wall's foam face.
        #
        # ``accessories.rainscreen_cavity_m`` answers both — it is the same question the bug
        # screen and the envelope take-off ask — so this reads it rather than re-deriving it.
        # The band-minus-fill walk stays as the fallback for a stack it declines (a band with
        # no cladding outboard of it is not a rainscreen and vents nothing).
        from typehaus.resolve.accessories import rainscreen_cavity_m

        band = layers[furring_index]
        cavity = rainscreen_cavity_m(wall.layers)
        if cavity is None:
            fill = next((layer for layer in wall.layers
                         if layer.is_cavity and layer.cavity_host == band.name), None)
            cavity = band.thickness_m - (fill.thickness_m if fill is not None else 0.0)
        foam = batten + max(0.0, cavity)
    else:
        batten = foam = cladding
    if sheathing_index is not None:
        deck = sum(layer.thickness_m for layer in layers[sheathing_index + 1:])
    else:
        deck = foam
    return {"deck": deck, "foam": foam, "batten": batten, "metal": batten - _METAL_PROUD_M}


def _layer_group(function: LayerFunction, previous: str | None) -> str | None:
    """Clip-rule group of one above-structure layer (membranes ride the layer below).

    ``previous`` is the group the layer inboard of this one landed in, which is what makes
    the SHEATHING rule position-aware. A nailbase roof has TWO sheathing layers on opposite
    sides of the foam: the inboard one is the deck proper, the outboard one is the top deck
    the metal is clipped to, and it occupies the slot a vented roof's battens occupied. So
    a sheathing layer that appears once the stack has already reached the foam clips as a
    batten, not as a deck — without that it would inherit the deck's much larger setback and
    the top deck would stand proud of its own roofing at every edge.

    :func:`layer_edge_setbacks` applies a second, whole-stack half of the same rule that
    this per-layer walk cannot see: a deck with NO foam and NO batten anywhere above it *is*
    the batten, because the covering is fixed straight to it. See the note there.
    """
    if function is LayerFunction.SHEATHING:
        return "batten" if previous in ("foam", "batten") else "deck"
    if function is LayerFunction.INSULATION:
        return "foam"
    if function in (LayerFunction.AIRGAP, LayerFunction.FURRING):
        return "batten"
    if function is LayerFunction.CLADDING:
        return "metal"
    if function is LayerFunction.MEMBRANE:
        return previous or "deck"
    return previous


def _skinned(model, wall):
    """``wall`` if it carries a weather skin, else the wall whose skin stands in for it.

    A bearing element with no SHEATHING layer and nothing outboard of one has no stack for
    a clip rule to read: every setback comes back 0.0, the roof deck runs out to the
    footprint edge, and the metal ends up 0.6" PROUD of a deck that should be well behind
    it. That is not a hypothetical — a story-and-a-half roof lands on a 2x plate laid flat
    on the deck, which is exactly such an element.

    The skin the roof actually clips against belongs to the wall the plate STANDS ON, which
    is authored as ``Wall.stacks_on``, so ``skin_stand_ins`` resolves it without an
    elevation band or a collinearity search. It returns the whole eave line (a bearing ref
    names one segment of a line authored as several); every segment of one line carries the
    same assembly, so the first is the clip rule for all of them — and where they do NOT,
    ``envelope._resolve_roof`` already raises ``integrity.roof_bearing``.
    """
    from typehaus.resolve.roof_edge_geometry import skin_layers, skin_stand_ins

    if wall is None or skin_layers(wall):
        return wall
    stand_ins = skin_stand_ins(model, wall, lambda _wall: True)
    return stand_ins[0] if stand_ins else wall


def _edge_wall(model, roof, edge: str, bearing_walls: list):
    """The wall whose stack governs one footprint edge.

    Eave edges use the nearest bearing wall. Rake edges use the exterior wall whose
    outermost-layer polygon touches that footprint edge (the same cladding polygon
    ``_resolve_roof`` laps the footprint out to); fallback: the first bearing wall.
    A skinless result is replaced by its stand-in (:func:`_skinned`).
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
        wall = _skinned(model, _edge_wall(model, roof, edge, bearing_walls))
        clips[edge] = (_wall_clip_setbacks(wall) if wall is not None
                       else {"deck": 0.0, "foam": 0.0, "batten": 0.0, "metal": 0.0})
    groups: list[str | None] = []
    group: str | None = None
    for layer in layers:
        group = _layer_group(layer.function, group)
        groups.append(group)
    # **A deck with nothing above it but membranes and the covering IS the batten.** The
    # "deck" clip stops a layer at the WALL SHEATHING face, which is right while foam and a
    # nailbase run out over the wall's stand-off band and carry the metal — and wrong the
    # moment they do not. On a zero-overhang continuous-skin edge with no above-deck
    # insulation (CATLIN_ROOF since 2026-08-31) that rule left the structural deck stopping
    # at the wall sheathing plane, 6.6" short of the roofing clipped to it: the panel
    # cantilevered over the girts with nothing under it, and the take-off meanwhile bought
    # deck for the whole sloped footprint. The deck really does oversail the last rafter and
    # span the girts, and this is the line that says so.
    if not any(g in ("foam", "batten") for g in groups):
        groups = ["batten" if g == "deck" else g for g in groups]
    entries: list[dict] = []
    for layer, group in zip(layers, groups, strict=True):
        entries.append({
            "layer": layer.name,
            **{edge: (clips[edge][group] if group is not None else 0.0)
               for edge in ("west", "east", "south", "north")},
        })
    return tuple(entries)
