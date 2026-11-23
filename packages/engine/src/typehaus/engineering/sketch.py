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
