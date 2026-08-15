"""Shared libcst name-formatting helpers used by the dialect linter and import sync."""

from __future__ import annotations

import libcst as cst


def _dotted(node: cst.BaseExpression) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_dotted(node.value)}.{node.attr.value}"
    return ""
