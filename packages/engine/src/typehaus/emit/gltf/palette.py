"""The export's colour vocabulary: layer function / member category → RGBA, plus the material
finish colours that follow a named material rather than its category.

Mirrored by ui/src/three/members.ts ``CATEGORY_COLOR`` and ui/src/three/materials.ts — a tone
that changes here has to change there too, or the .glb and the live viewer disagree.
"""

from __future__ import annotations

from typehaus.emit.draw.palette import family_of, material_color, material_family_color
from typehaus.resolve.model import ResolvedModel


# function/category → RGBA color (linear, 0..1). Keys are lowercased layer functions and
# member categories; anything unmatched falls back to a neutral gray.
_PALETTE: dict[str, tuple[float, float, float, float]] = {
    "structure": (0.62, 0.45, 0.28, 1.0),
    "insulation": (0.93, 0.74, 0.36, 1.0),
    "sheathing": (0.72, 0.72, 0.70, 1.0),
    "cladding": (0.55, 0.58, 0.60, 1.0),
    "lining": (0.90, 0.89, 0.86, 1.0),
    "finish": (0.90, 0.89, 0.86, 1.0),
    "membrane": (0.30, 0.45, 0.55, 1.0),
    "air_gap": (0.80, 0.85, 0.90, 0.35),
    "furring": (0.68, 0.52, 0.34, 1.0),
    # framing member categories
    "stud": (0.70, 0.52, 0.33, 1.0),
    "plate": (0.66, 0.48, 0.30, 1.0),
    "header": (0.60, 0.42, 0.26, 1.0),
    "raked_plate": (0.66, 0.48, 0.30, 1.0),
    "corner": (0.64, 0.46, 0.29, 1.0),
    "stringer": (0.60, 0.42, 0.26, 1.0),
    "tread": (0.70, 0.52, 0.33, 1.0),
    "winder": (0.70, 0.52, 0.33, 1.0),
    # Opening framing. These existed in ui/src/three/members.ts CATEGORY_COLOR only, so a
    # header's king/jack/cripple studs read as lumber in the browser and as the grey fallback
    # in the GLB. Same tones as their whole-stud/plate/header siblings, as the viewer has.
    "king": (0.70, 0.52, 0.33, 1.0),
    "jack": (0.70, 0.52, 0.33, 1.0),
    "cripple": (0.70, 0.52, 0.33, 1.0),
    "sill": (0.66, 0.48, 0.30, 1.0),
    "bearing_stiffener": (0.60, 0.42, 0.26, 1.0),
    # stair landing platforms + the U-stair well partition read as framing lumber; the
    # concrete-wall hanger/ledger band is galvanized grey like "connector". Mirrored in
    # ui/src/three/members.ts CATEGORY_COLOR (GLB/three.js parity convention).
    "landing": (0.72, 0.55, 0.36, 1.0),
    # The joists, rims and posts under a landing deck: framing lumber, a shade under the
    # deck they carry. Mirrors CATEGORY_COLOR in ui/src/three/members.ts.
    "landing_framing": (0.639, 0.463, 0.247, 1.0),  # 0xa3763f — as blocking
    # The winder newel carries every winder's narrow end — a post-sized member, so it takes
    # the header/stringer tone rather than the lighter tread lumber.
    "newel": (0.60, 0.42, 0.26, 1.0),
    "partition": (0.70, 0.52, 0.33, 1.0),
    "trimmer": (0.66, 0.48, 0.30, 1.0),
    "hanger": (0.35, 0.36, 0.38, 1.0),
    "joist": (0.72, 0.55, 0.36, 1.0),
    # Plies sistered onto a joist line under a point load (resolve/floors.py). Same stock as
    # the joist it doubles, a shade darker so a reinforced line reads as one in the viewer.
    "sister_joist": (0.66, 0.48, 0.30, 1.0),
    "rim": (0.66, 0.48, 0.30, 1.0),
    # Furring strapping (resolve/framing/furring.py). Lighter than a stud: 1x4 battens
    # over the sheathing are the last lumber outboard of the wall, and reading them as
    # a paler grid over the darker frame is how a rainscreen is told apart from it.
    "strapping": (0.757, 0.596, 0.416, 1.0),  # 0xc1986a
    "ridge_beam": (0.55, 0.38, 0.22, 1.0),
    "brace": (0.639, 0.463, 0.247, 1.0),         # 0xa3763f — as blocking
    # Stick-framed roof lumber + the blocking that fills between it. These had no entry at
    # all, so ~260 members rendered as the neutral gray fallback in *both* renderers (the
    # "garage truss should visualize as wood" report). Values chosen to round-trip exactly
    # to the hex literals in ui/src/three/members.ts CATEGORY_COLOR.
    "rafter": (0.678, 0.498, 0.310, 1.0),        # 0xad7f4f
    "blocking": (0.639, 0.463, 0.247, 1.0),      # 0xa3763f
    "outlooker": (0.722, 0.549, 0.361, 1.0),     # 0xb88c5c
    "barge_rafter": (0.549, 0.384, 0.220, 1.0),  # 0x8c6238
    # roof truss members + the birdsmouth seat cut
    "top_chord": (0.70, 0.52, 0.33, 1.0),
    "bottom_chord": (0.66, 0.48, 0.30, 1.0),
    "truss_web": (0.74, 0.57, 0.38, 1.0),
    "truss_heel": (0.60, 0.42, 0.26, 1.0),
    "seat_cut": (0.58, 0.40, 0.24, 1.0),
    "floor": (0.82, 0.80, 0.76, 1.0),
    "roof": (0.35, 0.37, 0.40, 1.0),
    "slab": (0.55, 0.56, 0.57, 1.0),
    "footing": (0.48, 0.49, 0.50, 1.0),
    "pad": (0.50, 0.51, 0.52, 1.0),
    "column": (0.60, 0.60, 0.62, 1.0),  # concrete/wood posts (sonotube, 6x6 pillars)
    "beam": (0.62, 0.46, 0.28, 1.0),  # PT / built-up wood beams
    "furniture": (0.46, 0.31, 0.20, 1.0),
    # The site sheet under the building. 0x806040 is the viewer's soil brown
    # (ui/src/three/builders/site.ts buildEarth); the viewer draws it at 0.28 opacity with
    # depth writes off, which is an overlay trick with no importer equivalent, so the export
    # ships the same tone opaque.
    "earth": (0.502, 0.376, 0.251, 1.0),
    # opening fillings — frame/leaf/panel read as wood; glazing is translucent blue-grey
    # (0x8fb7c9 @ 0.48), matching ui/src/components/Panel3D.tsx buildOpening. The frame tone is
    # the viewer's light-theme member wood (0xb3854f, ui/src/nordic/palette.ts); the .glb has no
    # theme to follow, so it ships the default one buildOpening reads for the same boxes.
    "opening_frame": (0.702, 0.522, 0.310, 1.0),
    "glass": (0.561, 0.718, 0.788, 0.48),
    # Exterior window casing (resolve/geometry_openings.py). This entry plus the mirrored
    # CATEGORY_COLOR.window_trim in ui/src/three/members.ts are the whole recolor. Rounds
    # exactly to 0x1c1f24 — the house's one exterior dark, shared with the roof-edge trim
    # coil and the guards (metal-dark-exterior in _FINISH_BASE below). It reads as the
    # charcoal 0x3a3d40 was meant to be: the viewer's ambient lifts a dark albedo well above
    # itself, so the authored value has to sit under the tone you want on screen.
    "window_trim": (0.110, 0.122, 0.141, 1.0),
    # accessories (→ resolve/accessories.py)
    "railing": (0.80, 0.81, 0.83, 1.0),   # aluminum guard
    "dowel": (0.20, 0.55, 0.35, 1.0),     # GFRP rebar (green)
    "thermal_break": (0.95, 0.55, 0.15, 1.0),  # XPS foam block (orange)
    "connector": (0.35, 0.36, 0.38, 1.0),  # galvanized hardware
    "sump": (0.30, 0.32, 0.34, 1.0),       # pit
    "vent": (0.88, 0.88, 0.86, 1.0),       # painted vent pipe
    # routed plumbing runs (→ resolve/mep.py _emit_run_solids), riser-diagram colors
    "pipe_drain": (0.20, 0.20, 0.22, 1.0),       # ABS/PVC waste, near-black
    "pipe_vent": (0.88, 0.88, 0.86, 1.0),        # same as the vent risers
    "pipe_water_hot": (0.80, 0.25, 0.22, 1.0),   # red PEX
    "pipe_water_cold": (0.20, 0.40, 0.75, 1.0),  # blue PEX
    "pipe_gas": (0.85, 0.75, 0.20, 1.0),         # yellow CSST
    "pipe_radon": (0.55, 0.58, 0.60, 1.0),       # bare gray
    # In-line supply devices, one category per PipeAccessoryKind (→ emit/trades.py). Brass
    # for anything with a body you turn or that holds pressure, so hardware reads as hardware
    # against the PEX it interrupts; the two that are not valves get their own tone.
    "main_shutoff": (0.72, 0.58, 0.28, 1.0),          # brass
    "shutoff": (0.72, 0.58, 0.28, 1.0),
    "backflow_preventer": (0.72, 0.58, 0.28, 1.0),
    "vacuum_breaker": (0.72, 0.58, 0.28, 1.0),
    "ro_stub": (0.72, 0.58, 0.28, 1.0),
    "water_hammer_arrestor": (0.62, 0.64, 0.66, 1.0),  # sealed steel chamber, not a valve
    "penetration_seal": (0.95, 0.72, 0.35, 1.0),       # the foam/gasket kit, not plumbing metal
    # Raceways (→ resolve/mep.py _emit_run_solids, one category per side of the NEC
    # 800.133/725 power-vs-comms line). Deliberately *outside* the riser-diagram hues above:
    # a raceway drawn in red or blue would read as a supply line in the one view where
    # telling them apart matters — the basement ceiling, where CD-B-KITCHEN runs the length
    # of the house alongside the hot and cold trunks. Violet and teal are what the plumbing
    # convention leaves free, and they separate cleanly from each other, which is the
    # distinction that actually earns a colour here.
    "conduit_power": (0.545, 0.302, 0.702, 1.0),  # 0x8b4db3
    "conduit_data": (0.180, 0.659, 0.608, 1.0),   # 0x2ea89b
    # The cast-in block-out (→ resolve/mep.py _emit_sleeve_solid). Not concrete — it is the
    # hole, and reading as the pour it sits in would defeat the point of drawing it — and not
    # pipe metal either: the cream is the fibre void former the concrete crew actually sets.
    "pipe_sleeve": (0.851, 0.788, 0.639, 1.0),    # 0xd9c9a3
    "solar": (0.10, 0.14, 0.28, 1.0),      # PV module glass, deep blue
    "fascia": (0.92, 0.92, 0.90, 1.0),     # PVC fascia
    "soffit": (0.88, 0.88, 0.85, 1.0),     # vented soffit panel under the overhang
    "gutter": (0.85, 0.86, 0.87, 1.0),     # metal gutter
    # stormwater below the gutter (→ emit/trades.py, trade "drainage")
    "downspout": (0.85, 0.86, 0.87, 1.0),  # the gutter's own aluminium, drawn down the wall
    # Perforated tile is a warmer near-black than the ABS waste `pipe_drain` above, so a
    # buried drainage view can tell the storm ring from the sanitary run it parallels.
    "drain_tile": (0.16, 0.15, 0.13, 1.0),   # corrugated HDPE tile
    "french_drain": (0.62, 0.60, 0.56, 1.0),  # washed-rock trench
    "drywell": (0.52, 0.50, 0.47, 1.0),      # soakaway aggregate, darker than the trench
    "ridge_cap": (0.85, 0.86, 0.87, 1.0),  # vented standing-seam ridge cap
    "corner_trim": (0.85, 0.86, 0.87, 1.0),  # eave corner trim (continuous skin)
    "flashing": (0.75, 0.77, 0.80, 1.0),   # metal flashing
    # LightRun's channel + tape (→ emit/gltf/emitter.py::_add_light_run). Mirrors
    # ui/src/three/builders/structure.ts COVE_CHANNEL_COLOR / LED_TAPE_COLOR.
    "cove_channel": (0.80, 0.80, 0.80, 1.0),  # mill-finish aluminium extrusion
    "led_tape": (1.00, 0.92, 0.72, 1.0),      # warm-white tape, bright rather than lit
}
_FALLBACK = (0.70, 0.70, 0.70, 1.0)


def _color(key: str) -> tuple[float, float, float, float]:
    return _PALETTE.get(key.lower(), _FALLBACK)


def _hex_rgba(hex_str: str) -> tuple[float, float, float, float]:
    # Fed straight into baseColorFactor like the existing _solid_color path; no sRGB→linear
    # conversion, matching the emitter's other palette values which are authored directly.
    #
    # ``#RRGGBBAA`` is how a material declares that it is see-through. The whole alpha path
    # was already built — ``emit/gltf/scene.py`` switches a material below 1.0 to
    # ``alphaMode: BLEND`` and makes it double-sided, and ``air_gap``/``glass`` use it — but
    # it was unreachable from an authored ``Material``, because this pinned alpha to 1.0. A
    # sheet of polycarbonate that renders opaque is not a glazed breezeway, it is a shed.
    h = hex_str.lstrip("#")
    if len(h) in (6, 8):
        alpha = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, alpha)
    return _FALLBACK


# Finish classification mirrors ui/src/three/materials.ts so the export approximates the
# viewer's procedural finishes with one flat base colour (no baked textures): a standing-seam
# wall reads near-white, CMU reads grey block, white brick reads whitewashed, and any other
# recognised material falls back to its material-family colour.
#
# ``_FINISH_BASE`` is keyed by the engine's finish vocabulary (model/materials.py
# ``Material.finish``, mirrored by MASONRY_STYLES in ui/src/three/materials.ts). A resolved
# layer carries only its material *ref*, not the authored Material, so the ref is matched
# against that vocabulary by name first — an exact, spelling-independent hit for any material
# whose tag is its finish — and only then falls back to the substring guesswork below.
_SEAM_BASE = "#e8e8e2"          # Panel3D.tsx createStandingSeamMaterial base (0xE8E8E2)
_CMU_BASE = "#9c988f"           # materials.ts CMU_STYLE.base
_WHITE_BRICK_BASE = "#e9e6df"   # materials.ts WHITE_BRICK_STYLE.base
_GLAZED_GREEN_BRICK_BASE = "#1b4332"  # materials.ts GLAZED_GREEN_BRICK_STYLE.base
_DECK_BOARD_BASE = "#b9bcc0"    # materials.ts ALUMINUM_DECK_BASE_COLOR (0xb9bcc0)

_EXTERIOR_DARK = "#1c1f24"      # the house's one exterior dark; see window_trim above

_FINISH_BASE: dict[str, str] = {
    "standing-seam": _SEAM_BASE,
    "cmu": _CMU_BASE,
    "white-brick": _WHITE_BRICK_BASE,
    "glazed-green-brick": _GLAZED_GREEN_BRICK_BASE,
    # Formed edge trim ordered in a second coil colour (Roof.edge_trim_material). Without an
    # entry it falls to the "metal" family's blue-grey, and the accent that makes a
    # zero-overhang rake legible would differ between the .glb and the viewer.
    "metal-dark-exterior": _EXTERIOR_DARK,
    # The balcony 6x6 pillars' painted-lumber material (POST_WHITE_PAINT's structure
    # layer), now also carried by the knee-brace diagonals as a FramedMember material.
    # No family needle matches the ref, so without an entry the brace member path falls
    # to the bare "brace" category lumber while the pillars it braces render white.
    # Value = the material's authored colour in houses/catlin/plan/assemblies.py.
    "post-paint-white": "#f4f2ee",
}


def _is_standing_seam(material_ref: str | None) -> bool:
    if not material_ref:
        return False
    s = material_ref.lower()
    return "seam" in s or (family_of(material_ref) == "metal" and "standing" in s)


def _is_cmu(material_ref: str | None) -> bool:
    if family_of(material_ref) != "masonry":
        return False
    s = (material_ref or "").lower()
    return "cmu" in s or "block" in s or "concrete mason" in s


def _is_white_brick(material_ref: str | None) -> bool:
    s = (material_ref or "").lower()
    return "white" in s or "limewash" in s or "whitewash" in s


def _is_aluminum_deck_board(material_ref: str | None) -> bool:
    """Aluminum plank decking — the viewer's grooved 5.5" board finish (materials.ts
    isAluminumDeckBoard). The metal family colour would read as dark flashing, so the
    export pins the plank's own mill-finish base instead."""
    if not material_ref:
        return False
    s = material_ref.lower()
    return "deck" in s and ("alum" in s or family_of(material_ref) == "metal")


def authored_colors(model: ResolvedModel) -> dict[str, object]:
    """The catalog materials that state their own colour, keyed by tag.

    The ``authored`` argument of :func:`_material_finish_color` — built once per export and
    threaded through the wall/roof layer colouring, because a resolved layer carries only its
    material *ref* and cannot reach the catalog on its own.
    """
    return {m.tag: m for m in model.plan.library.materials if m.color}


def _material_finish_color(material_ref: str | None,
                           function: str,
                           authored: dict | None = None) -> tuple[float, float, float, float]:
    """Colour a material by its named finish, else its authored catalog colour, else its
    family + finish classification, mirroring the viewer's materialColor
    (ui/src/nordic/palette.ts: FINISH_BASE → authored ``color`` → family inference — keep
    the precedence in step). ``function`` is the lowercased layer function string
    ("cladding", …), used for the standing-seam test and as the fallback palette key when no
    family is recognised. ``authored`` is the :func:`authored_colors` dict; without it this
    guessed a family for every layer, so an authored wall-paint colour reached the viewer
    but never the .glb."""
    named = _FINISH_BASE.get((material_ref or "").lower())
    if named is not None:
        return _hex_rgba(named)
    if authored:
        material = authored.get(material_ref or "")
        if material is not None:
            return _hex_rgba(material_color(material.hatch, material.color))
    if function == "cladding" and _is_standing_seam(material_ref):
        return _hex_rgba(_SEAM_BASE)
    if _is_aluminum_deck_board(material_ref):
        return _hex_rgba(_DECK_BOARD_BASE)
    if family_of(material_ref) == "masonry":
        if _is_cmu(material_ref):
            return _hex_rgba(_CMU_BASE)
        if _is_white_brick(material_ref):
            return _hex_rgba(_WHITE_BRICK_BASE)
        return _hex_rgba(material_family_color(material_ref))  # default red brick → masonry
    if family_of(material_ref) is not None:
        return _hex_rgba(material_family_color(material_ref))
    return _color(function)


def _layer_color(layer, authored: dict | None = None) -> tuple[float, float, float, float]:
    """Colour a resolved wall layer: named finish, then the material's authored catalog colour
    (``authored`` = :func:`authored_colors`), then material family; falls back to the function
    palette for layers with no recognisable material ref."""
    return _material_finish_color(layer.material_ref, layer.function, authored)


def _room_floor_color(model: ResolvedModel,
                      floor_finish: str | None) -> tuple[float, float, float, float]:
    """The colour a room's floor finish reads in, or the neutral floor tone when unfinished.

    Every room used to export as one flat ``_color("floor")`` grey, so carpet, oak and tile
    were indistinguishable in the .glb even though the finish was resolved and exported. The
    lookup is exact — the finish string *is* the material tag — and it resolves through the
    material's authored ``color``/``hatch``, which is the same path
    ``ui/src/nordic/palette.ts::materialColor`` takes in the live viewer, so the two agree
    (→ ``glb-emitter-parity``). An unrecognised finish string falls back rather than raising:
    a typo shows up as bare deck here and as an UNKNOWN row in the takeoff.
    """
    if not floor_finish:
        return _color("floor")
    material = next((m for m in model.plan.library.materials if m.tag == floor_finish), None)
    if material is None:
        return _color("floor")
    return _hex_rgba(material_color(material.hatch, material.color))


def _solid_color(model: ResolvedModel, solid) -> tuple[float, float, float, float]:
    """A solid with an authored assembly (e.g. a composite/aluminum deck) reads with its
    material colour; otherwise it falls back to the per-category palette.

    A trim run names its material directly rather than through an assembly, and that ref wins
    over the category — it is how a gutter ordered in the roof's trim coil says so. Only a
    *named* finish or a catalog material with an authored colour counts: the generic refs the
    family already carries ("aluminum") stay on their category tone, so this changes nothing
    for a run that never stated a colour.
    """
    named = _FINISH_BASE.get((solid.material or "").lower())
    if named is not None:
        return _hex_rgba(named)
    if solid.material:
        authored = next((m for m in model.plan.library.materials
                         if m.tag == solid.material and m.color), None)
        if authored is not None:
            return _hex_rgba(material_color(authored.hatch, authored.color))
    if solid.assembly:
        assembly = model.plan.library.resolve_assembly(solid.assembly)
        if assembly is not None and assembly.layers:
            idx = assembly.structure_index()
            layer = assembly.layers[idx if idx is not None else 0]
            if _is_aluminum_deck_board(layer.material_ref):
                return _hex_rgba(_DECK_BOARD_BASE)
            material = next((m for m in model.plan.library.materials
                             if m.tag == layer.material_ref), None)
            if material is not None:
                return _hex_rgba(material_color(material.hatch, material.color))
    return _color(solid.category)
