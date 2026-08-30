"""pytest plugin — parametrizes the checks registry so `pytest` runs every check as a
test, guaranteeing identical findings to `haus check` (→ 12 §Dual invocation).

Discovery: a house dir is taken from the ``TYPEHAUS_HOUSE`` env var (set by CI / the
agent loop); absent, the plugin is inert so unit tests are unaffected.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from typehaus.checks.registry import CheckContext, registered
from typehaus.checks.run import build_context
from typehaus.findings import Result, Severity
from typehaus.source import load_plan


def _house_dir() -> Path | None:
    env = os.environ.get("TYPEHAUS_HOUSE")
    return Path(env) if env else None


@pytest.fixture(scope="session")
def _check_context() -> CheckContext | None:
    house = _house_dir()
    if house is None:
        return None
    result = load_plan(house)
    if not result.ok or result.plan is None:
        pytest.fail(f"plan failed to load: {[f.render() for f in result.findings]}")
    ctx, _ = build_context(result.plan, house)
    return ctx


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "registered_check" in metafunc.fixturenames:
        checks = registered()
        metafunc.parametrize(
            "registered_check", [fn for _cid, fn in checks],
            ids=[cid for cid, _fn in checks],
        )


def test_registered_check(registered_check, _check_context) -> None:  # type: ignore[no-untyped-def]
    """Each registered check runs; ERROR-severity FAIL findings fail the test."""
    if _check_context is None:
        pytest.skip("set TYPEHAUS_HOUSE to run engine checks as tests")
    findings = registered_check(_check_context)
    hard = [
        f for f in findings
        if f.severity is Severity.ERROR and f.result is Result.FAIL
    ]
    assert not hard, "\n".join(f.render() for f in hard)
