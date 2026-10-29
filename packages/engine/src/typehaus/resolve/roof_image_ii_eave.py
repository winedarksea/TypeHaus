"""The Image II eave stack, resolved from the catalog sections and the roof's own layers.

One frame throughout, per eave run: ``u`` is plan distance outboard of the footprint edge
(the wall cladding's outer face), ``w`` is perpendicular height above the structure plane,
``z`` is vertical height above the run's own elevation (``ResolvedRoof.eave_z_m``), all in
meters. ``s`` runs down the pitch: ``u = s cos + w sin``, ``z = w cos - s sin``.

On the deck, bottom to top, every sheet ``LAP_GAP_M`` clear of the one below (GCP TL-15: the
metal goes over the membrane; IWSDET-102 option 2: a strip of membrane over the metal):
field membrane, the box gutter's roof flange, the Extended Eave (7/8 hem under its leg),
the membrane strip-in, the Image II pan. At the face line, inside to out: wall panel,
gutter back, eave face. The gutter itself is placed by the house (``params/roof_trim.py``);
this module reserves its room and says where it goes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.library.trim._image_ii import (
    EXTENDED_EAVE_LEGS_IN,
    EXTENDED_EAVE_REACH_IN,
    extended_eave_section,
    hem_offset_in,
)
from typehaus.library.trim.metal_sales import pbr_box_gutter_section
from typehaus.model.enums import LayerFunction
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M, _inset_section
from typehaus.resolve.roof_edge_geometry import EdgeRun, mating_faces, roof_slope
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

#: Clearance between stacked sheets, so no two share a face (and the viewer never z-fights).
LAP_GAP_M = inch(1 / 32).meters
#: What the wall-panel head and its closure keep under the lowest eave sheet. Clearance only:
#: the head's support is not the trim's job.
HEAD_CLEARANCE_M = LAP_GAP_M
#: The membrane strip-in over both flanges: 9 in, so it laps ~4 in past the eave's hem.
#: Provisional until GCP confirms the width.
STRIP_IN_WIDTH_M = inch(9).meters
#: The run a sheet takes to climb a step in the stack under it (the hem, the strip's edge).
STEP_RAMP_M = inch(0.5).meters
#: How far inboard of an eave line a wall-top element still counts as under that eave.
_HEAD_REACH_M = inch(12).meters
#: The pan's return under the eave lip after its 180 deg fold (Image II PIG pp. 20-23).
PAN_RETURN_M = inch(0.5).meters
#: How close a raked wall's top must ride the roof plane to be that roof's gable.
_ROOF_MEET_M = inch(4).meters


@dataclass(frozen=True)
class EaveStack:
    """The levels and face-line positions of one roof's Image II eave (meters, module frame)."""

    slope: float
    membrane_top_w: float
    strip_thickness_m: float
    strip_material: str | None
    strip_layer: str | None = None

    @property
    def cos(self) -> float:
        return 1.0 / math.hypot(1.0, self.slope)

    @property
    def sin(self) -> float:
        return self.slope * self.cos

    @property
    def factor(self) -> float:
        return math.hypot(1.0, self.slope)

    # -- levels (w) --------------------------------------------------------------------
    @property
    def gutter_flange_bottom_w(self) -> float:
        return self.membrane_top_w + LAP_GAP_M

    @property
    def gutter_flange_top_w(self) -> float:
        return self.gutter_flange_bottom_w + SHEET_24_GA_M

    @property
    def eave_bottom_w(self) -> float:
        """The underside of the 7/8 hem and of the lip's return: the eave's seat line."""
        return self.gutter_flange_top_w + LAP_GAP_M

    @property
    def eave_top_w(self) -> float:
        """The leg's weather face: the hem's plies and gap above the seat line."""
        return self.eave_bottom_w + _hem_offset_m()

    @property
    def head_cap_w(self) -> float:
        """Highest the wall-panel head and closure may stand: clear of the field membrane's
        underside, whose cut end overhangs the head's inner edge."""
        return self.membrane_top_w - self.strip_thickness_m - HEAD_CLEARANCE_M

    # -- face line (u) -----------------------------------------------------------------
    @property
    def gutter_back_inner_u(self) -> float:
        return LAP_GAP_M

    @property
    def gutter_back_outer_u(self) -> float:
        return self.gutter_back_inner_u + SHEET_24_GA_M

    @property
    def face_inner_u(self) -> float:
        return self.gutter_back_outer_u + LAP_GAP_M

    @property
    def corner_u(self) -> float:
        """The Extended Eave's origin: the face's outer surface where it meets the leg."""
        return self.face_inner_u + SHEET_24_GA_M

    # -- frame -------------------------------------------------------------------------
    def z_at(self, w: float, u: float) -> float:
        """Vertical height of level ``w`` at plan position ``u``."""
        return w * self.factor - u * self.slope

    def uz(self, s: float, w: float) -> tuple[float, float]:
        return (s * self.cos + w * self.sin, w * self.cos - s * self.sin)

    def sw(self, u: float, z: float) -> tuple[float, float]:
        return (u * self.cos - z * self.sin, u * self.sin + z * self.cos)

    @property
    def corner_z(self) -> float:
        return self.z_at(self.eave_bottom_w, self.corner_u)

    @property
    def corner_s(self) -> float:
        return self.sw(self.corner_u, self.corner_z)[0]

    @property
    def face_bottom_z(self) -> float:
        return self.corner_z - EXTENDED_EAVE_LEGS_IN[3] * M_PER_IN

    @property
    def hem_s(self) -> float:
        """The upslope fold of the 7/8 hem: the leg's inboard end."""
        return self.corner_s - EXTENDED_EAVE_REACH_IN * M_PER_IN

    @property
    def lip_s(self) -> float:
        """The lip's fold, outer face: the leg's outboard end."""
        return self.corner_s + EXTENDED_EAVE_LEGS_IN[2] * M_PER_IN

    @property
    def hem_tip_s(self) -> float:
        """Where the 7/8 hem ends under the leg: single-ply land starts downslope of it."""
        return self.hem_s + EXTENDED_EAVE_LEGS_IN[0] * M_PER_IN

    def eave_section(self) -> list[tuple[float, float]]:
        """The Extended Eave's weather-face path placed on the edge, (u, z)."""
        return [(self.corner_u + x * M_PER_IN, self.corner_z + y * M_PER_IN)
                for x, y in extended_eave_section(self.slope)]

    def gutter_origin(self) -> tuple[float, float]:
        """(u, z) of the box gutter's back top, the origin of ``pbr_box_gutter_section``.

        Its flange's top face rides the ``gutter_flange_top_w`` line under the eave leg and
        its back's outer face stands at ``gutter_back_outer_u``.
        """
        return (self.gutter_back_outer_u,
                self.z_at(self.gutter_flange_top_w, self.gutter_back_outer_u))

    def gutter_flange_tip_uz(self) -> tuple[float, float]:
        """(u, z) of the box gutter flange's upslope tip, its water face."""
        u0, z0 = self.gutter_origin()
        x, y = pbr_box_gutter_section(self.slope)[0]
        return u0 + x * M_PER_IN, z0 + y * M_PER_IN

    def gutter_flange_end_s(self) -> float:
        return self.sw(*self.gutter_flange_tip_uz())[0]

    # -- strip-in and pan --------------------------------------------------------------
    def _ramp(self) -> tuple[float, float]:
        """(start, end) in ``s`` of the climb over the gutter flange and the eave's hem."""
        end = self.hem_s
        return min(end, self.gutter_flange_end_s()) - STEP_RAMP_M, end

    def strip_up_s(self) -> float:
        return self.lip_s - STRIP_IN_WIDTH_M

    def strip_bottom_sw(self) -> list[tuple[float, float]]:
        start, end = self._ramp()
        field = self.membrane_top_w + LAP_GAP_M
        over = self.eave_top_w + LAP_GAP_M
        return [(self.strip_up_s(), field), (start, field), (end, over), (self.lip_s, over)]

    def strip_top_sw(self) -> list[tuple[float, float]]:
        return _inset_section(self.strip_bottom_sw(), -self.strip_thickness_m)

    def strip_ring(self) -> list[tuple[float, float]]:
        ring = [*self.strip_bottom_sw(), *reversed(self.strip_top_sw())]
        return [self.uz(s, w) for s, w in ring]

    def pan_cut_s(self) -> float:
        """Where the field skin stops: one ramp upslope of the strip's edge."""
        return self.strip_up_s() - STEP_RAMP_M

    def pan_cut_u(self) -> float:
        """Plan position of the skin's cut at the pan's underside (the roofing base)."""
        return self.uz(self.pan_cut_s(), self.membrane_top_w)[0]

    def pan_path_sw(self) -> list[tuple[float, float]]:
        """The pan end's weather face: over the strip and the stack, round the lip, back under."""
        sheet = SHEET_24_GA_M
        top = _inset_section(self.strip_top_sw(), -(LAP_GAP_M + sheet))
        fold = self.lip_s + LAP_GAP_M + sheet
        top[-1] = (fold, top[-1][1])
        under = self.eave_bottom_w - LAP_GAP_M - sheet
        return [(self.pan_cut_s(), self.membrane_top_w + sheet), *top, (fold, under),
                (fold - PAN_RETURN_M, under)]

    def lip_reach_u(self) -> float:
        """The roofing's plan reach on this eave: the pan's fold round the lip."""
        return max(self.uz(s, w)[0] for s, w in self.pan_path_sw())

    def seam_flats(self) -> list[tuple[float, float, float]]:
        """(u0, u1, lift) for each stretch the seam legs ride at one height over the stack.

        ``lift`` is the pan underside's rise above the field (``membrane_top_w``); the
        legs stop at the face line, short of the fold.
        """
        start, end = self._ramp()
        field = self.strip_top_sw()[0][1] + LAP_GAP_M
        over = self.eave_top_w + 2 * LAP_GAP_M + self.strip_thickness_m
        out = []
        for s0, s1, w in ((self.strip_up_s(), start, field), (end, self.corner_s, over)):
            out.append((self.uz(s0, w)[0], self.uz(s1, w)[0], w - self.membrane_top_w))
        return out


def _hem_offset_m() -> float:
    return hem_offset_in() * M_PER_IN


def eave_stack(model, roof) -> EaveStack | None:
    """The roof's eave stack, or ``None`` when its covering names no Image II kit."""
    from typehaus.resolve.roof_image_ii import image_ii_covering

    if not image_ii_covering(model, roof):
        return None
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    membranes = [layer for layer in layers if layer.function is LayerFunction.MEMBRANE]
    strip = membranes[-1] if membranes else None
    return EaveStack(
        slope=abs(roof_slope(roof)), membrane_top_w=mating_faces(layers).cladding_under,
        strip_thickness_m=strip.thickness.meters if strip else 0.0,
        strip_material=strip.material_ref if strip else None,
        strip_layer=strip.name if strip else None)


@dataclass(frozen=True)
class EaveBearing:
    """How the placed Extended Eave sits on its deck, in plan (meters, ``u`` outboard)."""

    deck_edge_u: float      # the deck's top outer corner
    leg_inboard_u: float    # the pitched leg's inboard end (the hem fold)
    hem_tip_u: float        # the 7/8 hem's free end, where single-ply land begins

    @property
    def bearing_m(self) -> float:
        """Plan overlap of the pitched leg inboard of the deck edge (FORTIFIED §4.5)."""
        return self.deck_edge_u - self.leg_inboard_u

    @property
    def fastener_land_m(self) -> float:
        """Single-ply leg over the deck, between the hem tip and the deck edge."""
        return self.deck_edge_u - self.hem_tip_u

    @property
    def fastener_edge_distance_m(self) -> float:
        """The fastener line at the land's middle, to the deck edge."""
        return self.fastener_land_m / 2.0


def eave_deck_bearing(model, roof, run: EdgeRun) -> EaveBearing | None:
    """The resolved bearing of ``run``'s Extended Eave on the deck, from placed geometry.

    The deck's eave edge is cut square to the pitch through its setback on the structure
    plane (``geometry_roofs.layer_inset_rect``), so its top corner sits the deck's own
    thickness x sin further out.
    """
    from typehaus.resolve.roof_drip_edge import deck_edge_m

    stack = eave_stack(model, roof)
    if stack is None:
        return None
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    deck = next((layer for layer in layers if layer.function is LayerFunction.SHEATHING), None)
    deck_t = deck.thickness.meters if deck else 0.0
    section = stack.eave_section()
    hem_tip_u = section[0][0]
    leg_inboard_u = min(u for u, _ in section[:3])
    return EaveBearing(deck_edge_m(roof, layers, run) + deck_t * stack.sin, leg_inboard_u,
                       hem_tip_u)


def wrapped_eave_head_cap_w(model, roof, point: tuple[float, float]) -> float | None:
    """``EaveStack.head_cap_w`` where ``point`` stands under a wrapped Image II eave, else None.

    "Under" is within the wall stack's reach of that eave's line (``_HEAD_REACH_M``).
    """
    from typehaus.resolve.roof_edge_geometry import roof_edge_runs
    from typehaus.resolve.roof_image_ii import wrapped_image_ii_edges

    edges = wrapped_image_ii_edges(model, roof)
    stack = eave_stack(model, roof) if edges else None
    if stack is None:
        return None
    for run in roof_edge_runs(roof):
        if not run.is_eave or run.edge_name not in edges:
            continue
        nx, ny = run.normal
        offset = (point[0] - run.p0[0]) * nx + (point[1] - run.p0[1]) * ny
        if -_HEAD_REACH_M <= offset <= LAP_GAP_M:
            return stack.head_cap_w
    return None



def wrapped_eave_deck_cut(model, roof, point: tuple[float, float], *,
                          level_inboard: bool = True) -> tuple[float, float] | None:
    """(z, rise) of the deck's square-cut eave end over ``point`` under a wrapped Image II eave
    (the reach of ``wrapped_eave_head_cap_w``), else None.

    Outboard of the deck's bottom corner, ``z`` is the cut face's height at ``point`` and it
    rises ``1/slope`` per meter further out; inboard, the corner's height, level (the
    underside's lowest over anything standing there), or with ``level_inboard`` False the cut
    face's plane carried on (one clip plane, conservative there).
    """
    from typehaus.resolve.roof_edge_geometry import roof_edge_runs
    from typehaus.resolve.roof_image_ii import wrapped_image_ii_edges

    edges = wrapped_image_ii_edges(model, roof)
    stack = eave_stack(model, roof) if edges else None
    if stack is None or stack.slope <= 0.0:
        return None
    for run in roof_edge_runs(roof):
        if not run.is_eave or run.edge_name not in edges:
            continue
        nx, ny = run.normal
        offset = (point[0] - run.p0[0]) * nx + (point[1] - run.p0[1]) * ny
        if not -_HEAD_REACH_M <= offset <= LAP_GAP_M:
            continue
        corner = _deck_corner(model, roof, run, stack)
        if corner is None:
            return None
        corner_u, corner_z = corner
        if level_inboard and offset < corner_u - 1e-9:
            return corner_z, 0.0
        return corner_z + (offset - corner_u) / stack.slope, 1.0 / stack.slope
    return None


def _deck_corner(model, roof, run: EdgeRun, stack: EaveStack) -> tuple[float, float] | None:
    """(u, z) of the deck's bottom outer corner on ``run``: its square-cut end meets the
    underside there. ``None`` for a stack with no deck."""
    from typehaus.resolve.roof_drip_edge import deck_edge_m
    from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate

    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    under_w = 0.0
    for layer in layers:
        if layer.function is LayerFunction.SHEATHING:
            break
        under_w += layer.thickness.meters
    else:
        return None
    corner_u = deck_edge_m(roof, layers, run)
    at = (run.p0[0] + run.normal[0] * corner_u, run.p0[1] + run.normal[1] * corner_u)
    return corner_u, roof_plane_z(roof, roof_slope_coordinate(roof, at)) + under_w * stack.factor


@dataclass(frozen=True)
class HeadCap:
    """The ``head_cap_w`` line of one wrapped eave as a plan plane: nothing standing under
    the eave stack rises above it. Applies from ``_HEAD_REACH_M`` inboard of the eave line
    out to the roofing's lip (meters; ``normal`` outboard; ``fall`` per meter outboard).

    ``deck_u``/``deck_z`` is the deck's bottom outer corner: the line sits above the deck's
    underside, so a gable layer under the deck is also held below the underside, or
    ``deck_clear`` under the square-cut end that rises from that corner (the eave
    wall's closure rule, ``board_batten._deck_cut_at``)."""

    p0: tuple[float, float]
    normal: tuple[float, float]
    z_line: float
    fall: float
    reach_out: float
    reach_in: float = _HEAD_REACH_M
    deck_u: float | None = None
    deck_z: float | None = None
    deck_clear: float = HEAD_CLEARANCE_M

    def z_at(self, x: float, y: float) -> float | None:
        offset = (x - self.p0[0]) * self.normal[0] + (y - self.p0[1]) * self.normal[1]
        if not -self.reach_in <= offset <= self.reach_out:
            return None
        z = self.z_line - self.fall * offset
        if self.deck_u is not None and self.fall > 0.0:
            du = offset - self.deck_u
            z = min(z, self.deck_z + max(-self.fall * du, du / self.fall - self.deck_clear))
        return z

    def kinks(self) -> tuple[float, ...]:
        """Offsets where ``z_at`` bends: a top sampled only at ring vertices needs them."""
        if self.deck_u is None or self.fall <= 0.0:
            return ()
        rise = 1.0 / self.fall
        cut = self.deck_u + self.deck_clear / (self.fall + rise)
        # The raised cut meets the line: deck_z + (u - deck_u) rise - c = z_line - fall u.
        meet = ((self.z_line - self.deck_z + self.deck_clear + self.deck_u * rise)
                / (self.fall + rise))
        return tuple(u for u in (cut, meet) if -self.reach_in < u < self.reach_out)


def roof_head_caps(model, roof) -> tuple[HeadCap, ...]:
    """One ``HeadCap`` per wrapped Image II eave of ``roof``."""
    from typehaus.resolve.roof_edge_geometry import roof_edge_runs
    from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate
    from typehaus.resolve.roof_image_ii import wrapped_image_ii_edges

    edges = wrapped_image_ii_edges(model, roof)
    stack = eave_stack(model, roof) if edges else None
    if stack is None:
        return ()
    caps = []
    for run in roof_edge_runs(roof):
        if not run.is_eave or run.edge_name not in edges:
            continue
        deck_u, deck_z = _deck_corner(model, roof, run, stack) or (None, None)
        caps.append(HeadCap(run.p0, run.normal,
                            roof_plane_z(roof, roof_slope_coordinate(roof, run.p0))
                            + stack.head_cap_w * stack.factor, stack.slope,
                            stack.lip_reach_u(), deck_u=deck_u, deck_z=deck_z))
    return tuple(caps)


def capped_z(caps, x: float, y: float, z: float) -> float:
    """``z`` held under every cap that reaches plan point (x, y)."""
    for cap in caps:
        limit = cap.z_at(x, y)
        if limit is not None and limit < z:
            z = limit
    return z


def assign_wall_head_caps(model) -> None:
    """Give each gable wall raked to a wrapped Image II roof that roof's ``HeadCap`` lines.

    Only a raked wall whose top meets the roof plane: its layers past the axis end stand
    flat at the axis-end height, which near an eave is inside the stack.
    """
    from dataclasses import replace

    from typehaus.resolve.geometry_walls import is_raked, wall_top_at
    from typehaus.resolve.roof_edge_geometry import footprint_test
    from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate

    for roof in model.roofs:
        caps = roof_head_caps(model, roof)
        if not caps:
            continue
        inside = footprint_test(roof)
        for index, wall in enumerate(model.walls):
            if not is_raked(wall) or not inside(wall) or any(
                    abs(wall_top_at(wall, *p) - roof_plane_z(roof, roof_slope_coordinate(roof, p)))
                    > _ROOF_MEET_M for p in wall.axis):
                continue
            model.walls[index] = replace(wall, head_caps=wall.head_caps + caps)
