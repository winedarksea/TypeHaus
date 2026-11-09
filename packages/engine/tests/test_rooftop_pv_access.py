"""R324.6 rooftop PV access, hand-worked on a synthetic gable (no house load).

Roof footprint 8 m (x) x 10 m (y), ridge x = 4, rise 2 m over 4 m (6:12 is 0.5; any slope
over 2:12 applies). Module: 1.0 m down-slope (plan) x 1.7 m along the ridge. Ten modules
(five a side) cover 10 x 1.7 = 17 m2 of 80 m2 = 21.25% -> the 18" (0.4572 m) setback.
PASS: 0.5 m clear of the ridge; rows y 0..8.5, leaving a 1.5 m (59") corridor at the north
end, where the street is. MISS: rows y 0.75..9.25 leave 0.75 m (29.5") at each end, and a
0.3 m (11.8") ridge clearance.
"""

from types import SimpleNamespace

from typehaus.checks.code.mn_residential.rooftop_pv_access import rooftop_pv_access
from typehaus.findings import Result
from typehaus.resolve.model import ResolvedRoof, ResolvedSolarPanel

ROOF = ResolvedRoof(
    uid="R", tag="RF-T", storey="s", form="gable",
    footprint=((0, 0), (8, 0), (8, 10), (0, 10)), eave_z_m=3.0, ridge_z_m=5.0,
    ridge_direction="y", assembly="A", surface_area_m2=0.0)


def _panels(ridge_gap: float, y_start: float):
    out = []
    for side, sign in (("W", -1), ("E", 1)):
        for i in range(5):
            x0, x1 = 4 + sign * ridge_gap, 4 + sign * (ridge_gap + 1.0)
            y0 = y_start + 1.7 * i
            ring = tuple((x, y, 4.0) for x, y in
                         ((x0, y0), (x0, y0 + 1.7), (x1, y0 + 1.7), (x1, y0)))
            out.append(ResolvedSolarPanel(
                uid=f"{side}{i}", tag=f"SP-{side}{i}", storey="s", roof_ref="RF-T",
                corners_bottom=ring, corners_top=ring, watts=440.0))
    return out


def _ctx(panels, with_street=True):
    parcel = tuple(SimpleNamespace(xy_m=p) for p in ((-5, -5), (13, -5), (13, 20), (-5, 20)))
    streets = (SimpleNamespace(edge=2),) if with_street else ()  # edge 2 = the y = 20 side
    site = SimpleNamespace(parcel=parcel, streets=streets)
    return SimpleNamespace(model=SimpleNamespace(roofs=[ROOF], solar_panels=panels),
                           plan=SimpleNamespace(project=SimpleNamespace(site=site)))


def test_compliant_layout_passes_every_requirement() -> None:
    results = [f.result for f in rooftop_pv_access(_ctx(_panels(0.5, 0.0)))]
    assert results == [Result.PASS] * 4  # two setbacks, pathways, street side


def test_centred_short_clearance_layout_misses_all_three_rules() -> None:
    findings = rooftop_pv_access(_ctx(_panels(0.3, 0.75)))
    assert [f.result for f in findings] == [Result.FAIL] * 4
    assert "11.8\" against 18\"" in findings[0].message
    assert "29.5\"" in findings[2].message


def test_street_unknown_is_reported_not_passed() -> None:
    findings = rooftop_pv_access(_ctx(_panels(0.5, 0.0), with_street=False))
    assert findings[-1].result is Result.UNKNOWN
