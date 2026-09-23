"""Fenestration solar gain, hour by hour — and why the one-number version was wrong.

``typehaus/energy.py``'s header documents the precedent for this placement: ``checks/`` has
no leaf restriction, so a building-science analysis may import ``resolve``/``model``/
``quantities`` freely. ``_facade_for_wall`` lives here now rather than in ``wwr``, because the
window-to-wall check and the load are two consumers of one orientation question.

**What this replaces.** The block load's cooling term was::

    window_solar += area × shgc × ORIENTATION_WEIGHT[facade] × 164.0

with weights ``{N 0.25, E 0.70, S 1.00, W 0.85}``. Two errors, and they compound:

1. **The weights put south at the peak.** At 45 °N in July the clear-sky totals on a vertical
   surface at each orientation's *own* peak hour are N 54 / **E 230** / S 161 / **W 230**
   Btu/h·ft² — so south is about 0.70 of the peak and east and west *are* the peak. The
   weights have it nearly backwards.
2. **Every orientation peaks at once.** A single weighted sum charges the east glass its
   8 a.m. peak and the west glass its 4 p.m. peak in the same hour, which is not an hour that
   exists. The house's real peak is one hour of the day, and every facade contributes what it
   is actually getting *then*.

Together those overstated catlin's glass by about 1.6×, on a term that is four fifths of its
cooling load.

**What it is now.** The ASHRAE clear-sky model, evaluated at each solar hour from 08:00 to
20:00 on the cooling design date, with shading derived from whatever is actually overhead —
an eave, a deck, a balcony standing clear of the wall. The peak hour is selected across the
whole house, and the **AED excursion** (ACCA TRB 2003-001a) is added to it: a house whose
gain is concentrated in a few hours needs more capacity than its peak hour alone implies,
because the structure cannot store the swing.

Nothing here is a rule of thumb. The clear-sky constants are ASHRAE's published monthly A/B/C
values; the geometry is spherical trigonometry; the shading is the building's own roofs,
decks and slabs.
Oracled by ``houses/catlin/notes/solar_gain_basis.md``, reproduced by
``tests/test_energy_solar.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.model import ResolvedModel, ResolvedWall

# The four orientations, and the surface azimuth of each measured from SOUTH, positive west.
# A vertical surface faces outward, so a south-facing wall's surface azimuth is 0.
_SURFACE_AZIMUTH_DEG = {"S": 0.0, "W": 90.0, "N": 180.0, "E": -90.0}

# ASHRAE clear-sky model coefficients. ``A`` is the apparent extraterrestrial direct normal
# irradiance (Btu/h·ft²), ``B`` the atmospheric extinction coefficient, ``C`` the diffuse sky
# factor, all for the 21st of the month — the published table. Only the cooling design month
# is needed for a design-hour load; July is that month in the northern hemisphere and is the
# one the ASHRAE residential tables are drawn at.
_JULY_A = 346.1
_JULY_B = 0.207
_JULY_C = 0.136
# Solar declination on 21 July, degrees.
_JULY_DECLINATION_DEG = 20.6
# Ground reflectance. 0.2 is the ASHRAE default for ordinary ground (grass, gravel, asphalt);
# snow would be 0.7 and is not a cooling-season condition.
_GROUND_REFLECTANCE = 0.2

# The hours a cooling design day is evaluated over, in SOLAR time. Before 08:00 and after
# 20:00 the sun is low enough that neither the gain nor the coincident conduction load can
# be the day's peak, and the half-hour step is fine enough that the peak is not missed
# between samples (the flattest facade moves under 3% in half an hour near its own peak).
_FIRST_HOUR = 8.0
_LAST_HOUR = 20.0
_HOUR_STEP = 0.5

# ACCA TRB 2003-001a's Adequate Exposure Diversity threshold. A house whose fenestration gain
# is *diverse* — spread over the day, several orientations sharing it — rides its peak hour on
# the structure's own thermal mass. A house whose gain is concentrated cannot, and the
# excursion is the part of the peak the mass will not absorb: ``peak − 1.3 × average``, added
# only when positive.
_AED_DIVERSITY_FACTOR = 1.3

# Manual J residential internal gains, COOLING ONLY. Manual J credits no internal gain
# against a heating load and neither does this — a design heating hour is 4 a.m. in January
# with the house asleep and the appliances off, and crediting people against it is how a
# system ends up unable to recover from a setback.
_OCCUPANT_SENSIBLE_BTUH = 230.0
_OCCUPANT_LATENT_BTUH = 200.0
# Manual J's residential appliance allowance for a kitchen, sensible. The published range is
# 1,200-2,400 Btu/h; the low end is the ordinary case (the high end is a second oven or a
# commercial-style range) and a house that wants the high end should say so rather than have
# the engine assume it.
_APPLIANCE_SENSIBLE_BTUH = 1200.0


@dataclass(frozen=True)
class SolarResult:
    """One house's fenestration gain at its own peak hour, plus the AED excursion."""

    peak_hour: float
    peak_btu_per_hour: float
    average_btu_per_hour: float
    excursion_btu_per_hour: float
    #: Gain at the peak hour, by facade — the table a reviewer reads to see which glass is
    #: driving the number.
    by_facade: dict[str, float]
    #: Openings whose product states no SHGC, or whose wall has no derivable orientation.
    unknown_inputs: tuple[str, ...] = ()

    @property
    def design_btu_per_hour(self) -> float:
        return self.peak_btu_per_hour + self.excursion_btu_per_hour


def _facade_for_wall(wall: ResolvedWall, model: ResolvedModel) -> str:
    """Which of N/E/S/W this wall's exterior face looks at, in the project-north frame.

    Moved here from ``wwr.py``: the WWR check and the solar load are two consumers of one
    orientation question, and the load is now the one that cares which way the normal points
    rather than only which axis the wall runs along.
    """
    from typehaus.checks.building_science.wwr import _facade_for_wall as _wwr_facade

    return _wwr_facade(wall, model)


def solar_position(latitude_deg: float, solar_hour: float) -> tuple[float, float]:
    """``(altitude, azimuth-from-south)`` in radians for the cooling design date.

    ``sin β = cos L cos δ cos H + sin L sin δ`` and
    ``cos φ = (sin β sin L − sin δ) / (cos β cos L)``, signed by the hour angle so the
    morning sun is east of south. Standard spherical trigonometry, not a correlation.
    """
    latitude = math.radians(latitude_deg)
    declination = math.radians(_JULY_DECLINATION_DEG)
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))
    sin_altitude = (math.cos(latitude) * math.cos(declination) * math.cos(hour_angle)
                    + math.sin(latitude) * math.sin(declination))
    sin_altitude = max(-1.0, min(1.0, sin_altitude))
    altitude = math.asin(sin_altitude)
    cos_altitude = math.cos(altitude)
    if abs(cos_altitude) < 1e-9:
        return altitude, 0.0
    cos_azimuth = ((sin_altitude * math.sin(latitude) - math.sin(declination))
                   / (cos_altitude * math.cos(latitude)))
    cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
    azimuth = math.acos(cos_azimuth)
    return altitude, azimuth if solar_hour > 12.0 else -azimuth


def vertical_surface_irradiance(latitude_deg: float, solar_hour: float,
                                facade: str) -> tuple[float, float]:
    """``(total incident Btu/h·ft², wall-solar azimuth in radians)`` on a vertical surface.

    Direct + diffuse sky + ground-reflected, the three terms of the ASHRAE clear-sky model
    for a surface tilted 90°::

        E_b = A / exp(B / sin β)                 direct normal
        E_D = E_b cos θ,   cos θ = cos β cos γ   direct on the surface
        E_d = C E_b (1 + cos Σ)/2 = 0.5 C E_b    diffuse sky
        E_r = E_b (C + sin β) ρ (1 − cos Σ)/2    ground-reflected

    The wall-solar azimuth ``γ`` comes back with the total because the overhang shading needs
    it: a shadow line runs ``P tan β / cos γ`` down the glass, and that is not derivable from
    the irradiance alone.
    """
    altitude, azimuth = solar_position(latitude_deg, solar_hour)
    sin_altitude = math.sin(altitude)
    surface_azimuth = math.radians(_SURFACE_AZIMUTH_DEG.get(facade, 0.0))
    wall_solar_azimuth = azimuth - surface_azimuth
    if sin_altitude <= 0.01:
        return 0.0, wall_solar_azimuth
    direct_normal = _JULY_A / math.exp(_JULY_B / sin_altitude)
    cos_incidence = math.cos(altitude) * math.cos(wall_solar_azimuth)
    direct = direct_normal * cos_incidence if cos_incidence > 0 else 0.0
    diffuse = _JULY_C * direct_normal * 0.5
    reflected = direct_normal * (_JULY_C + sin_altitude) * _GROUND_REFLECTANCE * 0.5
    return direct + diffuse + reflected, wall_solar_azimuth


# How far out from a wall face to look for something overhead that shades it, and how wide
# the lateral band is taken. 40 ft reaches a detached porch or a neighbouring wing; the
# window's own width is the band, so a deck twenty feet along the same wall does not shade a
# window it stands nowhere near.
_SHADE_REACH_M = 40 * 0.3048


@dataclass(frozen=True)
class _ShadePlane:
    """A horizontal surface overhead that can shade a window, in that window's own frame.

    ``near_ft`` / ``far_ft`` are its edges measured out from the WALL FACE along the wall's
    outward normal. An eave has ``near_ft == 0``. catlin's sunken-garden balcony deck is
    2 3/4" clear of the main-floor south wall and reaches 9.9 ft out — a FLOOR doing an
    eave's job over a roof that projects nothing past that face, so a model that only
    understood eaves saw no shading at all on the largest piece of south glass in the
    house.
    """

    tag: str
    z_m: float
    near_ft: float
    far_ft: float


def shaded_band_m(plane: _ShadePlane, altitude: float,
                  wall_solar_azimuth: float) -> tuple[float, float]:
    """``(lower, upper)`` elevations of the shadow this plane casts on the wall, in metres.

    A horizontal plane blocks a band, not a half-space: its NEAR edge sets the top of the
    shadow and its FAR edge the bottom, because a ray grazing the near edge lands higher on
    the wall than one grazing the far edge. For an eave (``near_ft == 0``) the top of the band
    is the eave itself and the band degenerates to the classic ``P tan β / cos γ`` depth.

    ``tan β / cos γ`` is the vertical drop per foot of horizontal run, projected into the
    wall's own plane: the ``cos γ`` is what makes any overhead plane nearly useless on an
    east or west window — the sun is round the corner, ``γ`` approaches 90°, and the shadow
    runs away sideways rather than down.
    """
    cos_azimuth = math.cos(wall_solar_azimuth)
    if altitude <= 0 or cos_azimuth <= 1e-6:
        return 0.0, 0.0  # the sun is behind the wall; there is no direct beam to block
    drop_per_ft = math.tan(altitude) / cos_azimuth
    upper = plane.z_m - plane.near_ft * drop_per_ft * 0.3048
    lower = plane.z_m - plane.far_ft * drop_per_ft * 0.3048
    return lower, upper


def shaded_fraction(planes: tuple[_ShadePlane, ...], sill_m: float, head_m: float,
                    altitude: float, wall_solar_azimuth: float) -> float:
    """What share of the glass between ``sill_m`` and ``head_m`` is in shadow, 0..1.

    The union of the bands, not their sum: a porch roof and the deck above it overlap on the
    glass and shading the same inch twice is not more shade.

    **Only the DIRECT beam is shaded.** Diffuse sky and ground reflection still reach glass
    under an overhang, which is why a fully shaded south window is not a zero-gain one. That
    is conservative in one further respect the caller should know about: a plane overhead
    also blocks part of the sky the diffuse term integrates over, and this does not subtract
    that, so the gain is if anything slightly over-stated.
    """
    height = head_m - sill_m
    if height <= 0:
        return 0.0
    bands: list[tuple[float, float]] = []
    for plane in planes:
        lower, upper = shaded_band_m(plane, altitude, wall_solar_azimuth)
        lower = max(lower, sill_m)
        upper = min(upper, head_m)
        if upper > lower:
            bands.append((lower, upper))
    if not bands:
        return 0.0
    bands.sort()
    covered = 0.0
    current_lower, current_upper = bands[0]
    for lower, upper in bands[1:]:
        if lower > current_upper:
            covered += current_upper - current_lower
            current_lower, current_upper = lower, upper
        else:
            current_upper = max(current_upper, upper)
    covered += current_upper - current_lower
    return min(1.0, covered / height)


@dataclass(frozen=True)
class _Glazing:
    """One resolved opening reduced to what the solar walk needs."""

    tag: str
    facade: str
    area_ft2: float
    shgc: float
    sill_m: float
    head_m: float
    planes: tuple[_ShadePlane, ...]


def _face_point_and_normal(model: ResolvedModel, wall: ResolvedWall, opening):
    """``(plan point on the wall's exterior face at the opening, outward unit normal)``.

    The exterior face is the one ``envelope_geometry.both_faces_interior`` already found, so
    no new geometry is derived here; the probe line it hands back sits a fixed offset off
    that face and is pulled back onto it.
    """
    from shapely.geometry import Point

    from typehaus.checks.building_science.envelope_geometry import (
        _INTERIOR_PROBE_OFFSET_M,
        envelope_geometry,
    )

    probe = envelope_geometry(model).exterior_face_probe(wall)
    if probe is None:
        return None, None
    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if run <= 0:
        return None, None
    coords = list(probe.coords)
    mid_probe = ((coords[0][0] + coords[-1][0]) / 2, (coords[0][1] + coords[-1][1]) / 2)
    offset = (mid_probe[0] - (x0 + x1) / 2, mid_probe[1] - (y0 + y1) / 2)
    length = (offset[0] ** 2 + offset[1] ** 2) ** 0.5
    if length < 1e-9:
        return None, None
    outward = (offset[0] / length, offset[1] / length)
    station = min(1.0, max(0.0, opening.center_along_m / run))
    on_probe = (coords[0][0] + (coords[-1][0] - coords[0][0]) * station,
                coords[0][1] + (coords[-1][1] - coords[0][1]) * station)
    face = Point(on_probe[0] - outward[0] * _INTERIOR_PROBE_OFFSET_M,
                 on_probe[1] - outward[1] * _INTERIOR_PROBE_OFFSET_M)
    return face, outward


def _shade_planes(model: ResolvedModel, wall: ResolvedWall, opening,
                  head_m: float) -> tuple[_ShadePlane, ...]:
    """Every horizontal surface overhead that can shade this window, out to 40 ft.

    **Three sources, all derived, none authored.** A roof's resolved ``footprint`` already
    includes its own overhang (it is built from the bearing walls plus ``Roof.overhang``); a
    ``Slab`` off its storey datum is a deck; a ``FloorSystem``'s ``deck_outline`` is the
    surface people stand on. All three are plan polygons at a known elevation, and the
    shadow arithmetic does not care which kind of element cast it.

    Why it is not just the eave: catlin's ``D-M-BALC`` is shaded by the sunken-garden
    **balcony deck**, a ``FloorSystem`` reaching 9.9 ft out a metre above the door head,
    while ``RF-HOUSE`` — the only roof over that wall in plan — projects nothing past its
    face. An eave-only reading calls the largest piece of south glass in the house
    unshaded.
    """
    from shapely.geometry import LineString, Polygon

    face, outward = _face_point_and_normal(model, wall, opening)
    if face is None:
        return ()
    ray = LineString([(face.x, face.y),
                      (face.x + outward[0] * _SHADE_REACH_M,
                       face.y + outward[1] * _SHADE_REACH_M)])
    candidates: list[tuple[str, float, object, object]] = []
    for roof in model.roofs:
        if len(roof.footprint) >= 3:
            candidates.append((roof.tag, roof.eave_z_m, Polygon(roof.footprint), None))
    for solid in model.solids:
        if solid.category == "slab" and len(solid.outline) >= 3:
            candidates.append((solid.tag, solid.z1_m, Polygon(solid.outline), None))
    for floor in model.floors:
        if len(floor.deck_outline) >= 3:
            candidates.append((floor.tag, floor.deck_z1_m, Polygon(floor.deck_outline),
                               floor if floor.deck_plane is not None else None))
    planes: list[_ShadePlane] = []
    for tag, z_m, polygon, tilted in candidates:
        # Strictly above the window head, and not the deck the window's own storey sits on.
        if z_m <= head_m + 1e-6 or not polygon.is_valid:
            continue
        crossed = ray.intersection(polygon)
        if crossed.is_empty:
            continue
        # The near and far edges of what this plane covers, measured out along the normal.
        points = _line_points(crossed)
        distances = [((x - face.x) ** 2 + (y - face.y) ** 2) ** 0.5 / 0.3048
                     for x, y in points]
        if not distances:
            continue
        if tilted is not None:  # the OUTER edge casts the shadow line, so read it there
            z_m = tilted.deck_top_at(*points[distances.index(max(distances))])
        planes.append(_ShadePlane(tag, z_m, min(distances), max(distances)))
    return tuple(planes)


def _line_points(geometry) -> list[tuple[float, float]]:
    parts = getattr(geometry, "geoms", None)
    if parts is not None:
        return [point for part in parts for point in _line_points(part)]
    coords = getattr(geometry, "coords", None)
    return list(coords) if coords is not None else []


def _glazing(model: ResolvedModel, walls: dict[str, ResolvedWall],
             openings, unknown: list[str]) -> list[_Glazing]:
    window_types = {item.tag: item for item in model.plan.library.window_types}
    door_types = {item.tag: item for item in model.plan.library.door_types}
    out: list[_Glazing] = []
    for opening in openings:
        if opening.penetration_for:
            continue  # a duct/pipe hole is not fenestration; there is no glass
        if opening.is_blind:
            # A BLIND recess (``RoughOpening.depth``) does not reach the outside at all —
            # the sheathing, the foam and the cladding run past it unbroken — so it admits
            # no gain and owes no SHGC. Reported as an UNKNOWN it read as "catlin has a
            # window nobody has specified the glass of", which is the opposite of true: it
            # is a firebox pocket behind a brick breast.
            continue
        wall = walls.get(opening.host_wall)
        if wall is None:
            continue
        product = (door_types if opening.is_door else window_types).get(opening.type_ref)
        # A glazed door is fenestration under R202 and admits gain exactly as a window does;
        # an opaque leaf transmits none and earns neither a term nor an UNKNOWN.
        if opening.is_door and not bool(getattr(product, "glazed", False)):
            continue
        if product is None or product.shgc is None:
            unknown.append(f"{'door' if opening.is_door else 'window'} "
                           f"{opening.tag} SHGC")
            continue
        sill_m = wall.base_ref_z_m + opening.sill_m
        head_m = sill_m + opening.height_m
        out.append(_Glazing(
            tag=opening.tag, facade=_facade_for_wall(wall, model),
            area_ft2=opening.width_m * opening.height_m * 10.7639104167,
            shgc=product.shgc, sill_m=sill_m, head_m=head_m,
            planes=_shade_planes(model, wall, opening, head_m)))
    return out


def fenestration_gain(model: ResolvedModel, walls: dict[str, ResolvedWall],
                      openings) -> SolarResult:
    """The house's fenestration gain at its own peak hour, plus the AED excursion.

    One peak hour for the WHOLE house, which is the correction that matters most: the term it
    replaced charged every orientation its own peak simultaneously, an hour that does not
    exist.
    """
    unknown: list[str] = []
    glazing = _glazing(model, walls, openings, unknown)
    latitude = model.plan.project.site.lat
    hours: list[tuple[float, float, dict[str, float]]] = []
    hour = _FIRST_HOUR
    while hour <= _LAST_HOUR + 1e-9:
        altitude, _ = solar_position(latitude, hour)
        by_facade: dict[str, float] = {}
        for glass in glazing:
            incident, wall_solar_azimuth = vertical_surface_irradiance(
                latitude, hour, glass.facade)
            if incident <= 0:
                continue
            shaded = shaded_fraction(glass.planes, glass.sill_m, glass.head_m,
                                     altitude, wall_solar_azimuth)
            # Shading removes the DIRECT share of the total, so the split is needed here;
            # ``vertical_surface_irradiance`` returns the sum because that is what every
            # other consumer wants.
            direct = _direct_on_surface(altitude, wall_solar_azimuth)
            effective = incident - direct * shaded
            by_facade[glass.facade] = by_facade.get(glass.facade, 0.0) + (
                glass.area_ft2 * glass.shgc * effective)
        hours.append((hour, sum(by_facade.values()), by_facade))
        hour += _HOUR_STEP
    if not hours:
        return SolarResult(0.0, 0.0, 0.0, 0.0, {}, tuple(dict.fromkeys(unknown)))
    peak_hour, peak, by_facade = max(hours, key=lambda row: row[1])
    average = sum(row[1] for row in hours) / len(hours)
    excursion = max(0.0, peak - _AED_DIVERSITY_FACTOR * average)
    return SolarResult(peak_hour, peak, average, excursion, by_facade,
                       tuple(dict.fromkeys(unknown)))


def _direct_on_surface(altitude: float, wall_solar_azimuth: float) -> float:
    """The direct-beam share of a vertical surface's incident total, Btu/h·ft²."""
    sin_altitude = math.sin(altitude)
    if sin_altitude <= 0.01:
        return 0.0
    cos_incidence = math.cos(altitude) * math.cos(wall_solar_azimuth)
    if cos_incidence <= 0:
        return 0.0
    return (_JULY_A / math.exp(_JULY_B / sin_altitude)) * cos_incidence


@dataclass(frozen=True)
class InternalGains:
    """Manual J residential internal gains — **cooling only**."""

    occupants: int
    sensible_btu_per_hour: float
    latent_btu_per_hour: float


def internal_gains(model: ResolvedModel) -> InternalGains:
    """Manual J's occupant and appliance allowance, from the room list.

    Occupants = **bedrooms + 1**, which is Manual J's own rule and is a fact the model
    already carries (``Room.occupancy == BEDROOM``) rather than an authored guess. A house
    with rooms but no bedroom modelled gets one occupant, not zero — somebody lives there.

    A model with **no conditioned room at all** gets none, and that is a different answer
    from "no bedroom": ``houses/empty`` is a plan frame with no building in it, and giving
    it an occupant puts 1,430 Btu/h of cooling load on a house that does not exist.
    """
    conditioned = [room for room in model.rooms if room.conditioned]
    if not conditioned:
        return InternalGains(0, 0.0, 0.0)
    bedrooms = sum(1 for room in conditioned if room.occupancy == "bedroom")
    occupants = bedrooms + 1
    return InternalGains(
        occupants=occupants,
        sensible_btu_per_hour=occupants * _OCCUPANT_SENSIBLE_BTUH + _APPLIANCE_SENSIBLE_BTUH,
        latent_btu_per_hour=occupants * _OCCUPANT_LATENT_BTUH)


# --- the roof's sol-air term ---------------------------------------------------------------

# Outside surface conductance for a horizontal surface in summer design conditions,
# Btu/h·ft²·°F (ASHRAE Fundamentals, Ch. 26 Table 10 — the 7.5 mph summer film).
_OUTSIDE_FILM_CONDUCTANCE = 4.0
# The long-wave radiation correction ``ε ΔR / h_o``, °F. A horizontal surface sees the whole
# cold sky and loses to it; ASHRAE gives 7 °F for a horizontal surface and 0 for a vertical
# one, which is why this term appears on the roof and on nothing else here.
_HORIZONTAL_LONGWAVE_CORRECTION_F = 7.0


def horizontal_surface_irradiance(latitude_deg: float, solar_hour: float) -> float:
    """Total clear-sky irradiance on a HORIZONTAL surface, Btu/h·ft².

    Direct (``E_b sin β``) plus the whole sky's diffuse (``C E_b``, undiminished — a
    horizontal surface sees all of it) and no ground reflection, because a roof sees no
    ground.
    """
    altitude, _ = solar_position(latitude_deg, solar_hour)
    sin_altitude = math.sin(altitude)
    if sin_altitude <= 0.01:
        return 0.0
    direct_normal = _JULY_A / math.exp(_JULY_B / sin_altitude)
    return direct_normal * sin_altitude + _JULY_C * direct_normal


def sol_air_temperature_f(outdoor_db_f: float, absorptance: float,
                          irradiance_btuh_ft2: float) -> float:
    """``T_out + α I / h_o − ε ΔR / h_o`` — the temperature a roof behaves as if it faced.

    A roof is solar-dominated and nearly ΔT-independent: catlin's raw cooling ΔT is 15 °F
    and its roof's sol-air excess is several times that, so charging the roof a wall's ΔT
    understates it badly. This is the **instantaneous** sol-air temperature with **no mass
    lag**, which is an upper bound: a real roof's peak flux arrives later and damped by the
    assembly's own heat capacity. The bound is the conservative direction for a cooling
    term and it is stated rather than corrected, because the decrement factor that would
    correct it is a table this engine does not have and would be inventing.
    """
    return (outdoor_db_f
            + absorptance * irradiance_btuh_ft2 / _OUTSIDE_FILM_CONDUCTANCE
            - _HORIZONTAL_LONGWAVE_CORRECTION_F)


def roof_absorptance(model: ResolvedModel, assembly_tag: str) -> float | None:
    """The ``solar_absorptance`` of the outermost layer of this roof assembly, or ``None``.

    The outermost layer is what the sun hits, so it is the only one whose optics matter —
    the membrane under a standing seam is in the dark. ``None`` where that material states
    none, which is the ordinary case today and is reported rather than assumed.
    """
    assembly = model.plan.library.resolve_assembly(assembly_tag)
    if assembly is None:
        return None
    materials = {item.tag: item for item in model.plan.library.materials}
    for layer in reversed(assembly.layers):
        material = materials.get(layer.material_ref)
        if material is not None and material.solar_absorptance is not None:
            return material.solar_absorptance
    return None
