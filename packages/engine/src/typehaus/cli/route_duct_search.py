"""The one entry point every duct search goes through (E3 replaces the duct body).

``search_for`` stands in for ``route_roots.search_for`` at every call site in
``cmd_route``/``route_propose`` (proposal, counterfactual, sweep); non-ducts are untouched.
docs/routing.md."""

from __future__ import annotations

from typing import Any

from typehaus.cli import route_roots


def search_for(model: Any, graph: Any, ends: Any, slope: float | None):
    """``route_roots.search_for``'s contract: (search callable, refusal report)."""
    if ends.kind == "duct":
        return duct_search(model, graph, ends, slope)
    return route_roots.search_for(model, graph, ends, slope)


def duct_search(model: Any, graph: Any, ends: Any, slope: float | None):
    """The duct's search callable ``(graph, space, start, goals) -> found | None`` and its
    refusal report (None if it has none). Today: the generic plain A*, as before."""
    return route_roots.search_for(model, graph, ends, slope)
