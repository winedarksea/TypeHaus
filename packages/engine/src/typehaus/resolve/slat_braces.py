"""Resolve a :class:`~typehaus.model.braces.SlatBrace`: the band frame and its 45° slats.

``slat_layout`` is the ONE rule for which slats there are and where they land; the resolver,
the dead load (``resolve/assembly_weight``) and the engineering (``engineering/
lateral_band_slats``) all read it. Oracle: ``houses/catlin/notes/canopy_west_band.md`` §3a.

Each bay has its own frame: ``u`` runs from the chord face toward the centre post, ``z`` up
from the sill's top. A slat's centreline is ``z = u - c``, so every slat rises toward the
centre, and ``c_j = (W - H)/2 + j * pitch`` centres the set on the bay.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.findings import Finding, element_error
from typehaus.model.braces import SlatBrace
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section
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

    @property
    def length(self) -> float:
        return (self.u1 - self.u0) * _ROOT2


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

    def crossing_mid(self, index: int) -> int:
        """Slats crossing mid-band in one bay. The verticals' shear is zero there."""
        z = self.height / 2.0
        return sum(1 for s in self.bay(index) if s.u0 <= s.c + z <= s.u1)

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
    pitch = (face + el.clear_gap.meters) * _ROOT2
    c_mid = (width - height) / 2.0
    reach = int((width + height) / pitch) + 1
    slats = []
    for bay in (0, 1):
        for j in range(-reach, reach + 1):
            c = c_mid + j * pitch
            u0, u1 = max(0.0, c), min(width, height + c)
            if u1 <= u0 or (u1 - u0) * _ROOT2 < el.min_slat_length.meters - 1e-9:
                continue
            slats.append(Slat(bay, j, c, u0, u1, "sill" if c > 0.0 else "chord",
                              "centre" if height + c > width else "top"))
    return SlatLayout(length, chord_face, centre_half, plate, width, height, pitch,
                      tuple(slats))


def resolve_slat_brace(model: ResolvedModel, el: SlatBrace, storey: str) -> list[Finding]:
    """The sill, the top plate, the centre post and the slats, on one ``ResolvedBrace``.

    Each board is clipped to the bay faces, including its long points at a frame corner.
    Engineering uses its centreline; lumber nesting uses the blank spanning its miters.
    """
    layout = slat_layout(el)
    if layout is None:
        return [element_error("integrity.slat_brace", "the frame leaves no bay between the "
                              "chords, plates and centre post", el.tag)]
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
    half = face / _ROOT2  # half the slat's vertical extent at 45°
    z_sill = base + layout.plate
    offset = el.plane_offset.meters
    for s in layout.slats:
        profile = clipped_slat_profile(s, layout, face)
        u0, u1 = min(u for u, _ in profile), max(u for u, _ in profile)
        z_lo, z_hi = z_sill + (u0 - s.c), z_sill + (u1 - s.c)
        members.append(member(
            f"slat-{s.bay}{s.j:+d}", "brace", el.slat,
            at(layout.station(s.bay, u0), offset), at(layout.station(s.bay, u1), offset),
            max(z_sill, z_lo - half), min(z_sill + layout.height, z_lo + half), s.length,
            z0_end_m=max(z_sill, z_hi - half),
            z1_end_m=min(z_sill + layout.height, z_hi + half),
            elevation_profile=tuple((u - u0, z_sill + z) for u, z in profile),
            cut_length_m=slat_blank_length(profile),
            plan_width_m=cross_section(el.slat).depth_m, connection=f"kneebrace:{el.connector}"))
    model.braces.append(ResolvedBrace(uid=uid, tag=el.tag, storey=storey,
                                      members=tuple(members)))
    from typehaus.resolve.slat_connectors import resolve_slat_connectors

    resolve_slat_connectors(model, el, layout, storey)
    return []
