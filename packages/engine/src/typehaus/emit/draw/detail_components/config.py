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

M_TO_IN = 39.37007874015748

LAYER = "A-DETL-CMPT"


@dataclass(frozen=True)
class PerimeterDrainConfig:
    """Perforated drain tile in its washed-rock surround at the footing.

    Building facts, from ``basementconstruction.json`` ``foundation``. **These belong on the
    model, not the view**: ``FootingBedding`` currently models the drain as a bare
    ``drain_tile: bool`` with no size, so the drawing has nowhere to read them from. Until
    ``FootingBedding`` grows ``drain_diameter`` / ``drain_rock_width`` / ``drain_rock_depth``
    (``model/structure.py``, outside this workstream's ownership), the reference numbers are
    pinned here rather than scattered through the drawing code.
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

    #: Building fact: 1/4" sill gasket under the treated mudsill
    #: (``basementtoframedwalldetail.json`` ``sill/gasket_in``). Belongs on the wall's
    #: ``FramingSpec`` (a ``sill_gasket`` thickness) once the model carries one.
    sill_gasket_in: float = 0.25
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

    #: Thickness of the protection board / parge coat drawn over the exposed foam.
    protection_board_in: float = 0.5
    #: Minimum exposed height worth drawing — below this the band is a smear at detail scale.
    min_exposed_height_in: float = 1.5


FOUNDATION_FACE = FoundationFaceConfig()


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
SAUNA_CEILING_SLAB_IN = 9.0
SAUNA_CLEAR_HEIGHT_IN = 108.0
SAUNA_DROP_DEPTH_IN = 3.5
SAUNA_DROP_GAP_IN = 1.0

#: A room narrower than this is a degenerate cut, not a sauna interior.
SAUNA_MIN_ROOM_WIDTH_IN = 12.0
#: Fractions of the room width at which drop-ceiling hangers are drawn.
SAUNA_HANGER_FRACTIONS = (0.2, 0.5, 0.8)


# --- Chrome -------------------------------------------------------------------

#: Annotation text height in model inches; the writers convert at the drawn scale.
TEXT_HEIGHT_IN = 1.5
#: Material legend swatch size and the vertical pitch between rows.
LEGEND_SWATCH_IN = 2.6
LEGEND_ROW_PITCH_IN = 3.6
