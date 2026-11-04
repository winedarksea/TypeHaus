"""G-001 and its continuations G-001.1, G-001.2 … as ``SheetSpec``s.

The cover's sheet index is itself part of the set: when it outgrows G-001 it continues on
G-001.n, and those sheets are index entries too. So the page count is a fixed point, found
here while the sheet list is built (``add_cover``): the smallest ``k`` for which the index
*including* ``k - 1`` continuation entries paginates into ``k`` pages. The layout is bound
into each spec, so PDF order, manifest and the printed index come from one finalised list.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from typehaus.emit.draw.schedules.cover import (
    _footer_paragraphs,
    _write_cover,
    cover_header,
    footer_height_in,
)
from typehaus.emit.draw.schedules.cover_index import HEADING_GAP_IN, IndexPage, paginate
from typehaus.emit.draw.schedules.paged_tables import continuation_number
from typehaus.emit.draw.sheet_spec import SheetSpec
from typehaus.emit.draw.title_block import content_box
from typehaus.emit.draw.typography import wrap_columns_for

if TYPE_CHECKING:
    from pathlib import Path

    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import CheckReport, Preferences
    from typehaus.resolve.model import ResolvedModel

COVER = "G-001"
COVER_TITLE = "Cover / code summary"
CONT_TITLE = "Sheet index (cont.)"

#: Safety bound on continuation pages; a real set needs one or two.
_MAX_PAGES = 40


@dataclass(frozen=True)
class CoverPlan:
    """Every page's index slice, and the gate statement G-001 prints (pre-wrapped)."""
    pages: tuple[IndexPage, ...]
    footer: tuple[tuple[str, ...], ...]


def cover_inputs(model: ResolvedModel, profile: JurisdictionProfile | None,
                 preferences: Preferences | None, house_dir: Path | None,
                 report: CheckReport | None) -> tuple[JurisdictionProfile, CheckReport]:
    """The jurisdiction and registry run the cover is composed against.

    The profile defaults the way ``write_permit_set`` resolves it. A caller without a
    ``report`` gets one run here, which the engineering-register test shares.
    """
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Preferences
    from typehaus.checks.run import resolve_profile

    if profile is None:
        profile = resolve_profile(preferences or Preferences())
    if report is None:
        report = run_from_model(model, [], house_dir, profile=profile.name,
                                preferences=preferences)
    return profile, report


def plan_cover(model: ResolvedModel, profile: JurisdictionProfile, report: CheckReport,
               paper: tuple[float, float], rest: list[tuple[str, str]]) -> CoverPlan:
    """Paginate the index of ``rest`` (every sheet after the cover) plus the cover's own."""
    from typehaus.checks import evaluate_permit_checklist

    box = content_box(paper)
    x0, y0, x1, y1 = box
    register = next((number for number, title in rest if title == "Engineering register"),
                    None)
    footer = tuple(tuple(p) for p in _footer_paragraphs(
        profile, evaluate_permit_checklist(report, profile),
        wrap_columns_for(x1 - x0, 9.0), register=register))
    head = cover_header(model, profile, box)
    first = head.index_top - HEADING_GAP_IN - (y0 + footer_height_in(footer))
    later = (y1 - 0.35 - HEADING_GAP_IN) - (y0 + 0.10)
    return CoverPlan(tuple(converge(rest, first_height_in=first, later_height_in=later,
                                    width_in=x1 - x0)), footer)


def converge(rest: list[tuple[str, str]], *, first_height_in: float, later_height_in: float,
             width_in: float) -> list[IndexPage]:
    """The smallest page count ``k`` whose index, with ``k - 1`` continuation entries, fills ``k``.

    More continuation entries never shrink the index, so the search is monotone.
    """
    for pages_n in range(1, _MAX_PAGES + 1):
        index = [(COVER, COVER_TITLE),
                 *((continuation_number(COVER, page), CONT_TITLE)
                   for page in range(1, pages_n)), *rest]
        pages = paginate(index, first_height_in=first_height_in,
                         later_height_in=later_height_in, width_in=width_in)
        if len(pages) == pages_n:
            return pages
        if len(pages) < pages_n:
            raise RuntimeError(f"sheet index shrank to {len(pages)} page(s) at {pages_n}")
    raise RuntimeError("sheet index does not converge: no room for rows on a cover page")


def add_cover(sheets: list[SheetSpec], model: ResolvedModel, profile: JurisdictionProfile,
              report: CheckReport, paper: tuple[float, float]) -> list[SheetSpec]:
    """``sheets`` with G-001 (its first element) replaced by the planned cover pages."""
    if not sheets or sheets[0].number != COVER:
        return sheets
    rest = sheets[1:]
    plan = plan_cover(model, profile, report, paper,
                      [(sheet.number, sheet.title) for sheet in rest])
    cover = [SheetSpec(continuation_number(COVER, page),
                       COVER_TITLE if page == 0 else CONT_TITLE,
                       page=partial(_write_cover, plan=plan, page=page, profile=profile),
                       paper=paper, sets=sheets[0].sets)
             for page in range(len(plan.pages))]
    return [*cover, *rest]
