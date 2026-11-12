"""Shrink a composed set onto smaller paper: the 11x17 check print as a true reduction.

A reduced set is the full-size sheets scaled down, not a re-layout: lettering sized for
24x36 at 1/16" scale is wider than a closet (owner, 2026-11-12). Each page keeps its
orientation and is centred at one uniform factor, so vectors stay vectors and graphic
scale bars stay true to the drawing; the stated scales do not, hence DO NOT SCALE.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

PT_PER_IN = 72.0


def reduce_pdf(data: bytes, paper: tuple[float, float], output: Path) -> Path:
    """Write ``data``'s pages onto ``paper`` (inches, either orientation) at ``output``."""
    from pypdf import PdfWriter, Transformation
    from pypdf.generic import RectangleObject

    writer = PdfWriter(clone_from=BytesIO(data))
    long_pt, short_pt = max(paper) * PT_PER_IN, min(paper) * PT_PER_IN
    for page in writer.pages:
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        tw, th = (long_pt, short_pt) if w >= h else (short_pt, long_pt)
        k = min(tw / w, th / h)
        page.add_transformation(
            Transformation().scale(k, k).translate((tw - w * k) / 2, (th - h * k) / 2))
        box = RectangleObject([0, 0, tw, th])
        page.mediabox = box
        page.cropbox = box
        page.trimbox = box
    with output.open("wb") as handle:
        writer.write(handle)
    return output
