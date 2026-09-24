"""``run_checks(..., only=)`` and the run-scoped ``registry.shared`` memo."""

from __future__ import annotations

import pytest

from typehaus.checks.registry import Tier, registered, run_checks, shared


def test_only_runs_just_the_named_checks(catlin_ctx) -> None:
    report = run_checks(catlin_ctx, Tier.CODE, only="code.site_setback")
    assert report.ran == ("code.site_setback",)
    assert {f.check_id for f in report.findings} == {"code.site_setback"}


def test_only_takes_several_ids_and_keeps_registry_order(catlin_ctx) -> None:
    ids = [cid for cid, _ in registered(Tier.CODE)][:3]
    report = run_checks(catlin_ctx, Tier.CODE, only=reversed(ids))
    assert report.ran == tuple(ids)


def test_only_rejects_an_unregistered_id(catlin_ctx) -> None:
    """A typo would otherwise make every ``assert not matched`` pass without running."""
    with pytest.raises(ValueError, match="code.site_setbak"):
        run_checks(catlin_ctx, Tier.CODE, only="code.site_setbak")


def test_only_rejects_an_id_from_another_tier(catlin_ctx) -> None:
    advisory = next(cid for cid, _ in registered(Tier.ADVISORY))
    with pytest.raises(ValueError, match=advisory):
        run_checks(catlin_ctx, Tier.CODE, only=advisory)


def test_shared_is_a_plain_call_outside_a_run(catlin_ctx) -> None:
    calls: list[int] = []
    for _ in range(2):
        shared(catlin_ctx, "k", lambda: calls.append(1))
    assert len(calls) == 2


def test_shared_computes_once_per_run_and_forgets_after(catlin_ctx, monkeypatch) -> None:
    import typehaus.checks.registry as registry

    calls: list[int] = []

    def probe(ctx):
        for _ in range(3):
            shared(ctx, "probe", lambda: calls.append(1))
        return []

    monkeypatch.setitem(registry._REGISTRY, Tier.CODE, [("probe.one", probe),
                                                         ("probe.two", probe)])
    run_checks(catlin_ctx, Tier.CODE)
    assert len(calls) == 1
    run_checks(catlin_ctx, Tier.CODE)
    assert len(calls) == 2
