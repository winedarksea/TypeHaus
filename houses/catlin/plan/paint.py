# haus: editable
# Interior paint systems, declared once (decision #113): the rooms paint every gypsum face
# with the standard's pick (resolve/room_paint.py), wet rooms take `wet`, and the trim and
# door systems bill off the derived base, casing and leaves (takeoff/trim_paint.py). The
# systems, their products and the one house white are in plan/products_paint.py; an
# authored accent coat (latex-paint-accent) is kept as authored.

from typehaus import PaintStandard

PAINT_STANDARD = [
    PaintStandard(
        uid="PE33KB7Z5B", tag="PAINT-STANDARD",
        walls="paint-wall",
        ceilings="paint-ceiling",
        wet="paint-wet",
        trim="paint-enamel",
        doors="paint-enamel",
    ),
]
