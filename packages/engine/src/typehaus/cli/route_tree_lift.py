"""``haus route --tree TAG --lift RUN``: a drain tree that re-lays authored blockers.

STUB: E1 fills this. docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.cli.route_options import RouteOptions, not_built

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal


def propose_tree_lifted(model: ResolvedModel, tree: str, lift: tuple[str, ...],
                        opts: RouteOptions
                        ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                                   list]:
    """``_propose_tree``'s return shape for drain main ``tree`` with ``lift`` (authored run
    tags, in the order given) as ``touch`` and re-laid against the tree.

    Returns (proposal/storey pairs, problems, notices, structured refusals); ``cmd_route``
    evaluates and reports them as it does a plain tree. ``--alternatives`` is already
    refused with ``--tree``. A lift that names no run is a problem, not an exception."""
    not_built("--lift")
