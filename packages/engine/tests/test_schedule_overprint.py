"""No schedule lettering prints on top of other lettering (C7-E1).

Measured on the rendered figure, at the printed point size the writer actually set — the
defect was precisely that the reserved width and the printed width disagreed, so only the
drawn text can say whether two strings collide. Ledger, because it is the paper that
shrinks the schedules hardest.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from typehaus.emit.draw.paper import LEDGER  # noqa: E402

pytestmark = pytest.mark.slow


def _collisions(fig, keep=lambda text: True) -> list[tuple[str, str]]:
    # At print resolution: Agg's hinting at the 100 dpi default widens 4 pt glyphs.
    fig.set_dpi(300)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    artists = [*fig.texts]
    for ax in fig.axes:
        artists.extend(ax.texts)
        for table in ax.tables:
            artists.extend(cell.get_text() for cell in table.get_celld().values())
    boxes = sorted(((a.get_window_extent(renderer).shrunk(0.98, 0.9), a.get_text())
                    for a in artists if a.get_visible() and a.get_text().strip()
                    and keep(a.get_text())), key=lambda item: item[0].x0)
    hits = []
    for i, (box, text) in enumerate(boxes):
        for other, other_text in boxes[i + 1:]:
            if other.x0 >= box.x1:
                break
            if box.overlaps(other):
                hits.append((text, other_text))
    return hits


class _Capture:
    """Stands in for ``PdfPages``: checks the page at the moment the writer saves it."""

    def __init__(self):
        self.hits: list[tuple[str, str]] = []
        self.pages = 0

    def savefig(self, fig, **_kwargs):
        self.pages += 1
        self.hits.extend(_collisions(fig))


def test_schedules_print_without_overprint(catlin_model_ro):
    from typehaus.checks.code.mn_residential.profile import get_profile
    from typehaus.emit.draw.framingplan import build_framing_plan
    from typehaus.emit.draw.schedule_plan_sheet import schedule_plan_sheet
    from typehaus.emit.draw.schedules.paged_tables import continuation_number, page_count
    from typehaus.emit.draw.schedules.structural import _write_hardware_schedule, hardware_tables
    from typehaus.emit.draw.schedules.structural_notes import (
        _write_structural_notes,
        structural_notes_pages,
    )
    from typehaus.emit.draw.sheet_writer import compose_sheet, set_paper
    from typehaus.emit.draw.sheets import SheetSpec

    capture = _Capture()
    profile = get_profile("mn-2020")
    with set_paper(LEDGER):
        for page in range(page_count(hardware_tables(catlin_model_ro), LEDGER)):
            _write_hardware_schedule(capture, catlin_model_ro, continuation_number("S-602", page),
                                     "Connection hardware schedule", page=page)
        for page in range(structural_notes_pages(catlin_model_ro, LEDGER, profile=profile)):
            _write_structural_notes(capture, catlin_model_ro, continuation_number("S-001", page),
                                    "General structural notes", profile=profile, page=page)
        # S-101.1, the sheet whose MARK column printed over MARK: its schedule rows only —
        # plan labels crossing linework are a different drawing's business.
        scene = schedule_plan_sheet(build_framing_plan, "main")(catlin_model_ro)
    rows = {node.content for node in scene.nodes
            if getattr(node, "layer", "") == "A-ANNO-TEXT" and len(node.content) > 12}
    fig = compose_sheet(scene, SheetSpec("S-101.1", "Framing plan — main"), catlin_model_ro,
                        size=LEDGER)
    capture.hits.extend(_collisions(fig, keep=lambda text: text in rows))
    plt.close("all")
    assert capture.pages >= 3
    assert not capture.hits, capture.hits[:10]
