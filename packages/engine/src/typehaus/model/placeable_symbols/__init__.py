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
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typehaus.model.air_handler_installation import AirHandlerInstallation
    from typehaus.model.placeables import ServicePort
    from typehaus.model.shower_assembly import ShowerAssemblySpec

from typehaus.model.placeable_symbols._badger_disposal import (
    badger_disposal,
    badger_disposal_with_dearborn_trap,
)
from typehaus.model.placeable_symbols._broan_hood import broan_recirculating_hood
from typehaus.model.placeable_symbols._ceramic_fan_heater import ceramic_fan_heater
from typehaus.model.placeable_symbols._eg4_storage import eg4_12kpv, eg4_wallmount_indoor
from typehaus.model.placeable_symbols._erv_wall_hood import erv_wall_hood
from typehaus.model.placeable_symbols._fireplace_insert import fireplace_insert
from typehaus.model.placeable_symbols._frame import (
    PART_COLORS,
    Part,
    Point,
    Stroke,
    lamp_role,
    part_hex,
    with_material_refs,
)
from typehaus.model.placeable_symbols._gfci_in_use_cover import (
    gfci_in_use_cover,
    gfci_in_use_cover_15a,
)
from typehaus.model.placeable_symbols._gree_flexx import gree_flexx_horizontal
from typehaus.model.placeable_symbols._gree_flexx_outdoor import gree_flexx_outdoor
from typehaus.model.placeable_symbols._ibtb_bar import ibtb_bar
from typehaus.model.placeable_symbols._imo_rsd_initiator import imo_ess_rsd01
from typehaus.model.placeable_symbols._infrared_heater import infrared_heater
from typehaus.model.placeable_symbols._led_controller import (
    gledopto_gl_c_001p,
    ikea_tradfri_driver,
    nema_4x_box,
)
from typehaus.model.placeable_symbols._led_driver_jbox import diode_odx_j
from typehaus.model.placeable_symbols._led_driver_potted import meanwell_hlg_100h
from typehaus.model.placeable_symbols._meter_main import meter_main_class320
from typehaus.model.placeable_symbols._midnite_mnspd import midnite_mnspd
from typehaus.model.placeable_symbols._nema_3r_boxes import comms_entrance_box, pv_junction_box
from typehaus.model.placeable_symbols._pan_tilt_camera import reolink_omvi_3i_ceiling
from typehaus.model.placeable_symbols._reolink_doorbell import reolink_doorbell_d340p
from typehaus.model.placeable_symbols._sektion_kitchen import KITCHEN_SEKTION_SYMBOLS
from typehaus.model.placeable_symbols._sheet_metal_plenum import plenum_parts, sheet_metal_plenum
from typehaus.model.placeable_symbols._siemens_fs140 import siemens_fs140
from typehaus.model.placeable_symbols._sunnersta import sunnersta_frame
from typehaus.model.placeable_symbols._swanstone_flex import swanstone_flex
from typehaus.model.placeable_symbols._thermostat import thermostat
from typehaus.model.placeable_symbols._unifi_access_point import (
    UNIFI_ACCESS_POINT_SYMBOLS,
    unifi_u6_pro_ceiling,
    unifi_u6_pro_wall,
)
from typehaus.model.placeable_symbols.appliances import APPLIANCE_SYMBOLS
from typehaus.model.placeable_symbols.furniture import FURNITURE_SYMBOLS
from typehaus.model.placeable_symbols.lighting import LIGHTING_SYMBOLS
from typehaus.model.placeable_symbols.plumbing import PLUMBING_SYMBOLS
from typehaus.model.placeable_symbols.receptacles import RECEPTACLE_SYMBOLS
from typehaus.model.placeable_symbols.switches import SWITCH_SYMBOLS

__all__ = ["SYMBOL_NAMES", "PART_COLORS", "Part", "Stroke", "lamp_role", "model_parts",
           "part_hex", "place_local", "plan_symbol_strokes", "symbol_geometry"]

# A builder takes the type's overall size and returns both halves of its glyph at once, so a
# sofa's drawn arms and its 3D arm boxes cannot drift apart.
Builder = Callable[[float, float, float], tuple[tuple[Stroke, ...], tuple[Part, ...]]]

_REGISTRY: dict[str, Builder] = {**FURNITURE_SYMBOLS, **APPLIANCE_SYMBOLS, **PLUMBING_SYMBOLS,
                                 **LIGHTING_SYMBOLS, **KITCHEN_SEKTION_SYMBOLS,
                                 **RECEPTACLE_SYMBOLS, **SWITCH_SYMBOLS,
                                 "receptacle-gfci-in-use-cover": gfci_in_use_cover,
                                 "receptacle-gfci-in-use-cover-15a": gfci_in_use_cover_15a,
                                 "eg4-12kpv": eg4_12kpv,
                                 "eg4-wallmount-indoor-280ah": eg4_wallmount_indoor,
                                 "renewaire-fa8-wall-hood": erv_wall_hood,
                                 "swanstone-flex-3636": swanstone_flex,
                                 "infrared-heater": infrared_heater,
                                 "ceramic-fan-heater": ceramic_fan_heater,
                                 "thermostat": thermostat,
                                 "reolink-omvi-3i-ceiling": reolink_omvi_3i_ceiling,
                                 "unifi-u6-pro-ceiling": unifi_u6_pro_ceiling,
                                 "unifi-u6-pro-wall": unifi_u6_pro_wall,
                                 "insinkerator-badger-5": badger_disposal,
                                 "badger-5-with-dearborn-p9703wbg":
                                     badger_disposal_with_dearborn_trap,
                                 "broan-bwp1304ss-recirculating": broan_recirculating_hood,
                                 "fireplace-insert": fireplace_insert,
                                 "gree-flexx-ultra-24-horizontal": gree_flexx_horizontal,
                                 "gree-flexx-ultra-24-outdoor": gree_flexx_outdoor,
                                 "sunnersta-frame": sunnersta_frame,
                                 "sheet-metal-plenum": sheet_metal_plenum,
                                 "meanwell-hlg-100h": meanwell_hlg_100h,
                                 "diode-odx-j": diode_odx_j,
                                 "gledopto-gl-c-001p": gledopto_gl_c_001p,
                                 "ikea-tradfri-driver": ikea_tradfri_driver,
                                 "nema-4x-box": nema_4x_box,
                                 "imo-ess-rsd01": imo_ess_rsd01,
                                 "siemens-fs140": siemens_fs140,
                                 "midnite-mnspd": midnite_mnspd,
                                 "meter-main-class320": meter_main_class320,
                                 "nvent-erico-ibtb": ibtb_bar,
                                 "comms-entrance-box": comms_entrance_box,
                                 "pv-junction-box": pv_junction_box,
                                 "reolink-d340p-doorbell": reolink_doorbell_d340p}

# The frozen vocabulary. A catalog entry may only name a symbol listed here; the contract test
# holds the registry to it in both directions.
SYMBOL_NAMES = (UNIFI_ACCESS_POINT_SYMBOLS
                | frozenset(KITCHEN_SEKTION_SYMBOLS) | frozenset(RECEPTACLE_SYMBOLS)
                | frozenset(SWITCH_SYMBOLS)) | frozenset({
    "receptacle-gfci-in-use-cover", "receptacle-gfci-in-use-cover-15a",
    "plant-reservoir", "plant-irrigation-rack", "plant-leak-sensors",
    "broan-bwp1304ss-recirculating",
    "plain-round-mirror-nickel", "plain-arch-mirror-nickel", "plain-arch-mirror-chrome",
    "plain-arch-mirror-black",
    "plain-soft-rectangle-mirror-nickel", "plain-capsule-mirror-nickel",
    "halo-mirror-light", "socketed-vanity-2-nickel", "socketed-vanity-2-chrome",
    "socketed-vanity-3-nickel", "socketed-vanity-3-chrome",
    "pivoting-paper-holder", "towel-bar", "towel-hook",
    "pivoting-paper-holder-chrome", "towel-bar-chrome", "towel-hook-chrome",
    # furniture
    "sofa", "loveseat", "sectional", "armchair", "strandmon", "dining-chair", "cantilever-chair",
    "office-chair",
    "dining-table", "rounded-dining-table", "round-table", "coffee-table", "end-table",
    "chess-table", "hammock-chair", "hanging-daybed", "curtain-rod",
    "tapestry-rod-clips", "cellular-blind",
    "desk", "wall-desk", "footrest",
    "drawer-desk", "sit-stand-desk",
    "sektion-drawer-base", "dresser", "chest", "nightstand", "media-console", "bookcase",
    "rolling-cart",
    "hemnes-bookcase", "corner-bookcase", "slat-partition",
    "sektion-tall-drawers", "sektion-tall-open-lower", "sektion-cover-panel",
    "sektion-seat-base", "sektion-open-high", "sektion-open-base",
    "sektion-axstad-base", "sektion-axstad-drawers", "seat-cushion",
    "wardrobe-show", "wardrobe-show-hang", "wardrobe-dress", "wardrobe-double-hang", "closet-board",
    "closet-corner-wire", "closet-wire",
    "wardrobe-shelves", "wardrobe-corner", "wardrobe-sliding-pair",
    "bed", "tv", "tv-wall", "wall-tapestry", "potted-plant", "wall-rack", "peg-rail",
    "arch-shelf-mirror",
    "small-potted-plant", "wall-plant-stand", "hanging-vine-planter", "fiddle-leaf-fig",
    # sauna joinery — benches are fitted to the room, not bought as a set
    "sauna-bench", "sauna-bench-tiered", "sauna-open-bench", "sauna-recliner",
    "sauna-recliner-mattress",
    # kitchen/bath casework — the fitted millwork a room is built around
    "base-cabinet", "sink-base", "corner-base", "wall-cabinet", "corner-wall-cabinet",
    "sektion-plinth-wall-base", "tall-cabinet",
    "tall-cabinet-double", "tall-cabinet-triple", "besta", "tannforsen-wall", "countertop-bracket",
    # appliances + mechanical/electrical equipment
    "refrigerator", "range", "dishwasher", "washer", "dryer", "washer-dryer-stacked",
    "liftmaster-87504-267-7ft",
    "microwave", "countertop-microwave", "hood", "tea-kettle", "espresso-machine",
    "insinkerator-badger-5",
    "badger-5-with-dearborn-p9703wbg",
    "furnace", "erv", "sheet-metal-plenum", "renewaire-fa8-wall-hood",
    "heat-pump-outdoor", "heat-pump-indoor",
    "water-heater", "sauna-heater", "harvia-cilindro-pc110e", "panel", "register",
    "rheem-proterra-plugin-80",
    "eg4-12kpv", "eg4-wallmount-indoor-280ah",
    "gree-flexx-ultra-24-horizontal",
    "gree-flexx-ultra-24-outdoor",
    "infrared-heater", "fireplace-insert", "ceramic-fan-heater",
    "disconnect", "meter", "junction-box", "spd", "thermostat",
    "reolink-omvi-3i-ceiling",
    # LED drivers and controllers, back on the mounting surface
    "meanwell-hlg-100h", "diode-odx-j", "gledopto-gl-c-001p", "ikea-tradfri-driver",
    "nema-4x-box",
    # PV rapid-shutdown initiator, NEMA 4X rotary
    "imo-ess-rsd01",
    # Surge protective devices: the service SPD and the PV DC SPDs (the plug-ons are not drawn)
    "siemens-fs140", "midnite-mnspd",
    # Exterior service enclosures: meter-main, IBTB bar, comms entrance and PV junction boxes
    "meter-main-class320", "nvent-erico-ibtb", "comms-entrance-box", "pv-junction-box",
    # Reolink PoE video doorbell on its wall plate
    "reolink-d340p-doorbell",
    # Plumbing fixtures: "hydrant" is the Model 19 wall faucet; the Y34SS has its own
    # yard-hydrant geometry. Neither has a drain. "floor-drain" has no supply side.
    # "toilet-wall-hung" is a THIRD odd one out: no tank, so the china takes the whole
    # footprint. The product-specific "toto-ap-duofit" also models its concealed assembly;
    # surrounding wood bay framing remains in ``resolve/framing/carriers.py``.
    "toilet", "toilet-wall-hung", "toto-ap-duofit", "lavatory", "lavatory-wall-hung", "vanity",
    "solid-surface-vanity", "sektion-vanity", "drawer-vanity",
    "door-drawer-vanity", "drawer-vanity-indy", "sektion-vanity-indy",
    "havback-vanity", "havback-vanity-indy",
    "sunnersta-sink", "sunnersta-frame", "solid-surface-access-leaf", "tub",
    "kohler-underscore-6036", "kohler-underscore-6032",
    # "roman-tub-filler" is a bath's deck trim, placed on the deck beside the rim.
    "roman-tub-filler",
    "tub-shower", "shower", "swanstone-flex-3636",
    # "shower-neo-angle" is the square pan with its room-facing corner off at 45 deg. It is
    # its own name rather than a flag on "shower" because the cut is a plan outline a person
    # walks past, not a finish: the glyph, the massing and the catalog ``footprint_shape``
    # all come off ``plumbing.neo_angle_points`` so they cannot disagree.
    "shower-neo-angle",
    "kitchen-sink",
    "kitchen-sink-undermount-single",
    "hydrant", "woodford-y34ss", "floor-drain", "laundry-sink",
    # luminaires — one name per LuminaireForm that has a point instance. STRIP has none:
    # a cove strip is a LightRun polyline, drawn by the lighting plan, not a placeable.
    # "linear-light" covers ordinary compact linear fixtures. The plant tube has the
    # same plan glyph but its own 3D cable-suspension massing.
    "track-light", "flood-light", "recessed-can", "panel-light",
    "leviton-9726-c-a19", "leviton-9880-a19",
    "sconce", "sconce-updown", "sconce-spot", "sconce-gothic",
    "sconce-bantam", "sconce-bantam-down", "sconce-soren", "sconce-tube", "sconce-slim-updown",
    "sconce-swing-arm", "sconce-wac-sprig", "sconce-candle",
    "ceiling-fan-light-3", "suspended-flat-bar",
    "mirror-light",
    "pendant", "chandelier", "cluster-pendant", "ceiling-fan-light", "linear-light",
    "suspended-linear-light", "wave-chandelier", "round-mirror-light", "mirror-light-bar",
})

# Names in the vocabulary with no builder yet. Kept explicit so "not implemented" is a
# deliberate, reviewable state rather than a silently empty glyph.
PENDING_SYMBOLS: frozenset[str] = frozenset()

# Strokes are height-independent by contract; this is what the plan entry point passes so a
# single builder can still compute its parts.
_NOMINAL_HEIGHT = 1.0


def symbol_geometry(symbol: str | None, width_m: float, depth_m: float,
                    height_m: float) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """Both halves of a symbol at a concrete size. ``()``/``()`` when it has no builder."""
    builder = _REGISTRY.get(symbol or "")
    if builder is None or width_m <= 0 or depth_m <= 0 or height_m <= 0:
        return (), ()
    return builder(float(width_m), float(depth_m), float(height_m))


def plan_symbol_strokes(symbol: str | None, width_m: float,
                        depth_m: float, *,
                        air_handler_installation: AirHandlerInstallation | None = None,
                        ) -> tuple[Stroke, ...]:
    """The drawn plan glyph for ``symbol`` at a W×D footprint, in the local frame."""
    strokes = symbol_geometry(symbol, width_m, depth_m, _NOMINAL_HEIGHT)[0]
    if air_handler_installation is not None and symbol == "gree-flexx-ultra-24-horizontal":
        from typehaus.model.placeable_symbols._flexx_installation import installation_strokes

        strokes += installation_strokes(air_handler_installation, width_m, depth_m)
    return strokes


def model_parts(symbol: str | None, width_m: float, depth_m: float,
                height_m: float, *, shower_assembly: ShowerAssemblySpec | None = None,
                material_refs: Mapping[str, str] | None = None,
                ports: Sequence[ServicePort] = (),
                air_handler_installation: AirHandlerInstallation | None = None,
                ) -> tuple[Part, ...]:
    """The generated 3D parts for ``symbol`` at a W×D×H size, in the local frame."""
    parts = (plenum_parts(width_m, depth_m, height_m, ports)
             if symbol == "sheet-metal-plenum"
             else symbol_geometry(symbol, width_m, depth_m, height_m)[1])
    if air_handler_installation is not None and symbol == "gree-flexx-ultra-24-horizontal":
        from typehaus.model.placeable_symbols._flexx_installation import installed_flexx_parts
        from typehaus.model.placeable_symbols._gree_flexx import CABINET_IN

        parts = installed_flexx_parts(gree_flexx_horizontal(*CABINET_IN)[1],
                                      air_handler_installation, width_m, depth_m, height_m)
    if shower_assembly is not None:
        from typehaus.model.placeable_symbols._shower_hardware import shower_hardware_parts

        # Generic shells fit their catalog box. An assembly's actual end-face setout
        # puts the thin surround behind the control plane instead of burying its trim.
        parts = tuple({**part, "center": (
            part["center"][0] + math.copysign(part["size"][0], part["center"][0]),
            *part["center"][1:])} if part.get("role") == "shower:end-wall" else part
                      for part in parts)
        parts += shower_hardware_parts(shower_assembly)
    return with_material_refs(parts, material_refs)


def place_local(points: Sequence[Point], position: tuple[float, float],
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
