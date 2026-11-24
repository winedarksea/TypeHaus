"""ASCII free-body sketches for the calculation sheets — the shapes kinds share.

Each returns a :class:`~typehaus.engineering.item.Figure` drawn from numbers the caller
passes in (read off the record), so a sketch can never disagree with the sheet under it.
Pure, deterministic, ASCII only, at most ``FIGURE_WIDTH`` characters a line. Not to scale:
the labels carry the dimensions.
"""

from __future__ import annotations

from typehaus.engineering.item import FIGURE_WIDTH, Figure, num


def _fit(lines: list[str]) -> tuple[str, ...]:
    out = tuple(line.rstrip() for line in lines)
    assert all(len(line) <= FIGURE_WIDTH for line in out), "sketch wider than the page"
    return out


def _centre(text: str, width: int) -> str:
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text


def beam_on_two_posts(*, title: str, a_ft: float, s_ft: float, b_ft: float,
                      load: str, reactions: tuple[str, str], caption: str = "") -> Figure:
    """A beam with an overhang either side of two posts, under a uniform line load."""
    left, span, right = (6 if a_ft > 0 else 0), 36, (6 if b_ft > 0 else 0)
    width = 2 + left + span + right
    x1, x2 = 2 + left, 2 + left + span
    beam = " " + "=" * (width - 1)
    arrows = " " + " ".join("v" for _ in range((width - 1) // 2))
    seats = [" "] * (width + 1)
    seats[x1] = seats[x2] = "^"
    dims = [" "] * (width + 1)
    dims[x1], dims[x2] = "|", "|"
    span_label = f"<- s = {num(s_ft)} ft ->"
    start = x1 + 1 + max(0, (span - 1 - len(span_label)) // 2)
    for i, ch in enumerate(span_label):
        dims[start + i] = ch
    lines = [
        _centre(load, width),
        arrows,
        beam,
        "".join(seats),
        "".join(dims),
        f"  a = {num(a_ft)} ft (left overhang), b = {num(b_ft)} ft (right overhang)",
        f"  R1 = {reactions[0]}, R2 = {reactions[1]} (up, at the posts)",
    ]
    return Figure(title, _fit(lines), caption)


def cantilever_wall(*, title: str, height_ft: float, stem_in: float, toe_ft: float,
                    heel_ft: float, footing_ft: float, thrust: str, thrust_arm_ft: float,
                    weight: str, base: str, caption: str = "") -> Figure:
    """A cantilever retaining wall in section: thrust on the retained side, weight down,
    friction and bearing at the base. The retained soil is on the right."""
    lines = [
        "          stem " + num(stem_in) + " in" + "      retained soil",
        "            |##|  . . . . . . . . . . . .",
        "            |##|  . . . . . . . . . . . .  <-- " + thrust,
        f"            |##|  . . . . . . . . . . . .      at {num(thrust_arm_ft)} ft above",
        f"   H = {num(height_ft)} ft |##|  . . . . . . . . . . . .      the footing underside",
        "            |##|  . . . . W (soil on heel)",
        "  _______   |##|  . . . . . . . . . . . .",
        "  |=======================================|  footing " + num(footing_ft) + " ft",
        "  |<- toe " + num(toe_ft) + " ->|  |<-- heel " + num(heel_ft) + " -->|",
        "       ^ bearing          v " + weight,
        "  ->  " + base,
    ]
    return Figure(title, _fit(lines), caption)


def pinned_post(*, title: str, length_ft: float, axial: str, lateral: str,
                head: str, base: str, caption: str = "") -> Figure:
    """A post pinned head and foot: axial down at the head, wind across its height."""
    lines = [
        "        | " + axial,
        "        v",
        "      [====]  head: " + head,
        "        ||",
        "   -->  ||",
        "   -->  ||   L = " + num(length_ft) + " ft, K = 1 (pinned both ends)",
        "   -->  ||   " + lateral,
        "   -->  ||",
        "        ||",
        "      [====]  base: " + base,
        "      //////  pier",
    ]
    return Figure(title, _fit(lines), caption)


def diaphragm_on_joint(*, title: str, depth_ft: float, width_ft: float, along: str,
                       across: str, couple: str, chord: str, chord_across: str = "",
                       neighbour: str = "the neighbouring roof", caption: str = "") -> Figure:
    """A deck in plan, held along one edge by a joint to its neighbour and free on the
    opposite (open) edge: shear along and across the joint, the couple between the two,
    and the chord force at the deck's two ends (SDPWS 4.2.5.2)."""
    lines = [
        f"  {neighbour} (the deck's only support)",
        "  =S=====S=====S=====S=====S=====S=  joint: straps (S) and nailing",
        "  ||                               ||  --> V_a = " + along,
        "  ||   deck, plan view             ||",
        "  ||                               ||  vv  V_x = " + across,
        f"  ||  L' = {num(depth_ft)} ft deep{' ' * 15}||",
        "  ||                               ||",
        "  +--------- open front ------------+  free edge, W' = " + num(width_ft) + " ft",
        "  chord at each end of the deck: T_ch = M / W' = " + chord,
        "  couple M = V_a x its lever to the resultant = " + couple,
    ]
    if chord_across:
        lines += ["  N-S: the first and last truss are the deck's chords,",
                  "       T = V L / (8 d) = " + chord_across]
    return Figure(title, _fit(lines), caption)


def tie_line(*, title: str, case: str, fx: str, fy: str, moment: str, centre: str,
             joints: str, joint: str, forces: str, caption: str = "") -> Figure:
    """A deck held to a wall by tie joints, in plan: the case's resultant force and torque
    on a deck taken rigid, shared over the joints; the governing joint's share below."""
    lines = [
        "  plan view, x across, y up the page; " + case,
        "",
        "            F_y = " + fy,
        "               |",
        "               v        torque M = " + moment,
        "      +------------------------+   about " + centre,
        "      |  deck, rigid in plan   | --> F_x = " + fx,
        "      +--o-------o--------o----+",
        "         ^       ^        ^   tie joints: " + joints,
        "  wall ==========================  shared by the elastic method",
        "",
        "  governing joint: " + joint,
        "    " + forces,
    ]
    return Figure(title, _fit(lines), caption)


def wall_top_joint(*, title: str, axial: str, moment: str, shear: str, round_in: float,
                   couple: str, base: str, caption: str = "") -> Figure:
    """A round column fixed on a foundation-wall top: its factored loads, the dowel couple
    across the joint, and the stem below."""
    lines = [
        "         P_u = " + axial,
        "           |",
        "           v",
        "      M_u = " + moment + " (at the joint)",
        "     [=========]   V_u = " + shear,
        f"     [{num(round_in):>4} in. ]  -->",
        "     [  round  ]",
        "  ===+====+====+===  joint on the wall top: bearing C, dowels T",
        "     T ^       v C   " + couple,
        "  ###|          |###  stem below: plain concrete, spread at 45 deg",
        "  ###|__________|###  " + base,
        "  ########################  footing",
    ]
    return Figure(title, _fit(lines), caption)


def fixed_column(*, title: str, height_ft: float, axial: str, wind: str, guard: str,
                 base_moment: str, k: str, base: str, caption: str = "") -> Figure:
    """A column fixed at its base and free at its head: the cantilever a moment column is."""
    lines = [
        "        | P_u = " + axial,
        "        v",
        "      [====]  head: free (no moment restrained), k = " + k,
        "        ||",
        "   -->  ||   wind, 1.0W: " + wind,
        "   -->  ||   guard: " + guard,
        "   -->  ||   H = " + num(height_ft) + " ft above the joint",
        "        ||",
        "        ||",
        "      [====]  base: " + base,
        "     (  M_u  )  base moment " + base_moment,
    ]
    return Figure(title, _fit(lines), caption)
