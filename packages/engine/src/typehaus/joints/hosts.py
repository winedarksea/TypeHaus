"""Which storey a framed member stands in.

``ResolvedModel.all_members`` flattens the hosts away and a ``FramedMember`` carries no
storey of its own, so the storey a joint is filed under comes from the thing that owns the
member. Built by walking each host's **own** member list rather than by matching
``parent_uid`` against host uids: a member's parent is not always the host record's ``uid``
(the ridge beam's is not), and a map that silently missed would file 67 of catlin's markers
under the empty storey — which the IFC emitter turns into a ``KeyError`` and every other
reader turns into a marker in the wrong place.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel


def member_storeys(model: ResolvedModel) -> dict[str, str]:
    """``parent_uid -> storey`` for every framing host in the model."""
    by_uid: dict[str, str] = {}
    for hosts in (model.walls, model.stairs, model.floors, model.roofs,
                  model.braces, model.soffits):
        for host in hosts:
            for member in host.members:
                by_uid.setdefault(member.parent_uid, host.storey)
    return by_uid
