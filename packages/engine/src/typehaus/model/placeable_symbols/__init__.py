"""Generated plan symbols and 3D massing for catalog placeables — one geometry source.

TypeHaus ships every default placeable as a bare W×D×H rectangle: one ``<rect>`` on the 2D
canvas, one closed polyline on the sheets, one flat-coloured box in the viewer and in the glTF
export. The *imported asset* path (``plan_representation.svg`` / ``model_representation.glb``)
is the only escape hatch, and it needs a real product file per type.

This package is the default, no-asset-required alternative: a type names a ``plan_symbol`` and
gets a drawn plan glyph plus a boxy multi-colour massing. Geometry is generated **once, here,
in Python**, and streamed to every renderer as plain coordinate data through
``model/canvas.canvas_object_types()``. That deliberately does *not* follow the
``doorSymbols.ts`` ↔ ``door_symbols.py`` hand-mirrored precedent — ~30 glyphs are too many to
keep in sync by convention, and the UI's own rule is that it never re-measures the design.

Pure functions over floats, with no model imports, so ``model/canvas.py``, ``emit/draw/`` and
``emit/gltf/`` can all depend on it without a layering inversion.

An unknown or ``None`` symbol yields ``()`` from both entry points, so a catalog entry may name
a symbol before its builder exists.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Sequence, Tuple

from typehaus.model.placeable_symbols._frame import (PART_COLORS, Part, Point, Stroke,
                                                     lamp_role, part_hex)
from typehaus.model.placeable_symbols.appliances import APPLIANCE_SYMBOLS
from typehaus.model.placeable_symbols.furniture import FURNITURE_SYMBOLS
from typehaus.model.placeable_symbols.lighting import LIGHTING_SYMBOLS
from typehaus.model.placeable_symbols.plumbing import PLUMBING_SYMBOLS

__all__ = ["SYMBOL_NAMES", "PART_COLORS", "Part", "Stroke", "lamp_role", "model_parts",
           "part_hex", "place_local", "plan_symbol_strokes", "symbol_geometry"]

# A builder takes the type's overall size and returns both halves of its glyph at once, so a
# sofa's drawn arms and its 3D arm boxes cannot drift apart.
Builder = Callable[[float, float, float], Tuple[Tuple[Stroke, ...], Tuple[Part, ...]]]

_REGISTRY: dict[str, Builder] = {**FURNITURE_SYMBOLS, **APPLIANCE_SYMBOLS, **PLUMBING_SYMBOLS,
                                 **LIGHTING_SYMBOLS}

# The frozen vocabulary. A catalog entry may only name a symbol listed here; the contract test
# holds the registry to it in both directions.
SYMBOL_NAMES = frozenset({
    # furniture
    "sofa", "loveseat", "sectional", "armchair", "dining-chair", "office-chair",
    "dining-table", "round-table", "coffee-table", "end-table", "desk",
    "dresser", "chest", "nightstand", "media-console", "bookcase",
    "bed", "tv",
    # sauna joinery — benches are fitted to the room, not bought as a set
    "sauna-bench", "sauna-bench-tiered",
    # kitchen/bath casework — the fitted millwork a room is built around
    "base-cabinet", "sink-base", "wall-cabinet", "tall-cabinet", "tall-cabinet-double",
    "tall-cabinet-triple",
    # appliances + mechanical/electrical equipment
    "refrigerator", "range", "dishwasher", "washer", "dryer", "microwave", "hood",
    "furnace", "erv", "water-heater", "sauna-heater", "panel", "register",
    # plumbing fixtures. "hydrant" is the odd one out: it is a standpipe, not a vessel, so
    # its glyph is the riser's own diameter with a handle bar and an outlet nipple rather
    # than a basin.
    "toilet", "lavatory", "vanity", "tub", "tub-shower", "shower", "kitchen-sink",
    "hydrant",
    # luminaires — one name per LuminaireForm that has a point instance. STRIP has none:
    # a cove strip is a LightRun polyline, drawn by the lighting plan, not a placeable.
    # "linear-light" covers LINEAR_TUBE, WALL_LAMP and MIRROR_LIGHT, which differ by
    # mounting and schedule row rather than by glyph.
    "recessed-can", "panel-light", "sconce", "sconce-updown", "sconce-spot",
    "pendant", "chandelier", "ceiling-fan-light", "linear-light",
})

# Names in the vocabulary with no builder yet. Kept explicit so "not implemented" is a
# deliberate, reviewable state rather than a silently empty glyph.
PENDING_SYMBOLS: frozenset[str] = frozenset()

# Strokes are height-independent by contract; this is what the plan entry point passes so a
# single builder can still compute its parts.
_NOMINAL_HEIGHT = 1.0


def symbol_geometry(symbol: Optional[str], width_m: float, depth_m: float,
                    height_m: float) -> Tuple[Tuple[Stroke, ...], Tuple[Part, ...]]:
    """Both halves of a symbol at a concrete size. ``()``/``()`` when it has no builder."""
    builder = _REGISTRY.get(symbol or "")
    if builder is None or width_m <= 0 or depth_m <= 0 or height_m <= 0:
        return (), ()
    return builder(float(width_m), float(depth_m), float(height_m))


def plan_symbol_strokes(symbol: Optional[str], width_m: float,
                        depth_m: float) -> Tuple[Stroke, ...]:
    """The drawn plan glyph for ``symbol`` at a W×D footprint, in the local frame."""
    return symbol_geometry(symbol, width_m, depth_m, _NOMINAL_HEIGHT)[0]


def model_parts(symbol: Optional[str], width_m: float, depth_m: float,
                height_m: float) -> Tuple[Part, ...]:
    """The 3D massing boxes for ``symbol`` at a W×D×H size, in the local frame."""
    return symbol_geometry(symbol, width_m, depth_m, height_m)[1]


def place_local(points: Sequence[Point], position: Tuple[float, float],
                rotation_degrees: float) -> list[Point]:
    """Lift local-frame points into plan space.

    Mirrors ``resolve/placeables._transformed_polygon`` exactly — the resolver bakes rotation
    into ``footprint`` but not into symbol geometry, so every consumer applies the same
    rotate-then-translate here instead of re-deriving it.
    """
    radians = math.radians(rotation_degrees)
    cos, sin = math.cos(radians), math.sin(radians)
    return [(position[0] + x * cos - y * sin, position[1] + x * sin + y * cos)
            for x, y in points]
