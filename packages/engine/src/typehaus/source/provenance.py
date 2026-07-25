"""Provenance map: {tag → (file, CST node span)} for the writeback path (→ 02 §Two paths)."""

from __future__ import annotations

import libcst as cst

from typehaus.findings import SourceLoc


class Provenance:
    """Maps a plan element's ``tag`` to where its constructor call lives in source.

    Two tiers: *editable* locations come from the libcst scan of ``# haus: editable``
    files and are the only ones writeback may target; *generated* locations come from
    runtime authorship capture (params/ math modules, ``plan/views.py`` …) and are
    read-only badges — never a writeback destination.
    """

    def __init__(self) -> None:
        self._by_tag: dict[str, SourceLoc] = {}
        self._generated: dict[str, SourceLoc] = {}

    def add(self, tag: str, loc: SourceLoc) -> None:
        self._by_tag[tag] = loc

    def add_generated(self, tag: str, loc: SourceLoc) -> None:
        """Record a read-only (runtime-captured) location; editable always wins."""
        if tag not in self._by_tag:
            self._generated[tag] = loc

    def location(self, tag: str) -> SourceLoc | None:
        loc = self._by_tag.get(tag)
        return loc if loc is not None else self._generated.get(tag)

    def is_editable(self, tag: str) -> bool:
        return tag in self._by_tag

    def editable_tags(self) -> frozenset[str]:
        return frozenset(self._by_tag)

    def tags(self) -> frozenset[str]:
        return frozenset(self._by_tag)

    def items(self) -> list[tuple[str, SourceLoc]]:
        """Editable (tag, location) pairs — used to cache/replay a single file's provenance."""
        return list(self._by_tag.items())

    def __len__(self) -> int:
        return len(self._by_tag)


def scan_provenance(
    file: str, source: str, prov: Provenance,
    wrapper: "cst.MetadataWrapper | None" = None,
) -> None:
    """Record the source location of every constructor call carrying a ``tag=`` kwarg.

    ``wrapper`` may be a pre-built :class:`MetadataWrapper` shared with the loader's dialect
    lint so libcst parses each file once per rebuild rather than three times (Phase 0).
    """
    if wrapper is None:
        wrapper = cst.MetadataWrapper(cst.parse_module(source))
    positions = wrapper.resolve(cst.metadata.PositionProvider)

    class _V(cst.CSTVisitor):
        def visit_Call(self, node: cst.Call) -> None:
            for arg in node.args:
                if (
                    arg.keyword is not None
                    and arg.keyword.value == "tag"
                    and isinstance(arg.value, cst.SimpleString)
                ):
                    tag = arg.value.evaluated_value
                    if isinstance(tag, str):
                        pos = positions[node]
                        prov.add(tag, SourceLoc(file=file, line=pos.start.line,
                                                column=pos.start.column))

    wrapper.visit(_V())
