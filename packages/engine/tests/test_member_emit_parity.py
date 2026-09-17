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

    ``trade="framing"``, not ``"drywall"``: ``emit/trades.py``'s "soffit" -> "drywall" entry
    is a SOLID-category map that routes the finished box, and a stick belongs with every
    other stick in the building rather than behind the drywall toggle. The finished box is a separate
    node on the same uid — which is why the framing node reuses ``kind="solid"`` and needs no
    new ``SelectionKind``.
    """
    payload = model_to_dict(catlin_model_ro)
    soffits = {entry["tag"]: entry for entry in payload["soffits"]}
    # Every soffit in the house authors a FramingSpec, so every one of them frames. The claim
    # is COVERAGE, not a census: enumerating the tags made this a tripwire that fired on any
    # new soffit (two basement bulkheads landed on 2026-09-07), which is not what it is for.
    assert set(soffits) == {item.tag for item in catlin_model_ro.soffits}
    assert {"SF-S-DUCT", "SF-S-HP1"} <= set(soffits)
    assert all(entry["members"] for entry in soffits.values())
    hp1 = soffits["SF-S-HP1"]
    categories = {member["category"] for member in hp1["members"]}
    assert categories == {"plate", "stud", "blocking"}
    # And the two-stock ladder is visible in the payload, not just in the framing module:
    # rails on the plate profile, rungs on the member profile.
    rails = {m["profile"] for m in hp1["members"] if m["category"] == "plate"}
    rungs = {m["profile"] for m in hp1["members"] if m["key"].startswith("soffit-rung-")}
    assert rails == {"2x2"} and rungs == {"2x4"}


def test_every_rebar_piece_reaches_both_emitters(catlin_model_ro):
    """Bars are not framing (decision #75), so they get their own parity: every piece is in
    ``/model/rebar`` under its host, the model.json summary counts the same pieces, and the
    glTF carries one ``concrete:rebar`` node per host whose geometry is exactly one tube per
    leg of every bar's path."""
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.gltf.rebar import _CIRCLE_STRIDE, _FACETS, REBAR_FACET
    from typehaus.server.model_json_rebar import rebar_bars_json

    model = catlin_model_ro
    bars = rebar_bars_json(model, None)["rebar"]
    summary = {host["uid"]: host["bar_count"] for host in model_to_dict(model)["rebar"]}
    by_host = {host["uid"]: host["members"] for host in bars}
    resolved = {s.host_uid: s.bars for s in model.rebar}
    assert summary == {uid: len(pieces) for uid, pieces in resolved.items()}
    assert {uid: [m["key"] for m in members] for uid, members in by_host.items()} == \
        {uid: [b.key for b in pieces] for uid, pieces in resolved.items()}

    gltf, _blob = emit_gltf_dict(model)
    nodes = {n["extras"]["uid"]: n for n in gltf["nodes"]
             if n.get("extras", {}).get("facet") == REBAR_FACET}
    assert set(nodes) == set(resolved)
    # A GBox of an F-facet profile de-indexes to 2F side triangles and 2(F-2) cap triangles.
    per_leg = 3 * (2 * _FACETS + 2 * (_FACETS - 2))
    for uid, pieces in resolved.items():
        legs = 0
        for bar in pieces:
            points = len(bar.path)
            if bar.closed and points > 8:
                points = len(bar.path[::_CIRCLE_STRIDE])
            legs += points if bar.closed else points - 1
        vertices = sum(gltf["accessors"][p["attributes"]["POSITION"]]["count"]
                       for p in gltf["meshes"][nodes[uid]["mesh"]]["primitives"])
        assert vertices == legs * per_leg, uid
        assert nodes[uid]["extras"]["trades"] == ["concrete"]
