"""Every framed member the resolver builds is reachable through ``model_json``.

A guard against one specific, quiet class of bug, and it is worth naming because the house
carried an instance of it for weeks. ``ResolvedModel.all_members()`` collects framing from six
sources, so a new source lands in the BOM, in ``haus millwork`` and in
``checks/structural/interference.py`` the moment it has a producer. The two EMITTERS —
``emit/gltf/emitter.py`` and ``server/model_json_fabric.py`` — walk their sources by hand, and
nothing made them agree. Soffit ladder framing was the sixth source: it was billed, it was
interference-checked, and it was **invisible in 3D**, a Soffit rendering as one solid prism
with its lumber nowhere.

Nothing failed. That is the point of this test: the next source added to ``all_members()``
without an emitter fails loudly here instead of silently in the viewer.

Parity is asserted on ``(host uid, child_key)`` — the host being the object whose ``members``
list holds the stick, which is exactly what ``memberUid()`` addresses in the UI.

It is deliberately NOT keyed on ``FramedMember.parent_uid``: a member's parent and its host are
allowed to differ, and where they do it is on purpose. The wall->roof closure bands live in the
ROOF's members list and carry the WALL's uid, so that picking one selects the wall it closes;
the ridge beam is a roof member carrying its Beam's uid. Keying on ``parent_uid`` would report
126 of those as unreachable and say nothing about the thing this test is for.
"""

from __future__ import annotations

from typehaus.server.model_json import model_to_dict

# Payload keys that host framing. Each is a list of objects carrying `uid` and `members`.
# Not derived from the payload — spelled out, so that a source arriving with a producer and
# no emitter cannot satisfy this test by also not being listed here.
_MEMBER_HOSTS = ("walls", "roofs", "floors", "stairs", "braces", "soffits")


def _emitted_keys(payload) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for host_key in _MEMBER_HOSTS:
        for host in payload.get(host_key, []) or []:
            for member in host.get("members", []) or []:
                out.add((host["uid"], member["key"]))
    return out


def test_every_resolved_member_reaches_model_json(catlin_model_ro):
    model = catlin_model_ro
    payload = model_to_dict(model)
    # The same six lists ``all_members()`` walks, by host, so a source with no emitter shows
    # up as its whole set of keys missing rather than as nothing at all.
    resolved = {
        (host.uid, member.child_key)
        for hosts in (model.walls, model.roofs, model.floors, model.stairs,
                      model.braces, model.soffits)
        for host in hosts
        for member in host.members
    }
    emitted = _emitted_keys(payload)
    missing = sorted(resolved - emitted)
    assert not missing, (
        f"{len(missing)} member(s) are in all_members() but reach no emitter — "
        f"add the host to server/model_json_fabric.py AND emit/gltf/emitter.py: {missing[:12]}"
    )


def test_soffit_ladder_framing_is_in_the_payload(catlin_model_ro):
    """The instance the test above was written for, pinned by name.

    ``trade="framing"``, not ``"floors"``: ``emit/trades.py``'s "soffit" -> "floors" entry is
    a SOLID-category map that routes the finished box, and a stick belongs with every other
    stick in the building rather than behind the floors toggle. The finished box is a separate
    node on the same uid — which is why the framing node reuses ``kind="solid"`` and needs no
    new ``SelectionKind``.
    """
    payload = model_to_dict(catlin_model_ro)
    soffits = {entry["tag"]: entry for entry in payload["soffits"]}
    # All three of catlin's soffits author a FramingSpec, so all three frame.
    assert set(soffits) == {"SF-S-DUCT", "SF-S-HP1", "SF-S-SUITE"}
    hp1 = soffits["SF-S-HP1"]
    categories = {member["category"] for member in hp1["members"]}
    assert categories == {"plate", "stud", "blocking"}
    # And the two-stock ladder is visible in the payload, not just in the framing module:
    # rails on the plate profile, rungs on the member profile.
    rails = {m["profile"] for m in hp1["members"] if m["category"] == "plate"}
    rungs = {m["profile"] for m in hp1["members"] if m["key"].startswith("soffit-rung-")}
    assert rails == {"2x2"} and rungs == {"2x4"}
