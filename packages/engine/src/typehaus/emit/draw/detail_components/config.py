"""Named dimensional configuration for the 2D detail vocabulary.

Every number the detail components draw lives here, grouped by the junction it belongs to
and traceable to the drawing that fixes it (the catlin-house ``Pset_ifcPlot_*`` params in
``tests/fixtures/catlin_reference/*.json``). A component module that inlines a dimension
makes the drawing unmaintainable — the value has to be findable from the reference param it
came from, and changeable in one place.

Two kinds of value live here, and the distinction matters:

* **Building facts** — a 1/4" sill gasket, a 4" french drain, a 1" slab thermal break. These
  are properties of the building that the model does not (yet) carry a field for. Each is
  marked with the reference param that fixes it, and with the model field that should
  eventually own it, so the constant can be deleted when the model grows one.
* **Drawing conventions** — schematic sheet-metal thickness, gutter proportions, the
  distance a flashing leg stands off a face. These are properties of the *drawing* and
  correctly live in the view, exactly as a grade line or a soil hatch does.
"""

from __future__ import annotations

from dataclasses import dataclass

LAYER = "A-DETL-CMPT"


@dataclass(frozen=True)
class PerimeterDrainConfig:
    """Perforated drain tile in its washed-rock surround at the footing.

    Building facts, from ``basementconstruction.json`` ``foundation``. The model now owns
    these — ``DrainTile.diameter`` / ``.rock_width`` / ``.rock_depth`` — and the detail reads
    the authored spec whenever the bedding carries one. What remains here is the fallback for
    a bedding that models the drain as the bare ``drain_tile: bool``: reference numbers, so a
    tile with no spec still draws at a real size instead of not drawing at all.
    """

    #: 4" perforated pipe (``foundation/french_drain_diameter_in``).
    drain_diameter_in: float = 4.0
    #: 10" x 8" washed-rock surround (``foundation/river_rock_width_in`` / ``_depth_in``).
    rock_width_in: float = 10.0
    rock_depth_in: float = 8.0
    #: Rock bedding under the pipe invert, so the pipe floats in stone rather than sitting
    #: on the footing — a drawing convention, not a dimension the reference fixes.
    pipe_bedding_in: float = 1.0
    #: Clear gap between the wall face and the near edge of the rock trench.
    rock_offset_from_wall_in: float = 1.0
    #: tan(22.5°): the pipe bore is drawn as a square-cut octagon because the IR has no arc
    #: primitive that both writers render.
    octagon_half_flat_ratio: float = 0.4142


PERIMETER_DRAIN = PerimeterDrainConfig()


@dataclass(frozen=True)
class SheetMetalConfig:
    """How sheet metal is drawn: thickness and the stand-offs its legs take.

    All drawing convention. Real flashing is ~0.025" thick, which vanishes at detail scale;
    the profiles are drawn at a schematic thickness so the leg directions read.
    """

    thickness_in: float = 0.5
    #: Gutter trough: depth (outboard run) x height (drop below the fascia head).
    gutter_depth_in: float = 5.0
    gutter_height_in: float = 5.0
    gutter_wall_thickness_in: float = 0.6
    #: Standoff of the gutter's back pan from the cladding face.
    gutter_standoff_in: float = 0.6
    #: Drip edge: how far back onto the deck it starts, and how far down the fascia it turns.
    drip_edge_back_in: float = 0.5
    drip_edge_run_in: float = 1.6
    drip_edge_drop_in: float = 2.4
    #: Apron flashing over the head of the wall cladding, behind the drip edge.
    apron_back_in: float = 2.6
    apron_run_in: float = 2.4
    apron_drop_in: float = 3.0
    #: Insect-screen band height at a vent opening.
    screen_band_in: float = 0.6


SHEET_METAL = SheetMetalConfig()


@dataclass(frozen=True)
class BasementToFramedWallConfig:
    """The basement→framed-wall transition (``basement_to_framed_wall_detail_ifc.png``)."""

    #: Building fact: 1/16" of *compressed* sill gasket under the treated mudsill. The
    #: source detail's ``sill/gasket_in`` states 1/4", which is the uncompressed roll; what
    #: this draws, and what a bearing seat is derived from, is the joint as built. Only the
    #: fallback — ``FramingSpec.sill_gasket`` on the wall's structure layer wins when the
    #: assembly states one, and states the same compressed dimension.
    sill_gasket_in: float = 0.0625
    #: Spray-foam sealant bead at the outer end of the L-flashing.
    sealant_bead_in: float = 0.75
    sealant_bead_height_in: float = 0.9
    #: L-flashing: where it starts above the junction and how far it drops.
    l_flashing_rise_in: float = 3.0
    l_flashing_drop_in: float = 2.85
    #: Z-flashing profile at the base of the rainscreen furring.
    z_flashing_rise_in: float = 2.4
    z_flashing_drop_in: float = 2.15
    z_flashing_lip_in: float = 0.55
    z_flashing_face_in: float = 4.2
    z_flashing_kick_in: float = 0.7
    z_flashing_kick_drop_in: float = 0.25
    #: Insect screen sits just above the Z-flashing's up-turned leg.
    screen_rise_in: float = 2.65


BASEMENT_TO_FRAMED_WALL = BasementToFramedWallConfig()


@dataclass(frozen=True)
class SlabEdgeConfig:
    """The slab perimeter at a foundation wall (``basementconstruction.json`` ``slab``)."""

    #: Building fact: 1" discrete XPS thermal break at the slab edge
    #: (``slab/thermal_break_in``). Belongs on the slab's assembly as a perimeter-edge layer.
    thermal_break_in: float = 1.0
    #: Building fact: 1/2" polyurethane sealant cap over it (``slab/sealant_in``).
    sealant_cap_in: float = 0.5


SLAB_EDGE = SlabEdgeConfig()


@dataclass(frozen=True)
class FoundationFaceConfig:
    """Protection and drainage applied to a foundation face where it surfaces at grade.

    Reference: the garage detail's "protective coating over exposed ICF EPS (above grade,
    both sides)" and the basement notes' "exposed XPS: protect with elastomeric coating or
    rigid metal/PVC trim". Exposed rigid foam is UV- and impact-vulnerable, so the drawing
    has to show the protection board wherever the foam surfaces.
    """

    #: Thickness of the protection board / parge coat drawn over the exposed foam, when the
    #: assembly does not model one. An assembly that authors the panel as a banded layer
    #: (``Layer.extent``) supplies its own thickness and band, and that wins — the drawing
    #: reads the resolved layer so the sheet and the order describe one piece of material.
    protection_board_in: float = 0.5
    #: Minimum exposed height worth drawing — below this the band is a smear at detail scale.
    min_exposed_height_in: float = 1.5


FOUNDATION_FACE = FoundationFaceConfig()


@dataclass(frozen=True)
class InteriorSlabDripConfig:
    """Interior drip flashing where an unheated slab-on-grade meets its stem wall.

    Reference: ``garage_wall_detail_side_ifc.png`` — "interior drip flashing turning water
    in onto the sloped slab". Water coming down the stem's interior face (blown past the
    overhead door, or condensation on the cold concrete) has to be turned out onto the
    slab, which slopes to the apron; without the flashing it wicks into the wall base.
    All drawing convention — the legs draw at schematic proportions so their directions
    read at detail scale.
    """

    #: How far the vertical leg rises up the wall's interior face above the slab surface.
    rise_in: float = 3.0
    #: How far the horizontal leg runs in over the slab surface.
    run_in: float = 2.5
    #: The drip kick at the inboard end, turned down with the slab's fall.
    kick_in: float = 0.5
    kick_drop_in: float = 0.25


INTERIOR_SLAB_DRIP = InteriorSlabDripConfig()


@dataclass(frozen=True)
class RimBandConfig:
    """The floor-band air seal at a storey stack (``rim-band-air-seal``).

    The rim joist is the hardest plane in a wood-framed wall to keep airtight: the sheathing
    is interrupted by the floor structure, so the air-control layer has to be carried across
    the band by a membrane outboard and beads of sealant at each plate line inboard.
    """

    #: Membrane strip carrying the air barrier across the band, on the sheathing face.
    air_barrier_thickness_in: float = 0.12
    #: How far the strip laps onto the sheathing above and below the band.
    air_barrier_lap_in: float = 3.0
    #: Sealant bead at each plate line, inboard face of the rim.
    sealant_bead_in: float = 0.6
    #: Spray-foam insulation in the rim cavity, applied to the inboard face of the rim.
    cavity_foam_in: float = 2.0
    #: Below this band depth there is no rim to draw — the stack is plate-on-plate.
    min_band_depth_in: float = 3.0


RIM_BAND = RimBandConfig()


@dataclass(frozen=True)
class StackWidthShelfConfig:
    """The exposed ledge where a wall steps in over a wider wall (``stack-width-shelf``).

    A wall that steps inboard leaves the top of the wall below exposed to the weather. That
    ledge is a horizontal water trap unless it is capped and drained, so the drawing carries
    a sloped shelf flashing with an up-turned back leg and a drip at the outboard edge.
    """

    #: Ledges narrower than this are a construction tolerance, not a shelf worth flashing.
    min_ledge_in: float = 0.25
    #: Height of the up-turned back leg, behind the wall above's water-control layer.
    back_leg_rise_in: float = 3.0
    #: Fall across the shelf (positive slope drains outward).
    slope_fall_in: float = 0.5
    #: Drip at the outboard edge: how far it projects and how far it turns down.
    drip_projection_in: float = 0.5
    drip_drop_in: float = 1.2


STACK_WIDTH_SHELF = StackWidthShelfConfig()


@dataclass(frozen=True)
class InteriorCurbCapConfig:
    """The interior curb left where a framed wall steps in over a wider masonry wall
    below (also ``stack-width-shelf``, the inboard sibling of :class:`StackWidthShelfConfig`).

    A masonry stem wider than the framed wall it carries leaves a ledge on the *inside* —
    a garage ICF stem under a 2x6 wall is the reference case. Nothing sheds weather there,
    but it is still a horizontal ledge behind the framed wall's interior drywall, and water
    running down that drywall's face (splash, a hosed-down wall, condensation) needs to be
    turned back into the room rather than tracking down into the ledge and the board joint
    below it. Scaled down from the exterior shelf: this tucks behind 5/8" drywall, not a
    full rainscreen water plane.
    """

    #: Ledges narrower than this are a construction tolerance, not a curb worth capping.
    min_ledge_in: float = 0.25
    #: Height of the up-turned back leg, behind the upper wall's interior drywall.
    back_leg_rise_in: float = 2.0
    #: Fall across the curb top (positive slope drains back into the room).
    slope_fall_in: float = 0.25
    #: Drip at the inboard edge: how far it projects and how far it turns down.
    drip_projection_in: float = 0.375
    drip_drop_in: float = 0.5


INTERIOR_CURB_CAP = InteriorCurbCapConfig()


# --- Sauna --------------------------------------------------------------------
# Building facts from ``saunashowerdetail.json``. Kept as flat module constants because the
# sauna's room-scale functions take them one at a time and the parity tests name them.

# Liner base (``finish``).
SAUNA_BASEBOARD_IN = 6.0     # finish/baseboard_height_in
SAUNA_FLASH_IN = 0.35        # finish/flashing_in
SAUNA_MEMBRANE_IN = 0.25     # finish/membrane_in

# Benches (``benches``) — the Law of Löyly: sit above the heater's stone line.
SAUNA_BENCH_DEPTH_IN = 20.0
SAUNA_BENCH_LOWER_TOP_IN = 18.0
SAUNA_BENCH_UPPER_TOP_IN = 36.0
SAUNA_BENCH_THK_IN = 1.5

# Heater clearance envelope (``heater``).
SAUNA_HEATER_W_IN = 10.0
SAUNA_HEATER_H_IN = 18.0

# Floor slope to drain (``sauna_floor_slope``): 1" fall over an 8' run.
SAUNA_FLOOR_RISE_IN = 1.0
SAUNA_FLOOR_RUN_IN = 96.0
SAUNA_FLOOR_DRAIN_WIDTH_IN = 3.0
SAUNA_FLOOR_DRAIN_DEPTH_IN = 1.0
SAUNA_FLOOR_DRAIN_LIP_IN = 0.5

# Structure above (``structure``).
SAUNA_DROP_DEPTH_IN = 3.5
SAUNA_DROP_GAP_IN = 1.0

#: A room narrower than this is a degenerate cut, not a sauna interior.
SAUNA_MIN_ROOM_WIDTH_IN = 12.0
#: Fractions of the room width at which drop-ceiling hangers are drawn.
SAUNA_HANGER_FRACTIONS = (0.2, 0.5, 0.8)


# --- Opening perimeter --------------------------------------------------------


@dataclass(frozen=True)
class OpeningDetailConfig:
    """The opening-perimeter vocabulary: head flashing, sill pan, concrete bucks.

    All drawing convention except the buck: flashing legs are drawn at schematic
    proportions so their directions read, while the 2x (1.5") buck is the treated lumber
    a frame actually fastens to in a concrete opening.
    """

    #: Head flashing: how far it laps up the WRB face, past the cladding, and drips down.
    head_flashing_rise_in: float = 3.0
    head_flashing_lip_in: float = 0.5
    head_flashing_drop_in: float = 1.6
    #: Sill pan: up-turned back dam inboard, projected lip + drip outboard.
    sill_pan_back_dam_in: float = 1.5
    sill_pan_lip_in: float = 0.75
    sill_pan_drop_in: float = 1.2
    #: Sealant bead at the cladding-to-frame joint under the head flashing.
    sealant_bead_in: float = 0.6
    #: Building fact: 2x treated buck lining a concrete opening (what the frame screws to).
    buck_in: float = 1.5

    # --- outie window in a truss wall (``outie-window-truss``) ----------------------
    #: Building fact: on a SWINBURNE truss wall the head/sill blocking the flange bears on
    #: is a 2x4 ON EDGE, so it stands 1-1/2" above the head and below the sill in the truss
    #: plane.
    truss_blocking_in: float = 1.5
    #: The same fact on a CATLIN TRUSS wall, where that piece is a 2x4 laid FLAT — the same
    #: board turned 90 degrees, so it stands 3-1/2". Both are here rather than one derived
    #: number because they are two different walls, and ``resolve.truss_kind`` is what picks
    #: between them; a detail that guessed would draw the head flashing 2" low on one of
    #: them and there is no way to see that on a sheet.
    #:
    #: 3-1/2" is the head/sill COURSE's face on the wall — a 2x4 laid flat — not the BLOCK
    #: behind it, whose depth the outie detail reads off the resolved stack instead.
    girt_blocking_in: float = 3.5
    #: How far the head flashing laps UP the spray-foam face before it turns out. Shorter
    #: than the innie head's 3" rise: it starts above the head blocking rather than behind a
    #: WRB, and the foam it laps is the water plane, bonded and seamless.
    outie_head_rise_in: float = 2.0
    #: How far the sill pan's outboard leg turns DOWN past the truss plane. It stops inside
    #: the rainscreen gap and discharges behind the cladding — an outie pan that ran out
    #: past the panel face would be a visible metal lip under every window. The gap is 1" on
    #: the Swinburne wall and 2" on the girt wall, and this clears either.
    outie_pan_drop_in: float = 0.75


OPENING_DETAIL = OpeningDetailConfig()


@dataclass(frozen=True)
class RidgeHangerConfig:
    """The LVL-ridge face-mount hanger (``lvl-ridge-hanger``), drawn schematically.

    A hanger stamping is ~14 ga steel, invisible at detail scale; the side plate and seat
    draw at sheet-metal convention thickness so the load path (plate on the beam face,
    seat under the rafter) reads.
    """

    #: How far below the beam top the side plate starts (clear of the rafter's top edge).
    top_offset_in: float = 1.0
    #: Side-plate drop down the beam face.
    plate_drop_in: float = 8.0
    #: Seat leg projecting out under the carried rafter.
    seat_in: float = 3.5


RIDGE_HANGER = RidgeHangerConfig()


# --- Shower -------------------------------------------------------------------
# Building facts from ``saunashowerdetail.json`` ``shower``. Flat module constants, like
# the sauna's, because the room-scale functions take them one at a time and the parity
# tests name them.

SHOWER_TILE_IN = 0.75        # shower/tile_in
SHOWER_BACKER_IN = 1.0       # shower/wall_backer_in
SHOWER_GLASS_IN = 0.5        # shower/glass_in
SHOWER_GLASS_GAP_IN = 1.0    # shower/glass_gap_in
SHOWER_RECESS_IN = 4.0       # shower/recess_in
#: The exhaust takeoff the reference fixes at the shower (shower/hrv_duct_in). The *drawn*
#: duct takes its size from the resolved run in ``model.ducts``; this is the parity pin.
SHOWER_HRV_DUCT_IN = 3.0

#: Drawing conventions: enclosure height when the fixture type carries none, the clearance
#: the drawn takeoff keeps above the enclosure, the drain grate, and how far past the
#: shower footprint a crossing duct still counts as serving it.
SHOWER_ENCLOSURE_H_IN = 84.0
SHOWER_HRV_CLEAR_IN = 2.0
SHOWER_DRAIN_WIDTH_IN = 3.0
SHOWER_DRAIN_DEPTH_IN = 1.0
SHOWER_DUCT_REACH_M = 0.6

#: How far (metres) beyond a shower footprint edge a wall face may sit and still count as
#: the walled side of the enclosure (backer + tile land there; the open side gets glass).
SHOWER_WALL_ABUT_TOLERANCE_M = 0.35


# --- Chrome -------------------------------------------------------------------

#: Annotation text height in model inches; the writers convert at the drawn scale.
TEXT_HEIGHT_IN = 1.5
#: Material legend swatch size and the vertical pitch between rows.
LEGEND_SWATCH_IN = 2.6
LEGEND_ROW_PITCH_IN = 3.6


# --- Breezeway glazing --------------------------------------------------------
# The enclosed breezeway's cross section (``params/breezeway.py``). Everything here is
# either a fabrication instruction the model has no field for (weep-hole pitch, breather
# tape) or a drawing convention (how thick a 0.05" extrusion is drawn at detail scale).


@dataclass(frozen=True)
class BreezewayGlazingConfig:
    """The multiwall-polycarbonate enclosure's drawn vocabulary.

    Building facts the model does not carry a field for:

    * ``wedge_rise_in`` / ``wedge_run_in`` — the tapered sleeper on every rafter that crowns
      the roof to each eave. A ``Beam`` is a prism, so the wedge cannot be a member; it is
      the reason the roof drains at all, so it has to be *drawn*.
    * ``weep_pitch_in`` — how far apart the bottom U-channel is drilled. Multiwall flutes
      hold water at their low end unless the channel is vented; the spacing is a shop
      instruction, invisible in any geometry.
    * ``breather_tape_in`` — the vented tape between each joist top and the decking, so the
      two never trap water against each other.

    Drawing conventions:

    * ``extrusion_draw_in`` — an aluminium glazing section is ~0.05" of metal, which vanishes
      at detail scale; the profiles draw at a schematic thickness so their legs read.
    * ``fastener_*`` — the gasketed stainless screw drawn as head + shank + washer.
    """

    #: Building fact: drainage wedge, 1" rise over the roof's 2'-0" half-span (~1:24). The
    #: roof is a single 4'x4' sheet bent over the crown, not two flat sheets meeting at a
    #: bar, so the rise has to stay inside 16mm multiwall's cold-bend range.
    wedge_rise_in: float = 1.0
    wedge_run_in: float = 24.0
    #: Building fact: weep holes at 24" o.c. through the low U-channel.
    weep_pitch_in: float = 24.0
    weep_diameter_in: float = 0.25
    #: Building fact: vented breather tape over each joist top, full joist width.
    breather_tape_in: float = 1.5
    #: Drawing convention: schematic thickness for an aluminium extrusion.
    extrusion_draw_in: float = 0.25
    #: Building facts for the shared H channel where the standing sheet's head meets the
    #: roof sheet's edge. ``_resolve_edge_run`` draws every profile as the same box, so the
    #: only place this joint reads as a *joint* is the 2D detail.
    #: ``h_slot_in`` is the slot each sheet enters (16mm sheet plus fitting clearance);
    #: ``h_lap_in`` is how far the legs grip it; ``h_web_in`` is the plate between them.
    h_slot_in: float = 0.75
    h_lap_in: float = 1.5
    h_web_in: float = 0.5
    #: Drawing convention: the gasketed panel fastener's drawn head/washer/shank.
    fastener_head_in: float = 0.5
    fastener_washer_in: float = 0.9
    fastener_shank_in: float = 1.75


BREEZEWAY_GLAZING = BreezewayGlazingConfig()
