"""Cut-layer fill parity between the detail writer and the in-app detail canvas.

``emit/draw/palette.py``'s ``DETAIL_FILL`` decides what colour a cut layer is on the rendered
PNG/PDF. ``ui/src/components/DetailCanvas.tsx`` draws *the same* ``Scene`` in the app and
carries its own hand-authored copy of that table, with a comment saying the two must match.
Nothing checked that they did.

They did not, and the way they failed is the point. ``metal-dark-exterior`` — the house's one
exterior dark, named by the roof edge trim, the eave water chain and the guards — and ``kdat``
— the treated half of the catlin truss wall — were absent from **both** tables, so a box
gutter and every outer girt fell through to the near-white fallback and drew as blank boxes on
a detail whose whole subject is which piece is which. A missing key is silent in both
languages: there is no error, just a wrong colour that reads as an empty shape.

The existing parity tests do not cover this. ``test_palette_parity`` pins
``emit/gltf/palette.py`` (the 3D member colours) against the generated vocabulary manifest;
``DetailCanvas``'s table is a different mirror of a different palette and was unguarded.

The right long-term fix is the one ``members.ts`` and ``detailTypography.ts`` already took —
delete the TypeScript copy and import a generated manifest — and until someone does that, this
test is what stands in for it. It reads the TypeScript as text, which is exactly the
arrangement ``test_palette_parity``'s docstring calls out as having drifted before; it is
still strictly better than the nothing that was here.
"""

from __future__ import annotations

import re

from _helpers import REPO_ROOT

from typehaus.emit.draw.palette import DETAIL_FILL

DETAIL_CANVAS = REPO_ROOT / "ui" / "src" / "components" / "DetailCanvas.tsx"

#: Engine keys the canvas is not expected to carry. Empty today, and deliberately so: every
#: material the section cutter can reach is a material the app draws too, because it draws the
#: same Scene. A key added here needs a reason written beside it.
CANVAS_EXEMPT: frozenset[str] = frozenset()


def _canvas_detail_fill() -> dict[str, str]:
    """The ``DETAIL_FILL`` object literal in ``DetailCanvas.tsx``, parsed to a dict.

    Quoted and bare keys both occur (``"metal-dark": "#2f2f2f"`` beside ``metal: "#ffffff"``),
    which is why this is a regex over the object's body rather than a JSON load.
    """
    source = DETAIL_CANVAS.read_text()
    start = source.index("const DETAIL_FILL")
    body = source[start:source.index("\n};", start)]
    return {key or bare: value for key, bare, value in
            re.findall(r'(?:"([^"]+)"|([A-Za-z_][\w-]*))\s*:\s*"(#[0-9a-fA-F]{3,8})"', body)}


def test_every_engine_detail_fill_is_mirrored_in_the_app() -> None:
    """A material the writer fills is a material the app fills, in the same ink."""
    canvas = _canvas_detail_fill()
    missing = sorted(set(DETAIL_FILL) - set(canvas) - CANVAS_EXEMPT)
    assert not missing, (
        f"{DETAIL_CANVAS.name} is missing {missing} — those materials draw as the near-white "
        "fallback in the app while the rendered detail shows them correctly")
    wrong = {key: (DETAIL_FILL[key], canvas[key]) for key in DETAIL_FILL
             if key in canvas and DETAIL_FILL[key].lower() != canvas[key].lower()}
    assert not wrong, f"engine/app fill disagreement (engine, app): {wrong}"


def test_the_app_invents_no_fill_the_engine_does_not_have() -> None:
    """Drift runs both ways: a key only the canvas knows is a colour no rendered sheet shows.

    Worse than the missing-key direction, because it looks right in the app — which is where
    the material gets reviewed — and is wrong on the sheet that goes to the field.
    """
    extra = sorted(set(_canvas_detail_fill()) - set(DETAIL_FILL))
    assert not extra, (
        f"{DETAIL_CANVAS.name} fills {extra}, which emit/draw/palette.py does not — the app "
        "and the printed detail would disagree about those materials")
