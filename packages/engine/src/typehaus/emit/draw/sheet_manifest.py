"""The permit set's sheet index, as JSON beside the PDF.

``haus print`` composes one multi-page vector PDF and, until now, said nothing on disk about
what is on which page. A reader — the viewer's Drawings tab, a plan-check clerk, a script —
then had no way to jump to "S-101" short of paging through the whole set.

Pure: it takes the index ``write_permit_set`` already returns and the stamp the command
already decided, and returns a dict. No matplotlib, no model, no filesystem beyond the one
explicit writer at the bottom.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def sheet_manifest(index: Iterable[tuple[str, str]], *, pdf_name: str, paper: str,
                   issue: str, printed_at: str, engine_version: str,
                   content_hash: str) -> dict[str, Any]:
    """``{sheets, pdf, paper, issue, printed_at, engine_version, content_hash}``.

    ``index`` is ``write_permit_set``'s ``(number, title)`` sequence, in composed order.
    Page numbers are that order, 1-based: every sheet spec produces exactly one
    ``pdf.savefig`` (the cover through ``_write_cover``, table pages through
    ``sheet_writer.table_page``, scene sheets inline), so position *is* the page.
    """
    sheets = [{"number": number, "title": title, "page": page}
              for page, (number, title) in enumerate(index, start=1)]
    return {
        "content_hash": content_hash,
        "engine_version": engine_version,
        "issue": issue,
        "paper": paper,
        "pdf": pdf_name,
        "printed_at": printed_at,
        "sheets": sheets,
    }


def write_sheet_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write the manifest byte-deterministically, so two prints of one model diff cleanly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path
