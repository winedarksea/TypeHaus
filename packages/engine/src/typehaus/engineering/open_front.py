"""What an open-front deck owes past its joint — the chord force, the couple, the drift limit.

``diaphragm_delivery`` grades the joint's straps against the along-joint couple as a linear
distribution. That is one reading of the couple. SDPWS 4.2.5.2's own reading is a cantilever
diaphragm: the couple ``M`` is carried by the deck's two CHORDS, the members perpendicular to
the joint at its ends, as ``M / W'``, and the chords hand it across the joint through the end
straps. The receiving roof then carries the same ``M`` as a pair of opposite forces into its
two lines perpendicular to the joint. Until 2026-09-30 the record computed neither, said the
joint "closed" the couple, and never earned its N/A on the drift limit.

* **Chord force** ``M / W'`` in each chord, W' the chords' spacing, graded in the chord where
  it is a glulam (tension parallel to grain) and at the end strap, added linearly to that
  strap's share of the along-joint shear.
* **The couple into the receiving lines**: ``M / d`` on each far line, d their spacing, graded
  on the line's SURPLUS braced length at its authored row, on the along-joint case.
* **SDPWS 4.2.5.2's drift limit** is a SEISMIC provision (ASCE 7 story drift under seismic
  forces including torsion). It is NOT APPLICABLE only on positive evidence: the site's
  seismic design category, and only category A, which ASCE 7-16 §11.7 designs to §1.4 alone.

**Oracle.** ``houses/catlin/notes/canopy_west_band.md`` §6;
``tests/test_canopy_west_band_calcs.py``.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048


def _couple(rows: Any) -> float | None:
    return next((q.value for q in rows.inputs if q.name == "joint_couple_lb_ft"), None)


def open_front_rows(ctx: Any, rows: Any, element: Any, joints: list[Any], v_along: float,
                    along: str, far: list[tuple[Any, Any]], readings: dict) -> None:
    """Append the chord, couple and drift rows for an ``open_front`` delivery."""
    from typehaus.hardware.catalog import allowable_for_model

    couple = _couple(rows)
    if couple is None:
        return
    index = 0 if along == "x" else 1
    chords = [ctx.plan.by_tag(t) for t in element.diaphragm.collector_refs]
    stations = sorted(
        sum(ctx.plan.by_tag(getattr(c, n)).position.xy_m[index]
            for n in ("start_node", "end_node")) / 2.0 / _M_PER_FT
        for c in chords if c is not None)
    if len(stations) < 2:
        rows.missing.append("two chords across the joint (DiaphragmSpec.collector_refs): the "
                            "open front's couple is carried by them")
        return
    spacing = stations[-1] - stations[0]
    force = couple / spacing
    rows.inputs.append(Quantity("chord_force_open_front_lb", force, "lb", 1.0))
    for chord in chords:
        _chord_row(rows, chord, force, couple, spacing)
    ends = sorted(joints, key=lambda j: j.position.xy_m[index])
    allowable = allowable_for_model(ends[0].size or "")
    capacity = getattr(allowable, "uplift_lb", None)
    if capacity:
        share = v_along / len(joints)
        rows.states.append(LimitState(
            f"{ends[0].size} end straps, chord force + along share", force + share, capacity,
            "lb", f"the chord force {force:,.1f} lb crosses the joint through the end straps "
                  f"({ends[0].tag}, {ends[-1].tag}), added LINEARLY to each one's "
                  f"{share:,.1f} lb of along-joint shear"))
    _far_lines(ctx, rows, far, readings, couple, along)
    _drift(ctx, rows)


def _chord_row(rows: Any, chord: Any, force: float, couple: float, spacing: float) -> None:
    from typehaus.engineering.roof_beam_glulam import CM_FT, FT_PSI, glulam_section

    section = glulam_section(chord)
    if section is None:
        rows.notes.append(f"{chord.tag} carries a {force:,.1f} lb chord force and is not a "
                          f"glulam this engine holds a tension value for; not graded")
        return
    area = section[0] * section[1]
    rows.states.append(LimitState(
        f"{chord.tag} chord tension, open front", force / area, FT_PSI * CM_FT * 1.6, "psi",
        f"M / W' = {couple:,.1f} / {spacing:.3f}' = {force:,.1f} lb over {area:.1f} in2 — "
        f"AWC NDS 2018 Supplement Table 5A 24F-V4 DF Ft {FT_PSI:.0f} psi x wet C_M {CM_FT} "
        f"x C_D 1.6"))


def _far_lines(ctx: Any, rows: Any, far: list, readings: dict, couple: float,
               along: str) -> None:
    index = 0 if along == "x" else 1
    stations = []
    for wall, line in far:
        ends = [ctx.plan.by_tag(getattr(wall, n)) for n in ("start_node", "end_node")]
        stations.append((sum(e.position.xy_m[index] for e in ends) / 2.0 / _M_PER_FT,
                         wall, line))
    if len(stations) < 2:
        return
    stations.sort(key=lambda s: s[0])
    d = stations[-1][0] - stations[0][0]
    force = couple / d
    for _x, _wall, line in (stations[0], stations[-1]):
        reading = readings.get(line.wall)
        if reading is None:
            continue
        surplus = reading[1] - reading[2]
        rows.states.append(LimitState(
            f"{line.wall} joint couple, {'E-W' if along == 'x' else 'N-S'} case",
            force / surplus, line.unit_shear_asd_plf, "plf",
            f"{line.source}; M / d = {couple:,.1f} / {d:.3f}' = {force:,.1f} lb on the "
            f"{surplus:.3f}' surplus — the open front's couple, which the joint hands on "
            f"rather than closes"))


def _drift(ctx: Any, rows: Any) -> None:
    category = getattr(ctx, "seismic_design_category", None)
    if category == "A":
        rows.notes.append(
            "SDPWS 4.2.5.2 DRIFT LIMIT — NOT APPLICABLE, earned: the site is seismic design "
            "category A (the jurisdiction profile), ASCE 7-16 §11.7 designs an SDC A "
            "structure to §1.4 alone, and the open-front drift limit is ASCE 7's story drift "
            "under SEISMIC forces including torsion. The wind drift is not a code limit here.")
        return
    rows.missing.append(
        "the site's seismic design category: SDPWS 4.2.5.2 bounds an open front's drift under "
        f"seismic forces, and a {category or 'missing'} category does not earn its N/A")
