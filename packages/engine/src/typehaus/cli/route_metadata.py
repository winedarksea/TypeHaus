"""Non-geometric run facts survive both a printed proposal and its evaluation."""

from __future__ import annotations

from typing import Any


def run_metadata(model: Any, tag: str, fields: tuple[str, ...]) -> dict[str, Any]:
    authored = next((element for element in model.plan.all_elements()
                     if element.tag == tag), None)
    if authored is None:
        return {}
    return {name: value for name in fields
            if (value := getattr(authored, name, None)) is not None}
