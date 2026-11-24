"""The working for ``deck_tie``'s rows: loads to a force and torque, shared over the joints,
then the governing joint against its published allowables (review E-02).

Split out of ``deck_tie`` (file size). The steps read the very :class:`Distribution` the
ratio was graded on, so the sheet and the number cannot differ.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.deck_tie_basis import Load, TieJoint
from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, Step, num

#: The combination each row carries: wind at the published value (ASD, the 0.6 in it), a
#: guard at 1.0 against the row's own C_D 1.0 value.
WIND_ASD = ("ASCE 7-16 §2.4.1(5) 0.6W", (("W", 0.6),))
GUARD_ASD = ("L: the 200 lb guard load, ASD, C_D 1.0", (("L", 1.0),))


@dataclass(frozen=True)
class Distribution:
    """One case shared over the joints: the resultants and each joint's force."""

    forces: list[tuple[float, float]]
    fx: float
    fy: float
    n_x: float      # joints that carry along x
    n_y: float      # joints that carry along y
    xr: float
    yr: float
    moment: float
    polar: float
    k_x: tuple[float, ...]
    k_y: tuple[float, ...]


@dataclass(frozen=True)
class Governing:
    """The joint, case and sense that governed a state, with the numbers it was graded on."""

    ratio: float
    joint: TieJoint
    along_cap: float
    across_cap: float
    how: str
    index: int
    dist: Distribution
    joints: tuple[TieJoint, ...]
    loads: tuple[Load, ...]
    sign: float
    along: float
    across: float
    divisor: float


def _sum(values: list[float]) -> str:
    return " + ".join(num(v) for v in values) or "0"


def panel_share_steps(load: Load) -> tuple[Step, ...]:
    """A roof's shear-panel share at the 100% delivered envelope, built up from the roof's
    wind: 0.6 q_h G C_f over its solid area, plus half the drag of each pinned post. Empty
    where the load is not that envelope (the frame split is on the roof sheets)."""
    from typehaus.engineering.roof_lateral import wind_of
    from typehaus.wind_tables import GUST_EFFECT_RIGID, MAX_VERIFIED_CASE_AB

    tag, _, roof = load.label.partition(" panel share of ")
    wind = wind_of(roof) if roof else None
    axis = "y" if load.fy else "x"
    force = load.fy or load.fx
    if wind is None or abs(wind.delivered_lb(axis) - force) > 1e-6 or not wind.top_area_sf:
        return ()
    area = wind.top_area_sf[axis]
    pin_terms = " + ".join(f"{num(wind.pressure_psf)} x {num(p.width_ft)} x "
                           f"{num(p.length_ft)} / 2" for p in wind.pinned) or "0"
    return (
        Step("q_h", f"velocity pressure at the top of {roof}", wind.q_h_psf, "psf",
             source=f"{wind.basis_text}, height {num(wind.height_ft)} ft above ground"),
        Step("p", "ASD wind pressure on a solid band", wind.pressure_psf, "psf",
             "0.6 q_h G C_f", f"0.6 x {num(wind.q_h_psf)} x {num(GUST_EFFECT_RIGID)} x "
             f"{num(MAX_VERIFIED_CASE_AB)}", "gust factor G 0.85, force coefficient C_f 1.80 "
             "(the Case A/B bound)"),
        Step("A_s", f"solid area {roof} presents along axis {axis}: its roof projection and "
             "the header members", area, "ft^2", source="the roof's slope band or gable "
             "triangle, plus each bearing member's own depth x length"),
        Step("F_roof", f"wind on {roof} at deck level along {axis}", wind.top_shear[axis],
             "lb", "p A_s", f"{num(wind.pressure_psf)} x {num(area)}"),
        Step("F_post", "half the drag of each pinned post under the roof beams, returned "
             "to the deck level", force - wind.top_shear[axis], "lb",
             "sum(p w h / 2)", pin_terms),
        Step("F_share", f"{tag}'s share of {roof}: the whole deck-level shear, 100%, since "
             "the roof delivers to a neighbour and no stiffness split is judged across the "
             "joint", force, "lb", "F_roof + F_post",
             f"{num(wind.top_shear[axis])} + {num(force - wind.top_shear[axis])}"))


def interaction_steps(g: Governing) -> tuple[Step, ...]:
    d, i = g.dist, g.index
    s = num(g.sign)
    xs = [j.x_ft for j, k in zip(g.joints, d.k_y, strict=True) if k]
    ys = [j.y_ft for j, k in zip(g.joints, d.k_x, strict=True) if k]
    moment_terms = " + ".join(
        f"({num(load.x_ft)} - {num(d.xr)}) x {num(load.fy)} - "
        f"({num(load.y_ft)} - {num(d.yr)}) x {num(load.fx)}" for load in g.loads)
    polar_terms = [f"({num(j.y_ft)} - {num(d.yr)})^2" for j, k in
                   zip(g.joints, d.k_x, strict=True) if k]
    polar_terms += [f"({num(j.x_ft)} - {num(d.xr)})^2" for j, k in
                    zip(g.joints, d.k_y, strict=True) if k]
    j = g.joints[i]
    a, b = d.k_x[i], d.k_y[i]
    shares = tuple(step for load in g.loads for step in panel_share_steps(load))
    steps = [
        *shares,
        Step("F_x", "total force on the tie line along plan x, all loads in this case",
             d.fx, "lb", "s sum(F_x,k)", f"{s} x ({_sum([ld.fx for ld in g.loads])})",
             "s = +1, or -1 for the reverse sense, whichever is worse"),
        Step("F_y", "total force along plan y", d.fy, "lb", "s sum(F_y,k)",
             f"{s} x ({_sum([ld.fy for ld in g.loads])})"),
        Step("x_r", "plan x of the centre of the joints that carry y-direction force",
             d.xr, "ft", "sum(x_j) / n_y", f"({_sum(xs)}) / {num(d.n_y)}"),
        Step("y_r", "plan y of the centre of the joints that carry x-direction force",
             d.yr, "ft", "sum(y_j) / n_x", f"({_sum(ys)}) / {num(d.n_x)}"),
        Step("M", "torque of the loads about that centre", d.moment, "lb-ft",
             "s sum[(x_k - x_r) F_y,k - (y_k - y_r) F_x,k]", f"{s} x [{moment_terms}]",
             "each load placed where it acts in plan"),
        Step("J", "polar sum of the joints about that centre", d.polar, "ft^2",
             "sum_x (y_j - y_r)^2 + sum_y (x_j - x_r)^2", " + ".join(polar_terms) or "0",
             "elastic method, every carrying joint equally stiff"),
        Step("X_i", f"force on the governing joint ({j.member} at {j.wall}) along x",
             d.forces[i][0], "lb", "k_x (F_x / n_x - M (y_i - y_r) / J)",
             f"{num(a)} x ({num(d.fx)} / {num(d.n_x)} - {num(d.moment)} x "
             f"({num(j.y_ft)} - {num(d.yr)}) / {num(d.polar)})"),
        Step("Y_i", "force on that joint along y", d.forces[i][1], "lb",
             "k_y (F_y / n_y + M (x_i - x_r) / J)",
             f"{num(b)} x ({num(d.fy)} / {num(d.n_y)} + {num(d.moment)} x "
             f"({num(j.x_ft)} - {num(d.xr)}) / {num(d.polar)})"),
        Step("F_along", f"magnitude of the force along the wall {j.wall}", g.along, "lb",
             "|X_i| if the wall runs along x, else |Y_i|"),
        Step("F_across", "magnitude of the force across that wall", g.across, "lb",
             "the other one"),
        Step("C_along", "allowable along the wall, from the part's published row"
             + (", over its C_D" if g.divisor != 1.0 else ""),
             g.along_cap / g.divisor, "lb",
             "C_pub / C_D" if g.divisor != 1.0 else "",
             f"{num(g.along_cap)} / {num(g.divisor)}" if g.divisor != 1.0 else "",
             f"{len(j.parts)} x {j.model}: {g.how}; 0 = the part carries nothing this way"),
        Step("C_across", "allowable across the wall", g.across_cap / g.divisor, "lb",
             "C_pub / C_D" if g.divisor != 1.0 else "",
             f"{num(g.across_cap)} / {num(g.divisor)}" if g.divisor != 1.0 else ""),
    ]
    terms = [(g.along, g.along_cap, "F_along / C_along"),
             (g.across, g.across_cap, "F_across / C_across")]
    on = [t for t in terms if t[1] > 0.0]
    numbers = " + ".join(f"{num(f)}" + (f" x {num(g.divisor)}" if g.divisor != 1.0 else "")
                         + f" / {num(c)}" for f, c, _ in on) or "0"
    steps += [
        Step("I", "interaction: the force each way over its allowable, added",
             g.ratio, "", "F_along x div / C_along + F_across x div / C_across", numbers,
             "FL11473 §9 item 4 for a gusset; Simpson General Notes for an angle; a way the "
             "part does not carry has no term"),
        Step("I_allow", "interaction limit", 1.0, "", source="the same rule"),
    ]
    return tuple(steps)


NOT_COVERED = (
    NotCovered("the concrete member under the anchors",
               "out-of-plane bending of the wall top is bounded by hand in the oracle note, "
               "not computed",
               "the sealing engineer", "checking the oracle note's hand bound"),
    NotCovered("the tie block's own screws into the tied member",
               "named in the oracle note with a hand bound",
               "the sealing engineer", "checking the oracle note's hand bound"),
    NotCovered("the framed wall a tie lands on",
               "graded as that structure's bracing, not here",
               "the sealing engineer", "the lateral_system sheet"),
    NotCovered("the wood path from each load to the tied member",
               "assumed to deliver it; the deck is taken rigid in plan and every joint "
               "equally stiff",
               "the sealing engineer", "accepting the rigid-deck, equal-stiffness model"),
)

LABELS: dict[str, str] = {}


def figure(record: EngineeringRecord) -> Figure | None:
    """The governing state's resultant, torque and joint force, read off its own steps."""
    from typehaus.engineering import sketch

    state = record.governing
    if state is None or not state.working:
        return None
    by = {step.symbol: step for step in state.working}
    if not {"F_x", "F_y", "M", "x_r", "y_r", "X_i", "Y_i", "J"} <= by.keys():
        return None
    n_joint = by["X_i"].meaning.split("(")[1].split(")")[0]
    return sketch.tie_line(
        title=f"the tie line in plan, {state.name}",
        case=state.name, fx=f"{num(by['F_x'].value)} lb", fy=f"{num(by['F_y'].value)} lb",
        moment=f"{num(by['M'].value)} lb-ft",
        centre=f"({num(by['x_r'].value)}, {num(by['y_r'].value)}) ft",
        joints=f"J = {num(by['J'].value)} ft^2", joint=n_joint,
        forces=f"X_i = {num(by['X_i'].value)} lb, Y_i = {num(by['Y_i'].value)} lb",
        caption="Not to scale. Signs show the worse of the two senses of the load.")
