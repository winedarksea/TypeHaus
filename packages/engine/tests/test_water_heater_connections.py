"""EQ-B-WH's connections are PORTS now, and eight literals still have to find them.

``houses/catlin`` authors the water heater's coordinate once as ``Equipment.position``
(``plan/mep_hvac.py``) and then again, verbatim, as a path endpoint in every supply run that
leaves or arrives at the tank (``plan/mep_supply.py``) — seven of them — plus as the datum
for the T&P relief discharge (``plan/mep_drainage.py``). Those files are ``# haus: editable``,
whose dialect allows only literals: no shared constant can reach across them, and nothing in
the resolver pulls a pipe onto its equipment. So moving the tank without moving all of them
silently disconnects the hot trunk, the cold feed and five branches, and the model still
resolves, still builds, and still passes every MEP check — it just describes plumbing that
does not connect.

That is exactly what happened on 2026-08-23, when the tank moved from (6'-2 1/4", 32'-9 7/8")
to (5'-6", 24'-0") to clear ``EQ-B-ESS-BATT``'s REQUIRED separation zone. The move was fine;
the trap is real, and this file is the guard. It reads the RESOLVED model, not the source, so
it holds however the coordinate is spelled.

**What it grades changed on 2026-09-20, and the old question was too weak.** ``EQ-T-WATER-
HEATER`` used to state three ports at one local ``(0, 0)``, so the only thing a test could ask
was "is there a vertex on the footprint's centroid" — which a COLD run landing on the HOT tap
answers just as well as the right one, and which three pipes of two services drawn through a
single point answer best of all. The type now carries a dimensioned top pair (cold 4" west of
the axis, hot 4" east, both 3/4" NPT at the 5'-8" tank top), so the question this file asks is
the one that was always meant: **each run's tank end lands on the resolved port matching its
own service**, read through :func:`typehaus.resolve.mep_ports.placed_ports` — the same reading
``mep.equipment_port_service`` and the router's terminal snapping use.
"""

from __future__ import annotations

import pytest

#: Half an inch. A run end is ON a 3/4" stub or it is not; this is not a routing tolerance.
_TOLERANCE_M = 0.0127
# The T&P tap is deliberately NOT on the tank: it hangs 2" off the west face and drops a foot
# south. This is how far off-centre that puts it, and it is checked as a range rather than a
# point so the detail can be re-drawn without editing a test.
_TPR_MAX_OFFSET_M = 0.6096  # 2'-0" — anything further is not "beside the tank" any more

#: Every run that touches the tank, and WHICH TAP it has to touch. The point of the mapping
#: is the service column: a hot branch that drifts onto the cold stub is the failure this
#: file exists to catch, and the two are only 8" apart.
_RUNS_BY_PORT = {
    "hot": (
        "PR-B-HW-TRUNK",   # the hot trunk out of the tank
        "PR-B-HW-BATH1",
        "PR-B-HW-WASH",
        "PR-B-HW-SBATH",
        "PR-B-HW-BATH",
    ),
    "cold": (
        "PR-B-CW-WH",      # the cold feed into it
        "PR-B-CW-BATH",
    ),
}

#: The service each tap carries, so a port silently retyped fails here rather than passing
#: a positional test that no longer means anything.
_PORT_SERVICE = {"hot": "water_hot", "cold": "water_cold"}


def _centre(canvas_object) -> tuple[float, float]:
    xs = [p[0] for p in canvas_object.footprint]
    ys = [p[1] for p in canvas_object.footprint]
    return sum(xs) / len(xs), sum(ys) / len(ys)


@pytest.fixture(scope="module")
def water_heater(catlin_model):
    obj = next((o for o in catlin_model.canvas_objects if o.tag == "EQ-B-WH"), None)
    assert obj is not None, "EQ-B-WH did not resolve to a placed object"
    return obj


@pytest.fixture(scope="module")
def wh_ports(catlin_model):
    from typehaus.resolve.mep_ports import placed_ports

    ports = {p.port_tag: p for p in placed_ports(catlin_model)
             if p.equipment_tag == "EQ-B-WH"}
    assert {"cold", "hot"} <= set(ports), (
        "EQ-T-WATER-HEATER no longer declares a cold and a hot port: " + ", ".join(ports))
    return ports


def test_the_two_water_taps_are_dimensioned_and_exact(wh_ports) -> None:
    """An APPROXIMATE port cannot establish a connection, so nothing below would mean much.

    This is the precondition for every other assertion in the file: two distinct, EXACT,
    sized stations. Coincident ports are what this whole module was weakened by.
    """
    for tag, service in _PORT_SERVICE.items():
        port = wh_ports[tag]
        assert port.service == service, f"EQ-B-WH.{tag} carries {port.service}"
        assert port.exact, (
            f"EQ-B-WH.{tag} is APPROXIMATE — a run end cannot be graded against it")
        assert port.section_m is not None, f"EQ-B-WH.{tag} states no connection size"
    cold, hot = wh_ports["cold"], wh_ports["hot"]
    apart = ((cold.x_m - hot.x_m) ** 2 + (cold.y_m - hot.y_m) ** 2) ** 0.5
    assert apart > _TOLERANCE_M, (
        "EQ-B-WH's cold and hot taps are coincident again — every run below would pass "
        "against either of them")


@pytest.mark.parametrize("port_tag", sorted(_RUNS_BY_PORT))
def test_every_run_that_names_the_tank_lands_on_its_own_tap(catlin_model, wh_ports,
                                                            port_tag) -> None:
    """Each run below leaves or arrives at the tank; a vertex must sit ON the right port."""
    port = wh_ports[port_tag]
    other = wh_ports["cold" if port_tag == "hot" else "hot"]
    runs = {r.tag: r for r in catlin_model.pipe_runs}

    missing, wrong_tap = [], []
    for tag in _RUNS_BY_PORT[port_tag]:
        run = runs.get(tag)
        assert run is not None, f"{tag} is not in the resolved model at all"
        on_port = [i for i, (x, y) in enumerate(run.path)
                   if abs(x - port.x_m) <= _TOLERANCE_M
                   and abs(y - port.y_m) <= _TOLERANCE_M]
        if on_port:
            continue
        if any(abs(x - other.x_m) <= _TOLERANCE_M and abs(y - other.y_m) <= _TOLERANCE_M
               for x, y in run.path):
            wrong_tap.append(tag)
        else:
            missing.append(tag)

    assert not wrong_tap, (
        f"these runs land on EQ-B-WH's {other.port_tag} tap and carry {port.service}: "
        + ", ".join(sorted(wrong_tap)))
    assert not missing, (
        f"these runs no longer touch EQ-B-WH.{port_tag} — the tank or its port moved and "
        "they did not: " + ", ".join(sorted(missing)))


def test_the_two_runs_that_really_connect_land_at_the_tap_elevation(catlin_model,
                                                                    wh_ports) -> None:
    """The trunk and the feed END on the tank; the other five tee off above it.

    These are top connections, so the one vertex that is the connection sits at the port's
    own z. Before the ports were dimensioned both ran to a mid-tank 3'-9 7/16" — 22 1/2" of
    copper drawn down INSIDE the tank body, which nothing graded.
    """
    runs = {r.tag: r for r in catlin_model.pipe_runs}
    for tag, port_tag, index in (("PR-B-HW-TRUNK", "hot", 0), ("PR-B-CW-WH", "cold", -1)):
        run = runs[tag]
        port = wh_ports[port_tag]
        z = run.z_m[index] if getattr(run, "z_m", None) else run.z_start_m
        assert abs(z - port.z_m) <= _TOLERANCE_M, (
            f"{tag}'s tank end is at {z:.4f} m and EQ-B-WH.{port_tag} is at "
            f"{port.z_m:.4f} m — the connection is drawn inside or above the tank")


def test_the_relief_discharge_followed_the_tank(catlin_model, water_heater) -> None:
    """P2804.6.1's discharge is offset from the tank, so it is checked by proximity.

    It is measured from the tank CENTRE and not from a port on purpose: the T&P valve is
    factory-installed and the spec sheet (HP-400-SO REV. 1) gives no station for it, so
    ``EQ-T-WATER-HEATER`` declares no relief port to land on. This run is dimensioned off
    the tank's west FACE instead, which is the honest datum available.
    """
    tpr = next((r for r in catlin_model.pipe_runs if r.tag == "PR-B-WH-TPR"), None)
    assert tpr is not None, "EQ-B-WH names relief_discharge_ref=PR-B-WH-TPR; it is missing"
    tx, ty = _centre(water_heater)
    start = tpr.path[0]
    offset = ((start[0] - tx) ** 2 + (start[1] - ty) ** 2) ** 0.5
    assert offset <= _TPR_MAX_OFFSET_M, (
        f"PR-B-WH-TPR starts {offset:.3f} m from EQ-B-WH — the relief line did not follow "
        "the tank"
    )


def test_the_tank_stands_inside_the_room_it_claims(catlin_model, water_heater) -> None:
    """A placeable that drifts out of its room takes its clearances and loads with it."""
    from shapely.geometry import Polygon

    room = next((r for r in catlin_model.rooms if r.tag == "RM-B-FURNACE"), None)
    assert room is not None
    assert Polygon(room.clear_face).contains(Polygon(water_heater.footprint))


def test_both_taps_stand_over_the_tank(water_heater, wh_ports) -> None:
    """A derived offset that walks off the 24" top is a derivation that went wrong."""
    from shapely.geometry import Point, Polygon

    top = Polygon(water_heater.footprint)
    for tag in _PORT_SERVICE:
        port = wh_ports[tag]
        assert top.covers(Point(port.x_m, port.y_m)), (
            f"EQ-B-WH.{tag} is placed outside the tank's own footprint")
