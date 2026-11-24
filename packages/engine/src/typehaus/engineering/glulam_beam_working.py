"""The working for ``glulam_beam``'s four NDS rows, and its sheet declaration.

Split out to keep ``glulam_beam`` under 500 lines; the numbers are the ones ``nds_states``
builds the states from (review E-02).
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, Step, num

#: ASD: the deck's occupancy live load at C_D 1.0; deflection on live alone.
D_PLUS_L = ("D + L (planter as dead), unfactored (ASD), C_D 1.0", (("D", 1.0), ("L", 1.0)))
L_ALONE = ("L alone (IRC Table R301.7 limits live-load deflection)", (("L", 1.0),))


def nds_working(*, b: float, d: float, a: float, s: float, c: float, trib: float,
                live: float, dead: float, planter: float, cd: float, cv: float, cb: float,
                seat: float, env: Any, sm: float, ei: float, where: str, defl: float,
                span_in: float, limit_in: float, fb: float, fv: float, fcp: float
                ) -> tuple[tuple[Step, ...], ...]:
    from typehaus.engineering.glulam_beam import (
        GLULAM_FB_PSI,
        GLULAM_FC_PERP_PSI,
        GLULAM_FV_PSI,
        LIVE_DEFLECTION_DENOMINATOR,
        WET_FB,
        WET_FC_PERP,
        WET_FV,
    )

    w_d, w_l = dead * trib, live * trib
    loads = (Step("w_D", "deck dead line load", w_d, "plf", "q_D t", f"{num(dead)} x {num(trib)}"),
             Step("w_L", "deck live line load", w_l, "plf", "q_L t", f"{num(live)} x {num(trib)}"),
             *((Step("w_P", "planter dead load on the back span", planter, "plf",
                     source="preferences.toml [structural] balcony_planter"),) if planter else ()))
    patterns = (f"w_D (+ w_P on s) everywhere, w_L on each of the 8 subsets; a {num(a)}, "
                f"s {num(s)}, c {num(c)} ft")
    statics = "statics, ASCE 7-16 §4.3.3 partial loading"
    m, v, r = env.moment_lb_ft, env.shear_at_d_lb, max(env.reactions_lb)
    table = "NDS Supplement Table 5A 24F-V5M1/SP; Table 5.3.1 wet"
    bending = (*loads,
               Step("M", "largest bending moment over the patterns", m, "lb-ft", "max |M(x)|",
                    patterns, statics),
               Step("S", "section modulus", sm, "in^3", "b d^2 / 6", f"{num(b)} x {num(d)}^2 / 6"),
               Step("f_b", "bending stress", m * 12.0 / sm, "psi", "12 M / S",
                    f"12 x {num(m)} / {num(sm)}"),
               Step("C_V", "volume factor (joists brace the top edge, so C_L = 1)", cv, "",
                    "(21/s)^0.05 (12/d)^0.05 (5.125/b)^0.05 <= 1",
                    f"(21/{num(s)})^0.05 x (12/{num(d)})^0.05 x (5.125/{num(b)})^0.05",
                    "NDS §5.3.6, x = 20"),
               Step("F_b'", "allowable bending stress", fb, "psi", "F_b C_M C_D C_V",
                    f"{num(GLULAM_FB_PSI)} x {WET_FB} x {num(cd)} x {num(cv)}", table))
    shear = (*loads,
             Step("V", "largest shear at d from the seat face", v, "lb",
                  "max |V(x)|, x = d + seat / 2 from the bearing centre", patterns,
                  "statics; NDS §3.4.3.1(a)"),
             Step("f_v", "shear stress", 1.5 * v / (b * d), "psi", "1.5 V / (b d)",
                  f"1.5 x {num(v)} / ({num(b)} x {num(d)})"),
             Step("F_v'", "allowable shear stress", fv, "psi", "F_v C_M C_D",
                  f"{num(GLULAM_FV_PSI)} x {WET_FV} x {num(cd)}", table))
    bearing = (*loads,
               Step("R", "larger column reaction over the patterns", r, "lb", "max R1, R2",
                    patterns, statics),
               Step("f_c,perp", "bearing stress on the seat", r / (b * seat), "psi",
                    "R / (b l_b)", f"{num(r)} / ({num(b)} x {num(seat)})"),
               Step("C_b", "bearing area factor", cb, "", "(l_b + 0.375) / l_b",
                    f"({num(seat)} + 0.375) / {num(seat)}" if cb != 1.0 else "not claimed",
                    "NDS §3.10.4"),
               Step("F_c,perp'", "allowable bearing stress", fcp, "psi", "F_c,perp C_M C_b",
                    f"{num(GLULAM_FC_PERP_PSI)} x {WET_FC_PERP} x {num(cb)}", table))
    deflection = (loads[1],
                  Step("E'I", "stiffness", ei, "lb-in^2", "E C_M b d^3 / 12", source=table),
                  Step("delta", f"largest live-load deflection, at {where}",
                       defl, "in", "double integration of M / E'I",
                       "w_L on each subset of a, s, c", "statics"),
                  Step("delta_allow", "allowable deflection", limit_in, "in", "L / 360",
                       f"{num(span_in)} / {num(LIVE_DEFLECTION_DENOMINATOR)}",
                       "IRC Table R301.7 (a cantilever's L is twice its length, note b)"))
    return bending, shear, bearing, deflection


def figure(record: EngineeringRecord) -> Figure | None:
    from typehaus.engineering.sketch import beam_on_two_posts

    s = record.value("span")
    if s is None:
        return None
    trib = record.value("tributary") or 0.0
    live, dead = record.value("live_load") or 0.0, record.value("dead_load") or 0.0
    planter = record.value("planter_line_load") or 0.0
    bearing = next((st for st in record.limit_states if st.working and st.name.startswith(
        "bearing")), None)
    r = next((step.value for step in (bearing.working if bearing else ())
              if step.symbol == "R"), None)
    load = f"w_D {num(dead * trib)} + w_L {num(live * trib)} plf" + (
        f"; planter {num(planter)} plf on s" if planter else "")
    rtext = f"up to {num(r)} lb" if r is not None else "see bearing"
    return beam_on_two_posts(
        title=f"{record.key} on its two columns", a_ft=record.value("overhang_start") or 0.0,
        s_ft=s, b_ft=record.value("overhang_end") or 0.0, load=load,
        reactions=(rtext, rtext),
        caption="Joists bear on the beam top; their reactions are taken as the line loads "
                "above. Live load is patterned segment by segment.")


LABELS = {
    "overhang_start": "overhang past the first post, a",
    "overhang_end": "overhang past the second post, b",
    "tributary": "deck width the beam carries (tributary width)",
    "live_load": "deck live load",
    "dead_load": "deck dead load",
    "Fb": "tabulated bending design value F_b",
    "Fv": "tabulated shear design value F_v",
    "Fc_perp": "tabulated compression perpendicular to grain F_c-perp (bearing)",
    "E": "tabulated modulus of elasticity E",
    "C_M_bending": "wet-service factor on F_b",
    "C_M_shear": "wet-service factor on F_v",
    "C_M_bearing": "wet-service factor on F_c-perp",
    "C_M_modulus": "wet-service factor on E",
    "C_D": "load-duration factor",
    "C_V": "volume factor, size effect on bending",
    "C_b": "bearing-area factor for a short seat (NDS 3.10.4)",
    "bearing_length": "length of the seat under the beam at each post",
    "planter_line_load": "planter load per foot over the span between the posts",
}

NOT_COVERED = (
    NotCovered("snow on the deck", "the Minnesota deck basis is adopted (owner's stated "
               "basis, section 6); no snow path is built", "the owner (stated basis)",
               "the owner's decision stands unless the basis is revisited"),
    NotCovered("lateral-torsional stability over the unbraced overhang",
               "C_L is not computed (no E_min is held); the assumptions give the margin "
               "the negative moment leaves", "the sealing engineer",
               "accepting the overhang's compression-edge bracing"),
    NotCovered("wind uplift of the sealed deck and the beam-to-column connection",
               "graded on column_head_joint", "the sealing engineer",
               "the column_head_joint sheet"),
    NotCovered("long-term (creep) deflection", "reported in the assumptions, not graded",
               "the sealing engineer", "accepting the reported creep figure"),
)
