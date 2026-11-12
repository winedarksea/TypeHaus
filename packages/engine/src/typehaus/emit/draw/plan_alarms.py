"""Smoke/CO/heat/leak alarm glyphs and captions on the architectural floor plan."""

from __future__ import annotations

from typing import Any

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import SceneBuilder, Symbol, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, TAG_PT, model_in_per_pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve.alarms import alarm_xy
from typehaus.resolve.model import ResolvedModel

Box = tuple[float, float, float, float]

#: Candidate caption offsets around an alarm glyph, in glyph-radii, first that clears wins.
#: Right first because that is where a reader looks for a symbol's label; below-right last
#: because it is the direction a room block already occupies.
_ALARM_LABEL_SIDES = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))

#: How far off the glyph a caption sits, metres at ``PLAN_RESERVATION_SCALE``; the glyph
#: draws at a fixed printed size, so both lengths scale inversely with the sheet.
_ALARM_LABEL_GAP_M = 0.14

#: Half-width of the reserved box around an alarm glyph, metres at the reservation scale:
#: enough that a label block placed clear of it does not sit on its shoulder either.
_ALARM_GLYPH_HALF_M = 0.11


def _paper(length_m: float, scale: float) -> float:
    """A fixed printed length, reserved at ``scale`` instead of the reservation scale."""
    return length_m * PLAN_RESERVATION_SCALE / scale


def _placed_alarms(model: Any, storey: str, scale: float = PLAN_RESERVATION_SCALE,
                   ) -> list[tuple[Any, tuple[float, float]]]:
    """Each alarm on ``storey`` and where its symbol draws: ``alarm_xy``, with alarms sharing
    a point spread side by side (ESS's smoke and heat heads both sit on the room seed).

    Read before the room blocks are placed and again when the symbols are drawn; the two
    must agree, so the rule lives here once."""
    rooms = {element.tag: element for element in model.plan.storey_elements(storey)
             if element.element_kind == "Room"}
    placed: list[tuple[Any, tuple[float, float]]] = []
    for alarm in (element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "Alarm"):
        room = rooms.get(alarm.room)
        at = alarm_xy(alarm, room) if room is not None else None
        if at is not None:
            placed.append((alarm, at))
    groups: dict[tuple[float, float], list[int]] = {}
    for index, (_, at) in enumerate(placed):
        groups.setdefault((round(at[0], 3), round(at[1], 3)), []).append(index)
    pitch = 2.0 * _paper(_ALARM_GLYPH_HALF_M, scale)
    for members in groups.values():
        for rank, index in enumerate(members):
            alarm, (x, y) = placed[index]
            placed[index] = (alarm, (x + (rank - (len(members) - 1) / 2.0) * pitch, y))
    return placed


def _glyph_box(at: tuple[float, float], scale: float) -> Box:
    x, y, half = *at, _paper(_ALARM_GLYPH_HALF_M, scale)
    return (x - half, y - half, x + half, y + half)


def _alarm_glyph_boxes(model: ResolvedModel, storey: str,
                       scale: float = PLAN_RESERVATION_SCALE) -> list[Box]:
    """The boxes the alarm SYMBOLS will occupy, for the room block to place itself around.

    The caption dodges the block and the block dodges the glyph, which is not circular: a
    glyph cannot move at all, a block can move anywhere inside its room, and a caption can
    only pick a side."""
    return [_glyph_box(at, scale) for _, at in _placed_alarms(model, storey, scale)]


def _emit_alarms(b: SceneBuilder, model: ResolvedModel, storey: str,
                 avoid: list[Box] = (), scale: float = PLAN_RESERVATION_SCALE) -> None:
    """Draw each alarm symbol where it mounts and caption it on a side clear of ``avoid``
    (the room label blocks), the other glyphs, and the captions already placed. The SYMBOL
    never moves; only the caption steps aside."""
    placed = _placed_alarms(model, storey, scale)
    glyphs = [_glyph_box(at, scale) for _, at in placed]
    captions: list[Box] = []
    for index, (alarm, at) in enumerate(placed):
        # Every AlarmKind must appear here — this is a hard index, so a new member without a
        # label KeyErrors the whole plan sheet rather than drawing an unlabelled symbol.
        label = {"smoke": "SD", "co": "CO", "combo": "SD/CO", "heat": "HD",
                 "leak": "WD", "freeze": "FD"}[alarm.kind.value]
        b.add(Symbol(name="alarm", insert=_in(at), layer="A-ANNO-SYMB"))
        others = [g for i, g in enumerate(glyphs) if i != index]
        anchor, box = _alarm_label_anchor(at, label, [*avoid, *others, *captions], scale)
        captions.append(box)
        b.add(Text(anchor=_in(anchor), content=label, height_pt=TAG_PT, layer="A-ANNO-TEXT"))


def _alarm_label_anchor(at: tuple[float, float], label: str, avoid: list[Box],
                        scale: float = PLAN_RESERVATION_SCALE,
                        ) -> tuple[tuple[float, float], Box]:
    """The first side of the glyph whose caption clears ``avoid``, else the right; with the
    caption's box. The caption is left-aligned and vertically centred on its anchor."""
    per_m = model_in_per_pt(scale) * M_PER_IN
    half_w, half_h = len(label) * TAG_PT * CHAR_ASPECT * per_m / 2.0, TAG_PT * per_m / 2.0
    gap = _paper(_ALARM_LABEL_GAP_M, scale)
    sides = [(at[0] + dx * (gap + half_w), at[1] + dy * (gap + half_h))
             for dx, dy in _ALARM_LABEL_SIDES]
    for cx, cy in sides:
        box = (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
        if not any(box[2] > o[0] and box[0] < o[2] and box[3] > o[1] and box[1] < o[3]
                   for o in avoid):
            return (box[0], cy), box
    cx, cy = sides[0]
    return (cx - half_w, cy), (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
