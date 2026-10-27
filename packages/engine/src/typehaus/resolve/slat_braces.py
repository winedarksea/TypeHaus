"""Resolve a SlatBrace: the frame, 45° slats, or one exact corner diagonal per bay.

``slat_layout`` is the ONE rule for which slats there are and where they land; the resolver,
the dead load (``resolve/assembly_weight``) and the engineering (``engineering/
lateral_band_slats``) all read it. Oracle: ``houses/catlin/notes/canopy_west_band.md`` §3a.

Each bay has its own frame: ``u`` runs from the chord face toward the centre post, ``z`` up
from the sill's top. A slat's centreline is ``z = u - c``, so every slat rises toward the
centre, and ``c_j = (W - H)/2 + j * pitch`` centres the set on the bay.

A slat is ``braced`` when a KBS1Z's support leg stays on its bearing face at both ends. One
ending in a frame corner (catlin's j = 0) would run its leg into the plate, so it is screwed
infill: drawn and billed as lumber, but no connector, and no share of the brace force.
The corner layout's exact diagonal keeps the standard open knee: each heel sits where the
clipped end leaves its bearing face, the support leg running back toward the corner, so the
brace face must put both heels at least a leg from their corners (a 6x6 does; a 4x6 not).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.findings import Finding, element_error
from typehaus.model.braces import SlatBrace
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.kbs_geometry import KBS_GEOMETRY, kbs_heel_spacing
from typehaus.resolve.model import FramedMember, ResolvedBrace, ResolvedModel
from typehaus.resolve.slat_cuts import clipped_slat_profile, slat_blank_length

_ROOT2 = math.sqrt(2.0)


@dataclass(frozen=True)
class Slat:
    """One slat in its bay's frame, metres. ``low``: "sill" | "chord"; ``high``: "centre" |
    "top"."""

    bay: int  # 0: the bay at the start chord, 1: the bay at the end chord
    j: int
    c: float
    u0: float
    u1: float
    low: str
    high: str
    braced: bool = True  # False: screwed infill, no connector (module docstring)
    slope: float = 1.0

    def elevation(self, u: float) -> float:
        return self.slope * u - self.c

    @property
    def length(self) -> float:
        return (self.u1 - self.u0) * math.hypot(1.0, self.slope)


@dataclass(frozen=True)
class SlatLayout:
    """The frame's dimensions and its slats, metres along the start→end line."""

    length: float  # chord centre to chord centre
    chord_face: float  # half the chord: its face stands this far from its centre
    centre_half: float  # half the centre post
    plate: float  # a flat plate's thickness
    width: float  # a bay, chord face to centre-post face
    height: float  # a bay, sill top to top-plate underside
    pitch: float  # along a plate
    slats: tuple[Slat, ...]

    def bay(self, index: int) -> tuple[Slat, ...]:
        return tuple(s for s in self.slats if s.bay == index)

    def braces(self, index: int) -> tuple[Slat, ...]:
        """One bay's braced slats: the ones carrying the band's force."""
        return tuple(s for s in self.bay(index) if s.braced)

    def crossing_mid(self, index: int) -> int:
        """Braced slats crossing mid-band in one bay. The verticals' shear is zero there."""
        z = self.height / 2.0
        return sum(1 for s in self.braces(index) if s.u0 <= (s.c + z) / s.slope <= s.u1)

    def station(self, bay: int, u: float) -> float:
        """Distance along start→end of a bay-frame ``u``."""
        if bay == 0:
            return self.chord_face + u
        return self.length - self.chord_face - u


def slat_layout(el: SlatBrace) -> SlatLayout | None:
    """The slats a SlatBrace resolves to, or ``None`` when its frame leaves no bay."""
    (x0, y0), (x1, y1) = el.start.xy_m, el.end.xy_m
    length = math.hypot(x1 - x0, y1 - y0)
    chord_face = (cross_section(el.chord_size).width_m or 0.0) / 2.0
    centre_half = (cross_section(el.centre_post).width_m or 0.0) / 2.0
    plate = cross_section(el.plate).width_m or 0.0
    width = (length - 2.0 * chord_face) / 2.0 - centre_half
    height = el.top_elevation.meters - el.base_elevation.meters - 2.0 * plate
    face = cross_section(el.slat).width_m or 0.0
    if width <= 0.0 or height <= 0.0 or face <= 0.0:
        return None
    if el.corner_to_corner:
        # Open-knee heels at face/(2 cos θ) up the post and face/(2 sin θ) along the plate;
        # each support leg runs from its heel back toward the corner.
        half_vertical = face * math.hypot(1.0, height / width) / 2.0
        half_horizontal = half_vertical * width / height
        leg = KBS_GEOMETRY.leg_length_m - 1e-9
        fits = half_vertical >= leg and half_horizontal >= leg
        slats = tuple(Slat(bay, 0, 0.0, 0.0, width, "chord", "top",
                           el.connector != "KBS1Z" or fits, height / width)
                      for bay in (0, 1)
                      if math.hypot(width, height) >= el.min_slat_length.meters - 1e-9)
        return SlatLayout(length, chord_face, centre_half, plate, width, height, 0.0, slats)
    pitch = (face + el.clear_gap.meters) * _ROOT2
    c_mid = (width - height) / 2.0
    reach = int((width + height) / pitch) + 1 if el.brace_offset is None else 0
    slats = []
    for bay in (0, 1):
        for j in range(-reach, reach + 1):
            c = (c_mid + j * pitch if el.brace_offset is None
                 else el.brace_offset.meters)
            u0, u1 = max(0.0, c), min(width, height + c)
            if u1 <= u0 or (u1 - u0) * _ROOT2 < el.min_slat_length.meters - 1e-9:
                continue
            low, high = "sill" if c > 0.0 else "chord", "centre" if height + c > width else "top"
            braced = el.connector != "KBS1Z" or _kbs_fits(c, low, high, width, height, face)
            slats.append(Slat(bay, j, c, u0, u1, low, high, braced))
    return SlatLayout(length, chord_face, centre_half, plate, width, height, pitch,
                      tuple(slats))


def _kbs_fits(c: float, low: str, high: str, width: float, height: float,
              face: float) -> bool:
    """Both KBS1Z support legs stay on their bearing faces. Each runs ``leg`` away from the
    heel, the outside long edge, ``face / √2`` past the centreline (slat_connectors)."""
    reach = face / _ROOT2 + KBS_GEOMETRY.leg_length_m
    low_room = -c if low == "chord" else c  # heel's distance from the corner, along the face
    high_room = height - (width - c) if high == "centre" else width - (height + c)
    return low_room >= reach - 1e-9 and high_room >= reach - 1e-9


def resolve_slat_brace(model: ResolvedModel, el: SlatBrace, storey: str) -> list[Finding]:
    """The sill, the top plate, the centre post and the slats, on one ``ResolvedBrace``.

    Each board is clipped to the bay faces, including its long points at a frame corner.
    Engineering uses its centreline; lumber nesting uses the blank spanning its miters.
    """
    layout = slat_layout(el)
    if el.corner_to_corner and el.brace_offset is not None:
        return [element_error("integrity.slat_brace",
                              "corner_to_corner and brace_offset are alternative layouts", el.tag)]
    if layout is None:
        return [element_error("integrity.slat_brace", "the frame leaves no bay between the "
                              "chords, plates and centre post", el.tag)]
    if el.connectors_per_end == 2:
        depth = cross_section(el.slat).depth_m
        frame_depths = [cross_section(profile).depth_m
                        for profile in (el.chord_size, el.plate, el.centre_post)]
        if (any(not math.isclose(depth, width, abs_tol=1e-9) for width in frame_depths)
                or abs(el.plane_offset.meters) > 1e-9):
            return [element_error(
                "integrity.slat_brace", "two connectors per end require equal-width members "
                "with both faces flush (zero plane_offset)", el.tag)]
    if (el.brace_offset is not None or el.corner_to_corner) and (
            len(layout.slats) != 2 or not all(s.braced for s in layout.slats)):
        return [element_error(
            "integrity.slat_brace", "brace_offset/corner_to_corner leaves no brace "
            "or a KBS1Z leg runs off "
            "its bearing face; move the brace away from the frame corner", el.tag)]
    need = kbs_heel_spacing()
    if (el.brace_offset is None and not el.corner_to_corner
            and el.connector == "KBS1Z" and layout.pitch < need - 1e-9):
        return [element_error(
            "integrity.slat_brace",
            f"slats {layout.pitch / 0.0254:.3f}\" apart along a plate, but a KBS1Z at each end "
            f"needs {need / 0.0254:.3f}\": neighbouring connectors would overlap. Widen "
            f"clear_gap", el.tag)]
    (x0, y0), (x1, y1) = el.start.xy_m, el.end.xy_m
    ux, uy = (x1 - x0) / layout.length, (y1 - y0) / layout.length
    material = assembly_structure_material(model.plan, el.assembly)
    uid = el.uid or el.tag
    plate_width = cross_section(el.plate).depth_m or 0.0
    base, top = el.base_elevation.meters, el.top_elevation.meters

    def at(station: float, offset: float = 0.0) -> tuple[float, float]:
        return (x0 + ux * station - uy * offset, y0 + uy * station + ux * offset)

    def member(key: str, category: str, profile: str, p0, p1, z0, z1, length, **kw):
        return FramedMember(parent_uid=uid, child_key=key, category=category,
                            profile=profile, p0=p0, p1=p1, z0_m=z0, z1_m=z1,
                            length_m=length, material=material, **kw)

    a, b = layout.chord_face, layout.length - layout.chord_face
    members = [
        member("plate-sill", "plate", el.plate, at(a), at(b), base, base + layout.plate,
               b - a, plan_width_m=plate_width),
        member("plate-top", "plate", el.plate, at(a), at(b), top - layout.plate, top,
               b - a, plan_width_m=plate_width),
        member("post-centre", "stud", el.centre_post, at(layout.length / 2.0),
               at(layout.length / 2.0), base + layout.plate, top - layout.plate,
               layout.height, orient=(ux, uy)),
    ]
    face = cross_section(el.slat).width_m or 0.0
    z_sill = base + layout.plate
    offset = el.plane_offset.meters
    for s in layout.slats:
        half = face * math.hypot(1.0, s.slope) / 2.0
        profile = clipped_slat_profile(s, layout, face)
        u0, u1 = min(u for u, _ in profile), max(u for u, _ in profile)
        z_lo, z_hi = z_sill + s.elevation(u0), z_sill + s.elevation(u1)
        members.append(member(
            f"slat-{s.bay}{s.j:+d}", "brace", el.slat,
            at(layout.station(s.bay, u0), offset), at(layout.station(s.bay, u1), offset),
            max(z_sill, z_lo - half), min(z_sill + layout.height, z_lo + half), s.length,
            z0_end_m=max(z_sill, z_hi - half),
            z1_end_m=min(z_sill + layout.height, z_hi + half),
            elevation_profile=tuple((u - u0, z_sill + z) for u, z in profile),
            cut_length_m=slat_blank_length(profile, s.slope),
            plan_width_m=cross_section(el.slat).depth_m,
            connection=(f"kneebrace:{el.connector}" if s.braced
                        else f"screwed:{el.infill_fastener}")))
    model.braces.append(ResolvedBrace(uid=uid, tag=el.tag, storey=storey,
                                      members=tuple(members)))
    from typehaus.resolve.slat_connectors import resolve_slat_connectors

    resolve_slat_connectors(model, el, layout, storey)
    return []
