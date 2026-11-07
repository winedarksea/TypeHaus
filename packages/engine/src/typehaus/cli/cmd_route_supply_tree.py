"""``haus route --tree`` on a supply main, and ``--topology {tree,trunk}``.

STUB: E4 fills this. ``cmd_route`` hands a tree here when ``--topology`` is given or
:func:`is_supply_main` says the target is a pressurised run. docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.cli.route_options import RouteOptions, not_built

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal


def is_supply_main(model: ResolvedModel, tree: str) -> bool:
    """True when ``--tree tree`` names a supply main this module routes. False until built,
    so a supply tag keeps today's "not a drain run" problem from ``_propose_tree``."""
    return False


def propose_supply_tree(model: ResolvedModel, tree: str, topology: str | None,
                        opts: RouteOptions
                        ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                                   list]:
    """``_propose_tree``'s return shape for supply main ``tree``.

    ``topology`` is None (the default for the main), "tree" (one Steiner-style tree) or
    "trunk" (trunk and branch proposals split). Returns (proposal/storey pairs, problems,
    notices, structured refusals); ``cmd_route`` evaluates and reports them."""
    not_built("--topology" if topology else "--tree on a supply main")
