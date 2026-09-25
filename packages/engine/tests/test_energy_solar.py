"""Fenestration solar gain, against ``houses/catlin/notes/solar_gain_basis.md``.

Section by section:

* **§1** — solar position and the ASHRAE clear-sky irradiance on a vertical surface. The
  four own-peak figures at 45 °N in July are what condemn the orientation weights the block
  load used: south is 0.70 of the peak, and east and west ARE the peak.
* **§2** — one peak hour for the whole house. A weighted sum charged the east glass its
  8 a.m. peak and the west glass its 4 p.m. peak in the same hour, an hour that does not
  exist.
* **§3** — shading from whatever is actually overhead. Not just an eave: catlin's balcony
  door is shaded by a FLOOR — the sunken-garden balcony deck — over a roof that projects
  nothing past that face.
* **§4** — the AED excursion (ACCA TRB 2003-001a).
* **§5** — internal gains, cooling only, and the latent split.
* **§6** — the roof's sol-air excess, off the panel's published solar reflectance.
"""

from __future__ import annotations

import math

import pytest

from typehaus.checks.building_science.energy_scope import _storey_is_conditioned
from typehaus.checks.building_science.solar import (
    _AED_DIVERSITY_FACTOR,
    _APPLIANCE_SENSIBLE_BTUH,
    _OCCUPANT_LATENT_BTUH,
    _OCCUPANT_SENSIBLE_BTUH,
    _ShadePlane,
    fenestration_gain,
    horizontal_surface_irradiance,
    internal_gains,
    roof_absorptance,
    shaded_band_m,
    shaded_fraction,
    sol_air_temperature_f,
    solar_position,
    vertical_surface_irradiance,
)
from typehaus.resolve.envelope_geometry import envelope_geometry

_LATITUDE = 44.9778  # catlin's, to four places, off ``plan/site.py``

# §1's table: the clear-sky total on a vertical surface at each orientation's OWN peak hour.
# These are the numbers the retired weights {N 0.25, E 0.70, S 1.00, W 0.85} get wrong.
_OWN_PEAK = {"N": (53.5, 18.0), "E": (230.1, 8.0), "S": (161.4, 12.0), "W": (230.1, 16.0)}


def _house_glazing(model):
    geometry = envelope_geometry(model)
    conditioned = {storey.tag for storey in model.plan.storeys
                   if _storey_is_conditioned(model.plan, storey.tag)}
    walls = {wall.tag: wall for wall in model.walls
             if wall.storey in conditioned and geometry.is_envelope_wall(wall)}
    openings = [o for o in model.openings if o.host_wall in walls]
    return walls, openings


# --- §1. position and irradiance ------------------------------------------------------------

def test_solar_noon_puts_the_sun_due_south_at_its_highest() -> None:
    """The geometry sanity gate. Declination 20.6° on 21 July, so the noon altitude is
    ``90 − L + δ`` and the azimuth is 0 (due south). Fails on a sign error in the hour
    angle, which is the easiest thing to get wrong here."""
    altitude, azimuth = solar_position(_LATITUDE, 12.0)
    assert math.degrees(altitude) == pytest.approx(90 - _LATITUDE + 20.6, abs=0.05)
    assert azimuth == pytest.approx(0.0, abs=1e-6)
    morning = solar_position(_LATITUDE, 9.0)[1]
    afternoon = solar_position(_LATITUDE, 15.0)[1]
    assert morning < 0 < afternoon  # east of south in the morning


def test_the_orientation_weights_the_block_load_used_are_nearly_backwards() -> None:
    """§1, and the whole reason the weighted sum had to go.

    The retired weights put SOUTH at 1.00 and east at 0.70. At this latitude in July, east
    and west reach 230 Btu/h·ft² at their own peaks and south reaches 161 — so south is 0.70
    of the peak and east is 1.00. Fails if anyone restores a weight table.
    """
    for facade, (expected, hour) in _OWN_PEAK.items():
        assert vertical_surface_irradiance(_LATITUDE, hour, facade)[0] == pytest.approx(
            expected, abs=0.5), facade
    south = _OWN_PEAK["S"][0]
    east = _OWN_PEAK["E"][0]
    assert south / east == pytest.approx(0.70, abs=0.01)


def test_a_north_wall_still_gets_diffuse_and_reflected_light() -> None:
    """A north window is not a hole with no gain: it takes sky diffuse and ground bounce all
    day, and direct sun early and late in summer when the azimuth swings past 90°. Fails if
    the direct term is ever allowed to go negative and eat the other two."""
    at_noon = vertical_surface_irradiance(_LATITUDE, 12.0, "N")[0]
    assert at_noon > 0
    assert at_noon < _OWN_PEAK["S"][0] / 2


def test_before_sunrise_nothing_is_incident_anywhere() -> None:
    for facade in "NESW":
        assert vertical_surface_irradiance(_LATITUDE, 4.0, facade)[0] == 0.0


# --- §2. one peak hour for the whole house --------------------------------------------------

def test_the_house_has_one_peak_hour_not_four(catlin_model_ro) -> None:
    """§2. The gain is evaluated at every half hour and the largest total wins ONCE.

    The test is that the answer is strictly less than the sum of the four facades' own
    peaks, which is what the weighted sum computed. It cannot be equal: the east glass's
    peak is at 08:00 and the west's at 16:00.
    """
    walls, openings = _house_glazing(catlin_model_ro)
    result = fenestration_gain(catlin_model_ro, walls, openings)
    assert result.peak_hour == pytest.approx(10.5)
    assert result.peak_btu_per_hour == pytest.approx(12_154.0, rel=0.01)
    assert result.unknown_inputs == ()
    # Every facade contributes at the peak hour, and south leads it — but at 64% of the
    # total, not the 100% the weights implied by putting it at 1.00 alone.
    assert set(result.by_facade) == {"N", "E", "S", "W"}
    assert result.by_facade["S"] / result.peak_btu_per_hour == pytest.approx(0.64, abs=0.02)


def test_a_missing_shgc_is_named_not_assumed(catlin_model_ro) -> None:
    """A window with no SHGC is a gap in the glass spec, and the gap is the opening's tag —
    not a default SHGC, which would invent a product."""
    walls, openings = _house_glazing(catlin_model_ro)
    result = fenestration_gain(catlin_model_ro, walls, openings)
    assert result.unknown_inputs == (), "catlin's glass all states an SHGC"


# --- §3. shading -----------------------------------------------------------------------------

def test_an_eave_and_a_detached_balcony_shade_by_the_same_arithmetic() -> None:
    """§3. A horizontal plane blocks a BAND: its near edge sets the top of the shadow and
    its far edge the bottom. An eave is the degenerate case with ``near_ft == 0``.

    Fails if anyone reduces this to the eave-only ``P tan β / cos γ`` form, which finds no
    shading at all on catlin's main-floor south glass — the glass this house's own review
    records as fully shaded in June.
    """
    altitude = math.radians(60.0)
    eave = _ShadePlane("eave", z_m=3.0, near_ft=0.0, far_ft=2.0)
    lower, upper = shaded_band_m(eave, altitude, 0.0)
    assert upper == pytest.approx(3.0)  # an eave shades from itself down
    assert lower == pytest.approx(3.0 - 2.0 * math.tan(altitude) * 0.3048, abs=1e-6)

    # A balcony standing 3 ft clear shades a band that does NOT reach its own elevation.
    balcony = _ShadePlane("balcony", z_m=3.0, near_ft=3.0, far_ft=9.0)
    lower, upper = shaded_band_m(balcony, altitude, 0.0)
    assert upper < 3.0 - 1e-6
    assert lower < upper


def test_an_overhang_shades_a_high_sun_and_not_a_low_one() -> None:
    """The ``tan β`` term, and it is why a south overhang works and a west one does not.

    Depth is ``P tan β / cos γ`` — the profile angle. South glass at noon has a 63° sun
    nearly normal to the wall, so a 2 ft overhang drops 4 ft of shadow. West glass at 5 p.m.
    has a 25° sun, also nearly normal, and the same overhang drops under a foot; the sun
    walks in under it. The **orientation** decides whether shading is worth having, not the
    projection.
    """
    eave = _ShadePlane("eave", z_m=3.0, near_ft=0.0, far_ft=2.0)
    high = shaded_band_m(eave, math.radians(63.0), 0.0)
    low = shaded_band_m(eave, math.radians(25.0), 0.0)
    assert (high[1] - high[0]) > 3 * (low[1] - low[0])
    assert high[1] == pytest.approx(3.0)  # an eave shades from itself down
    # Sun behind the wall: no direct beam, so nothing to block.
    assert shaded_band_m(eave, math.radians(30.0), math.radians(100.0)) == (0.0, 0.0)


def test_overlapping_shadows_are_a_union_not_a_sum() -> None:
    """A porch roof and the deck above it overlap on the glass. Shading the same inch twice
    is not more shade, and a sum would run past 1.0 and turn the gain negative."""
    altitude = math.radians(60.0)
    planes = (_ShadePlane("a", z_m=3.0, near_ft=0.0, far_ft=6.0),
              _ShadePlane("b", z_m=3.0, near_ft=0.0, far_ft=6.0))
    one = shaded_fraction(planes[:1], 0.8, 2.0, altitude, 0.0)
    two = shaded_fraction(planes, 0.8, 2.0, altitude, 0.0)
    assert two == pytest.approx(one)
    assert 0.0 <= two <= 1.0


def test_catlins_balcony_door_is_shaded_by_the_balcony_and_the_window_beside_it_is_not(
        catlin_model_ro) -> None:
    """§3's specific case, and the one that made the general shading plane necessary.

    ``D-M-BALC`` — 33 sf of glazed door, the largest single piece of south glass in the
    house — is shaded by ``FS-SG-DECK``, the sunken-garden balcony deck: its near edge is
    2 3/4" clear of the wall face, its surface is 0.98 m above the door head, and it reaches
    9.9 ft out. **No roof projects past this face at all** (``RF-HOUSE`` covers the wall in
    plan with zero overhang here), so a model that only understood eaves found no shading on
    this door. The deck is not an eave and it is not on the roof; it is a floor.

    ``WIN-M-LIV-S1`` is in the same wall 10 ft east and is NOT shaded, because the balcony
    stops at x = 8.76 m and that window is at 9.75. Both halves are asserted: a shading
    model that shades everything on the south wall is as wrong as one that shades nothing.
    """
    from typehaus.checks.building_science.solar import _shade_planes

    def planes_over(tag: str):
        opening = next(o for o in catlin_model_ro.openings if o.tag == tag)
        wall = catlin_model_ro.wall(opening.host_wall)
        head_m = wall.base_ref_z_m + opening.sill_m + opening.height_m
        return _shade_planes(catlin_model_ro, wall, opening, head_m), head_m

    shaded, head_m = planes_over("D-M-BALC")
    assert "FS-SG-DECK" in {plane.tag for plane in shaded}
    balcony = next(plane for plane in shaded if plane.tag == "FS-SG-DECK")
    assert balcony.near_ft == pytest.approx(0.23, abs=0.05)
    assert balcony.far_ft == pytest.approx(9.9, abs=0.2)
    # 1.05 m until the balcony came down 3" (2026-09-23); a lower plane only shades more.
    assert balcony.z_m - head_m == pytest.approx(0.978, abs=0.02)
    # And the roof over it projects nothing, which is the point: the eave-only reading of
    # this door is "unshaded".
    roof = next(plane for plane in shaded if plane.tag == "RF-HOUSE")
    assert roof.far_ft == pytest.approx(0.0, abs=0.01)

    unshaded, _ = planes_over("WIN-M-LIV-S1")
    assert "FS-SG-DECK" not in {plane.tag for plane in unshaded}


# --- §4. the AED excursion -------------------------------------------------------------------

def test_the_aed_excursion_is_the_peak_over_a_diverse_day(catlin_model_ro) -> None:
    """§4. ACCA TRB 2003-001a: a house whose gain is spread over the day rides its peak on
    its own thermal mass; one whose gain is concentrated cannot. The excursion is
    ``peak − 1.3 × average``, added only when positive — so a house with good exposure
    diversity pays nothing and a glass wall facing one way pays a lot."""
    walls, openings = _house_glazing(catlin_model_ro)
    result = fenestration_gain(catlin_model_ro, walls, openings)
    assert result.excursion_btu_per_hour == pytest.approx(
        result.peak_btu_per_hour - _AED_DIVERSITY_FACTOR * result.average_btu_per_hour,
        abs=1.0)
    assert result.excursion_btu_per_hour == pytest.approx(866.0, rel=0.02)
    assert result.design_btu_per_hour == pytest.approx(
        result.peak_btu_per_hour + result.excursion_btu_per_hour)


# --- §5. internal gains and the latent split ------------------------------------------------

def test_occupants_are_bedrooms_plus_one(catlin_model_ro) -> None:
    """§5. Manual J's own rule, and a fact the model already carries. catlin has six
    conditioned bedrooms, so seven occupants."""
    gains = internal_gains(catlin_model_ro)
    bedrooms = sum(1 for room in catlin_model_ro.rooms
                   if room.conditioned and room.occupancy == "bedroom")
    assert gains.occupants == bedrooms + 1
    assert gains.sensible_btu_per_hour == pytest.approx(
        gains.occupants * _OCCUPANT_SENSIBLE_BTUH + _APPLIANCE_SENSIBLE_BTUH)
    assert gains.latent_btu_per_hour == pytest.approx(
        gains.occupants * _OCCUPANT_LATENT_BTUH)


def test_internal_gains_are_cooling_only(catlin_model_ro) -> None:
    """Manual J credits no internal gain against a heating load and neither does this: a
    design heating hour is 4 a.m. in January with the house asleep and the appliances off.
    Crediting people against it is how a system ends up unable to recover from a setback.

    Asserted structurally — the heating total must be the UA sum plus the two air-side terms
    and nothing else — because an internal-gain credit would be invisible in a total.
    """
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    report = estimate_block_load(catlin_model_ro, Preferences(
        ach50=1.0, window_u=0.25, infiltration_storeys=2.0))
    ua_only = sum(c.ua_btu_per_hour_f * (c.heating_delta_f or 0.0)
                  for c in report.components)
    assert report.heating_load_btu_per_hour == pytest.approx(
        ua_only + report.infiltration_btu_per_hour + report.ventilation_btu_per_hour)


def test_a_model_with_no_conditioned_room_has_no_occupants(catlin_model_ro) -> None:
    """Different from "no bedroom": a plan frame with no building in it houses nobody, and
    giving it an occupant puts 1,430 Btu/h of cooling on a house that does not exist."""
    import dataclasses

    empty = dataclasses.replace(catlin_model_ro, rooms=[])
    assert internal_gains(empty).occupants == 0
    assert internal_gains(empty).sensible_btu_per_hour == 0.0


# --- §6. the roof's sol-air excess -----------------------------------------------------------

def test_a_dark_roof_behaves_as_if_it_faced_a_much_hotter_day() -> None:
    """§6. ``T_sol-air = T_out + α I / h_o − ε ΔR / h_o``. A roof is solar-dominated and
    nearly ΔT-independent: at a 90 °F design day a black roof under 290 Btu/h·ft² behaves as
    if it faced 148 °F, so charging it the wall's 15 °F cooling ΔT understates it four-fold.
    """
    dark = sol_air_temperature_f(90.0, 0.90, 290.0)
    assert dark == pytest.approx(90.0 + 0.90 * 290.0 / 4.0 - 7.0, abs=0.01)
    assert dark - 75.0 > 4 * 15.0
    # A reflective roof is a different building. SR 0.73 (a real published metal-roofing
    # figure) is α 0.27, and the excess falls by two thirds.
    light = sol_air_temperature_f(90.0, 0.27, 290.0)
    assert (light - 75.0) < (dark - 75.0) / 2


def test_the_long_wave_correction_is_on_the_roof_and_nowhere_else() -> None:
    """A horizontal surface sees the whole cold sky and loses to it; ASHRAE gives 7 °F for
    horizontal and 0 for vertical, which is why nothing in the wall path carries it."""
    assert sol_air_temperature_f(90.0, 0.0, 0.0) == pytest.approx(83.0)


def test_the_horizontal_irradiance_sees_the_whole_sky_and_no_ground() -> None:
    """A roof takes the full sky diffuse (not the half a vertical surface sees) and no
    ground bounce at all. It peaks at solar noon, unlike every vertical surface but south."""
    noon = horizontal_surface_irradiance(_LATITUDE, 12.0)
    assert noon > _OWN_PEAK["E"][0]
    assert horizontal_surface_irradiance(_LATITUDE, 9.0) < noon
    assert horizontal_surface_irradiance(_LATITUDE, 15.0) < noon
    assert horizontal_surface_irradiance(_LATITUDE, 4.0) == 0.0


def test_catlins_roof_carries_a_sol_air_term_off_its_published_reflectance(
        catlin_model_ro) -> None:
    """§6, and it was OPEN until the owner stated the panel colour (2026-09-18).

    The roof is 24 ga PVDF standing seam in Metal Sales Linen White — a different profile
    from the walls' PBR panel, the same colour — so SR 0.73 and ``solar_absorptance`` 0.27.
    A light roof, and the term is still 329 Btu/h: the sol-air temperature at the peak hour
    is 101 °F against a 90 °F design day, a 26 °F CTD where the plain air ΔT is 15. At
    α 0.90 it would be 144 °F and a 69 °F CTD, five times the air ΔT.

    ``color`` could not have stood in for this: it is an sRGB presentation triple and says
    nothing about the near-infrared, where most of the energy is.
    """
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    assert roof_absorptance(catlin_model_ro, roof.assembly) == pytest.approx(0.27)
    report = estimate_block_load(catlin_model_ro, Preferences(
        ach50=1.0, window_u=0.25, infiltration_storeys=2.0))
    assert report.unknown_inputs == ()
    # The caveat is GONE now that the input exists — that is what a caveat is for.
    assert not any("solar_absorptance" in caveat for caveat in report.cooling_caveats)
    # The two remaining caveats are the latent ones, which no authored colour can close.
    assert all("latent" in caveat.lower() or "LATENT" in caveat
               for caveat in report.cooling_caveats)


def test_an_unstated_absorptance_is_a_CAVEAT_and_not_an_unknown_input(
        catlin_model_ro) -> None:
    """The distinction the report exists to make, exercised on a model whose roof states no
    absorptance.

    An *omitted refinement* must not take an equipment-sizing verdict to UNKNOWN, and an
    *assumed* absorptance would be the rule of thumb this package forbids. So the roof falls
    back to the plain air ΔT, ``unknown_inputs`` stays empty, and the omission rides in
    ``cooling_caveats`` where ``mep.cooling_capacity`` prints it.
    """
    import dataclasses

    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    library = catlin_model_ro.plan.library
    materials = tuple(
        item.model_copy(update={"solar_absorptance": None})
        if item.tag == "standing-seam-linen-white" else item
        for item in library.materials)
    plan = catlin_model_ro.plan.model_copy(update={
        "library": library.model_copy(update={"materials": materials})})
    model = dataclasses.replace(catlin_model_ro, plan=plan, _envelope_geometry=None)

    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    assert roof_absorptance(model, roof.assembly) is None
    report = estimate_block_load(model, Preferences(
        ach50=1.0, window_u=0.25, infiltration_storeys=2.0))
    assert report.unknown_inputs == ()
    assert any("solar_absorptance" in caveat and "RF-HOUSE" in caveat
               for caveat in report.cooling_caveats)
