"""The rows of the ``SolidCategory`` registry (:mod:`.solid_categories`).

Several rows carry ``ifc_class="IfcFooting"`` for things that are not footings (a plant, a
glazing panel, a sleeve). That is the old silent fallback made visible: registered as-is so
the IFC export stayed byte-identical, and each one is now a one-field fix.
"""

from __future__ import annotations

from typehaus.resolve.solid_categories import SolidCategory as C

_FOOTING = "IfcFooting"  # the former fallback; see the module docstring
_COVER = "IfcCovering"
_ACC = "IfcDiscreteAccessory"
_PIPE = "IfcPipeSegment"
_CHAMBER = "IfcDistributionChamberElement"
_GEO = "IfcGeographicElement"
_HARD = "hard"  # a placeable body may not enter it


def _pipe(system: str) -> C:
    """A routed pipe run: exported as segments by ``emit/ifc/mep.py``, billed by the foot."""
    return C(f"pipe_{system}", trade="plumbing", billed_elsewhere=True, collision=_HARD)


def _duct(system: str) -> C:
    return C(f"duct_{system}", trade="mechanical", billed_elsewhere=True, collision=_HARD)


def _accessory(kind: str, trade: str | None = "plumbing") -> C:
    """An in-line supply device: ``_emit_pipe_accessories`` owns its IFC."""
    return C(kind, trade=trade, billed_elsewhere=True)


def _trim(name: str, trade: str, ifc: str | None = _COVER, elevation: str | None = "trim",
          finish: str | None = "accessory") -> C:
    return C(name, trade=trade, ifc_class=ifc, elevation_family=elevation,
             finish_group=finish, billed_elsewhere=True)


def _drain(name: str, ifc: str, predefined: str, object_type: str | None = None,
           elevation: str | None = None) -> C:
    """Stormwater: IFC groups exactly these into ``IfcDistributionSystem/STORMWATER``."""
    return C(name, trade="drainage", ifc_class=ifc, ifc_predefined=predefined,
             ifc_object_type=object_type, elevation_family=elevation,
             finish_group="accessory", billed_elsewhere=True)


ROWS: tuple[C, ...] = (
    # Standalone structure: same lumber as the studs; a concrete pier re-files by material.
    C("beam", trade="framing", ifc_class="IfcBeam", elevation_family="body",
      finish_group="element", material_refile="cast", supports_on_top=True, collision=_HARD),
    C("column", trade="framing", ifc_class="IfcColumn", elevation_family="body",
      finish_group="element", material_refile="cast", supports_on_top=True, collision=_HARD),
    # Routed plumbing, one category per PipeSystem.
    *(_pipe(s) for s in ("drain", "vent", "water_hot", "water_cold", "gas", "radon",
                         "sump_discharge")),
    # In-line supply devices, one per PipeAccessoryKind. ``trap_primer`` has no trade row
    # and takes the fallback trade (unchanged behaviour).
    *(_accessory(k) for k in ("main_shutoff", "shutoff", "backflow_preventer",
                              "vacuum_breaker", "water_hammer_arrestor", "ro_stub",
                              "penetration_seal")),
    _accessory("trap_primer", trade=None),
    # A cast-in block-out, graded by the plumbing rough-in rules.
    C("pipe_sleeve", trade="plumbing", ifc_class=_FOOTING),
    # Raceways, split power vs comms for colour.
    C("conduit_power", trade="electrical", billed_elsewhere=True, collision=_HARD),
    C("conduit_data", trade="electrical", billed_elsewhere=True, collision=_HARD),
    # Vent terminals and routed air.
    _trim("vent", "mechanical", ifc="IfcBuildingElementProxy"),
    *(_duct(s) for s in ("supply", "return", "exhaust", "dryer", "transfer", "outdoor_air")),
    # Fenestration.
    _trim("glazing", "openings", ifc=_FOOTING, elevation="glaz"),
    _trim("glazing_trim", "openings", ifc=_FOOTING, elevation="sash"),
    # Roof edge trim and what fastens into the standing seam.
    _trim("flashing", "roofing"),
    C("ridge_cap", trade="roofing", ifc_class=_FOOTING, finish_group="accessory"),
    _trim("snow_guard", "roofing", ifc=_ACC),
    # A 3" clip is a dot at 1/4"=1'-0": real, visible, and not drawn in elevation.
    _trim("seam_clamp", "roofing", ifc=_ACC, elevation=None),
    _trim("panel_strap", "roofing", ifc=_ACC, elevation=None),
    # The siding contractor's trim.
    _trim("fascia", "siding"),
    _trim("eave_soffit", "siding"),
    _trim("wall_corner", "siding"),
    _trim("beam_cap", "siding"),
    _trim("bug_screen", "siding", ifc=_FOOTING, elevation=None),
    _trim("screen_slat", "siding", ifc=_FOOTING, elevation=None, finish=None),
    _trim("movement_joint", "masonry"),  # a brick wythe's sealant end joint
    # Stormwater, gutter to daylight.
    _drain("gutter", _PIPE, "GUTTER", elevation="trim"),
    _drain("downspout", _PIPE, "RIGIDSEGMENT", elevation="trim"),
    _drain("sump", _CHAMBER, "SUMP"),
    _drain("drain_tile", _PIPE, "FLEXIBLESEGMENT"),
    _drain("french_drain", _CHAMBER, "TRENCH"),
    _drain("drywell", _CHAMBER, "USERDEFINED", "SOAKAWAY"),
    _drain("rain_garden_media", _CHAMBER, "USERDEFINED", "BIORETENTION"),
    _drain("rain_garden_stone", _CHAMBER, "USERDEFINED", "BIORETENTION"),
    _drain("leader_extension", _PIPE, "RIGIDSEGMENT"),
    _drain("area_drain", "IfcWasteTerminal", "GULLYSUMP"),
    _drain("area_drain_riser", _PIPE, "RIGIDSEGMENT"),
    # Illustrative planting and a planting bed's own earth (resolve/landscape.py).
    C("plant", trade="landscaping", ifc_class=_FOOTING, finish_group="accessory"),
    C("trellis", trade="landscaping", ifc_class=_FOOTING, finish_group="accessory"),
    C("planting_soil", trade="landscaping", ifc_class=_GEO, ifc_predefined="USERDEFINED",
      ifc_object_type="PLANTING_SOIL", finish_group="accessory"),
    C("planting_fill", trade="earth", ifc_class=_GEO, ifc_predefined="USERDEFINED",
      ifc_object_type="TERRACE_FILL", finish_group="accessory"),
    # A slab's drawn base course: re-filed by its layer's material, as the takeoff bills it.
    C("sub_slab", trade="earth", ifc_class=_FOOTING, finish_group="element",
      material_refile="layer"),
    # The drywaller's overhead surfaces.
    C("soffit", trade="drywall", ifc_class=_COVER, elevation_family="body",
      finish_group="accessory", billed_elsewhere=True, collision=_HARD),
    C("ceiling", trade="drywall", ifc_class=_COVER, ifc_predefined="CEILING",
      billed_elsewhere=True),
    # Pours, and what is cast into them.
    C("slab", trade="concrete", ifc_class="IfcSlab", elevation_family="body",
      finish_group="element", material_refile="laid", is_pour=True, slab_family="slab",
      supports_on_top=True, collision=_HARD),
    # A Slab that is not a pour (resolve/slab_kind.py): laid decking, a wall-carried
    # platform, a ground band. Routed as a slab; the material re-files its trade.
    *(C(f"slab_{kind}", trade="concrete", ifc_class="IfcSlab", elevation_family="body",
        finish_group="element", material_refile="laid", slab_family="slab",
        supports_on_top=True, collision=_HARD)
      for kind in ("deck", "platform", "band")),
    C("footing", trade="concrete", ifc_class=_FOOTING, elevation_family="body",
      finish_group="element", material_refile="laid", is_pour=True, supports_on_top=True,
      collision=_HARD),
    C("pad", trade="concrete", ifc_class=_FOOTING, elevation_family="body",
      finish_group="element", material_refile="laid", is_pour=True, supports_on_top=True,
      collision=_HARD),
    C("dowel", trade="concrete", ifc_class="IfcReinforcingBar", finish_group="accessory"),
    C("thermal_break", trade="concrete", ifc_class="IfcBuildingElementProxy",
      finish_group="accessory"),
    # Guards and handrails. Infill exports as part of its railing (diff/semantic.py has no
    # IfcPlate row, so a lite exported that way would vanish from the census).
    _trim("railing", "stairs", ifc="IfcRailing", elevation="rail"),
    _trim("railing_infill", "stairs", ifc="IfcRailing", elevation="rail"),
    _trim("railing_glass", "stairs", ifc="IfcRailing", elevation=None),
    # Structural hardware rides with the members it joins. The carved-off families stay
    # FRAMING deliberately: this decides the viewer's container, the cost code decides who
    # is quoted (takeoff/cost_codes.py).
    _trim("connector", "framing", ifc="IfcMechanicalFastener", elevation=None),
    _trim("connector_embedded", "framing", ifc=_FOOTING, elevation=None, finish=None),
    _trim("connector_hanger", "framing", ifc=_FOOTING, elevation=None, finish=None),
    # Geometry-IR kinds that are not ResolvedSolid categories.
    C("wall", elevation_family="body", non_solid=True, collision=_HARD),
    C("floor", elevation_family="body", finish_group="element", non_solid=True,
      supports_on_top=True, collision=_HARD),
    C("roof", elevation_family="roof", finish_group="element", non_solid=True),
    C("solar_panel", elevation_family="roof", non_solid=True),
    C("earth", finish_group="element", non_solid=True),
    C("framing", non_solid=True),
    # A placeable's body (resolve/placeable_bodies.py). The glTF draws it from canvas_objects.
    C("equipment", trade="mechanical", elevation_family="body", non_solid=True,
      collision=_HARD),
    # Drawn by elevation_project's own part split (glass / door / sash), not by family.
    C("opening", non_solid=True),
)
