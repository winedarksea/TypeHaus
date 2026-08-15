"""Cost codes for BOM rows — NAHB primary, CSI MasterFormat optional.

A contractor's estimating software, accounting package and schedule all key on a *code*, not
on a material name: "2x6" is not something RSMeans Online, Craftsman Cloud, Buildertrend or a
QuickBooks job-cost report can file. Nothing in this repo carried a code taxonomy of any kind
before this module, so a Type:Haus export had to be re-coded by hand on the way in.

**NAHB is primary** because this is residential: the NAHB Chart of Accounts is what
residential builders, their lenders and their accountants actually use, and Buildertrend /
CoConstruct ship it as their default cost-code set. CSI MasterFormat is carried alongside
and is nullable — it is the commercial-specification vocabulary, useful when an architect or
a commercial sub is in the loop and merely noise otherwise.

Per **decision #28** the house owns its own numbers: a `[codes]` table in ``prices.toml``
overrides anything here, keyed ``"section"`` or ``"section:key"``. Custom codes are the
residential norm — most builders have inherited a numbering scheme from their accountant —
so the built-in table is a *starting point*, never an authority.

The ``trade`` column deliberately reuses :data:`typehaus.emit.trades.TRADES`, the same
13-value vocabulary the 3D viewer's visibility toggles use (and that
``tests/test_solid_trade_parity.py`` pins against ``ui/src/state/vocabulary.ts``). A parallel
trade vocabulary invented here would drift from it within a release.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

from typehaus.emit.trades import TRADES


@dataclass(frozen=True)
class CostCode:
    """One row's filing: NAHB account, optional CSI division, and a viewer trade."""

    nahb: str
    csi: str | None
    trade: str

    def as_dict(self) -> dict[str, str | None]:
        return {"nahb_code": self.nahb, "csi_code": self.csi, "trade": self.trade}


#: Per-key refinements, matched with :func:`fnmatch.fnmatchcase` against the BOM key and
#: tried before the section default. Ordered: the first pattern that matches wins, so put
#: the specific ones first.
#:
#: Kept deliberately short. A code table that tries to classify every key is a table that is
#: wrong about most of them; the section default is the honest answer for anything whose
#: key does not carry its trade on its face.
KEY_PATTERNS: tuple[tuple[str, str, CostCode], ...] = (
    # Concrete solids: the category *is* the account. Footings and flatwork are separate
    # NAHB accounts and separate subs, and lumping them loses the distinction the
    # estimator most wants.
    ("concrete", "footing*", CostCode("1200", "03 30 00", "concrete")),
    ("concrete", "slab*", CostCode("1300", "03 30 00", "concrete")),
    ("concrete", "pier*", CostCode("1200", "03 30 00", "concrete")),
    ("concrete", "gutter", CostCode("2600", "07 71 00", "drainage")),
    ("concrete", "downspout", CostCode("2600", "07 71 00", "drainage")),
    # Framing profiles that are not lumber.
    ("framing", "gutter*", CostCode("2600", "07 71 00", "drainage")),
    ("framing", "*panel*", CostCode("2400", "08 80 00", "openings")),
    # Sheet goods: roof and wall sheathing bill to the same account as the framing they
    # skin, insulated sheathing to insulation.
    ("sheet_goods", "zip-r*", CostCode("2100", "07 21 00", "walls")),
    # Openings: doors and windows are one NAHB account but two CSI divisions.
    ("openings", "*door*", CostCode("2400", "08 10 00", "openings")),
    ("openings", "*window*", CostCode("2400", "08 50 00", "openings")),
    # Pipe runs carry their system in the key.
    ("pipe_runs", "vent", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "drain", CostCode("3100", "22 13 00", "plumbing")),
    ("pipe_runs", "water_*", CostCode("3100", "22 11 00", "plumbing")),
    ("pipe_runs", "gas", CostCode("3300", "22 11 00", "plumbing")),
    ("pipe_runs", "radon", CostCode("3200", "23 05 00", "mechanical")),
)

#: The default code for every section in ``cli.prices.ESTIMATE_PLANS``. Every section must
#: appear here; ``tests/test_cost_codes.py`` pins that, the same way ``ESTIMATE_PLANS``
#: itself is pinned against ``_SECTIONS``.
SECTION_CODES: dict[str, CostCode] = {
    "framing": CostCode("2000", "06 11 00", "framing"),
    "sheet_goods": CostCode("2000", "06 16 00", "framing"),
    "hardware": CostCode("2000", "06 05 23", "framing"),
    "concrete": CostCode("1300", "03 30 00", "concrete"),
    "floor_heat": CostCode("3200", "23 83 00", "mechanical"),
    "placeables": CostCode("4200", "11 30 00", "furniture"),
    "floor_finishes": CostCode("4000", "09 60 00", "floors"),
    "envelope_layers": CostCode("2100", "07 20 00", "walls"),
    "wood_surfaces": CostCode("4100", "06 20 00", "walls"),
    "openings": CostCode("2400", "08 00 00", "openings"),
    "footing_bedding": CostCode("1100", "31 23 00", "earth"),
    "pipe_runs": CostCode("3100", "22 10 00", "plumbing"),
    "ducts": CostCode("3200", "23 31 00", "mechanical"),
    "sleeves": CostCode("3100", "22 05 17", "plumbing"),
    "conduit": CostCode("3300", "26 05 33", "electrical"),
    "plumbing_specialties": CostCode("3100", "22 40 00", "plumbing"),
    "install_parts": CostCode("3100", "22 05 00", "plumbing"),
    "pipe_insulation": CostCode("3100", "22 07 00", "plumbing"),
    "edge_trim": CostCode("2500", "07 62 00", "roof"),
    "wall_structure": CostCode("1200", "03 30 00", "concrete"),
    "railings": CostCode("2700", "05 52 00", "stairs"),
    "drainage": CostCode("2600", "07 71 00", "drainage"),
    "furnishings": CostCode("4200", "12 50 00", "furniture"),
}


def cost_code(section: str, key: str, overrides: dict[str, str] | None = None) -> CostCode:
    """The code for one BOM row: house override, then key pattern, then section default.

    ``overrides`` is ``prices.toml``'s ``[codes]`` table, keyed ``"section"`` or
    ``"section:key"``. It supplies the NAHB code only — the CSI code and the trade come
    from the built-in table either way, because a builder overriding their chart of
    accounts is not thereby renaming MasterFormat.
    """
    base = None
    for plan_section, pattern, code in KEY_PATTERNS:
        if plan_section == section and fnmatch.fnmatchcase(key.lower(), pattern):
            base = code
            break
    if base is None:
        base = SECTION_CODES.get(section)
    if base is None:
        raise KeyError(f"no cost code for section {section!r}; add it to SECTION_CODES")
    if overrides:
        custom = overrides.get(f"{section}:{key}") or overrides.get(section)
        if custom is not None:
            return CostCode(custom, base.csi, base.trade)
    return base


def _validate() -> None:
    """Import-time guard: every trade named here must be one the viewer actually has."""
    named = {code.trade for code in SECTION_CODES.values()}
    named |= {code.trade for _, _, code in KEY_PATTERNS}
    unknown = sorted(named - TRADES)
    if unknown:
        raise ValueError(f"cost_codes names trades the viewer does not have: {unknown}")


_validate()
