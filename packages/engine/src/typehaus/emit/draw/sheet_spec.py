"""``SheetSpec`` — one page of the set — and the helpers ``build_sheet_index`` composes with.

Split out of ``sheets.py`` (500-line limit); ``sheets`` re-exports ``SheetSpec``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.details import DerivedDetail, build_detail
from typehaus.emit.draw.scene import Scene
from typehaus.emit.draw.schedules.paged_tables import continuation_number
from typehaus.emit.draw.sheet_sets import BOTH_SETS, PERMIT_SET
from typehaus.emit.draw.sheet_writer import LEDGER, paper_for
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:
    from typehaus.checks.registry import CheckReport

SceneFn = Callable[[ResolvedModel], Scene]
PageFn = Callable[["object", ResolvedModel, str, str], None]  # pdf: PdfPages


@dataclass(frozen=True)
class SheetSpec:
    number: str                # "S-100"
    title: str                 # "Foundation plan"
    scale_note: str = "1/4\" = 1'-0\""  # hint only — compose_sheet prints the TRUE scale
    scene: SceneFn | None = None       # IR-backed sheets
    page: PageFn | None = None         # table/cover pages
    # The paper the whole *set* is on, landscape (w, h) in inches — ``build_sheet_index``
    # stamps every spec with the one it was asked for, so a set cannot be half 11x17.
    paper: tuple[float, float] = LEDGER
    # Orientation is the sheet's own business: E-602's four stacked tables need portrait on
    # whatever paper the set is printing on, which is a rotation of ``paper`` and not a
    # second preset. ``size`` resolves the two.
    portrait: bool = False
    north_arrow: bool = False          # stamp a north arrow in the viewport (plan sheets)
    # Which SETS this sheet belongs to. "full" is everything this engine can draw;
    # "permit" is what a Saint Paul DSI plan checker is asked to review, which is a
    # deliberately smaller thing — no separate E or P drawings (fixtures go on the floor
    # plans), no BOM, no room finish schedule, and only the starred derived details.
    # ``build_sheet_index(sets="permit")`` filters on it at the return.
    sets: frozenset[str] = BOTH_SETS

    @property
    def primary(self) -> bool:
        """Deprecated alias for permit-set membership. Kept for one release."""
        return PERMIT_SET in self.sets
    # What this sheet is ABOUT, for a caller that needs to find one without parsing its
    # title — ``{"storey": "main"}`` on the plan sheets. A dict rather than fields because
    # the set has no fixed vocabulary and a title is prose, not an index.
    keywords: Mapping[str, str] = field(default_factory=dict)

    @property
    def size(self) -> tuple[float, float]:
        """The figure size this sheet composes at — ``paper``, turned if it is portrait."""
        return paper_for(self.paper, self.portrait)




def _paged(number: str, title: str, page_fn, pages: int, **spec) -> list[SheetSpec]:
    """``number`` and its continuation sheets, one ``SheetSpec`` (one page) each."""
    return [SheetSpec(continuation_number(number, page),
                      title if page == 0 else f"{title} (cont.)",
                      page=partial(page_fn, page=page), **spec) for page in range(pages)]


def _storey_elevation(model: ResolvedModel, storey_tag: str) -> float:
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    return storey.elevation.meters if storey is not None else 0.0



def _derived_detail_title(derived: DerivedDetail) -> str:
    """A derived detail's sheet title, distinguished by the assemblies it actually cuts.

    ``derived.view.title`` is the *transition's* title, and a transition spawns one detail
    per distinct bound condition — so catlin printed fourteen consecutive sheets all called
    "TR-CATLIN-RIM-BAND", seven called "TR-CATLIN-FOUNDATION" and six "TR-CATLIN-EAVE". On
    the sheet index that is 27 of 98 rows saying nothing, and in the title block it means a
    sheet pulled off the pile cannot say which condition it is.

    ``derived.key`` is exactly the missing half — it is the bound condition, and it is
    unique by construction, which is why the detail set is keyed on it. ``condition:A|B``
    becomes "A / B" appended to the transition's own name.
    """
    title = derived.view.title or derived.key
    # ``rpartition``: a key is ``condition:A|B`` but a storey stack qualifies itself first
    # ("storey_stack:rim:A|B"), and splitting on the leading colon leaves that qualifier
    # stranded in front of the assemblies. The assembly list is always the last field.
    _, _, bound = derived.key.rpartition(":")
    pair = " / ".join(part for part in bound.split("|") if part)
    return f"{title} · {pair}" if pair else title


def _derived_detail_scene(model: ResolvedModel, derived: DerivedDetail) -> Scene:
    scene, _findings = build_detail(model, derived)
    return scene


def _has_engineered_items(model: ResolvedModel, house_dir: Path | None,
                          report: CheckReport | None = None) -> bool:
    """Whether any check in this house delegates to the engineering register.

    Asked by running the registry, not by enumerating the suite: which requirements a house
    puts outside the prescriptive path is a conclusion the checks reach, and a second
    enumeration here would be that judgement written twice.

    ``report`` is that same registry run, already in hand. It is not a different answer —
    it is the identical one, not computed twice: ``haus print`` runs the registry for the
    permit checklist immediately before composing the set, and this function was re-running
    every check in the house (~19 s on catlin) to append one sheet. A caller that holds a
    report for THIS model, house and jurisdiction passes it; anyone else passes nothing and
    the registry runs here as before.
    """
    if report is not None:
        return any(finding.engineering_item for finding in report.findings)

    from typehaus.checks import run_from_model

    fresh = run_from_model(model, [], house_dir)
    return any(finding.engineering_item for finding in fresh.findings)
