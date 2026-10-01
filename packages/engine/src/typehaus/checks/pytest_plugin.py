"""pytest plugin — parametrizes the checks registry so `pytest` runs every check as a
test, guaranteeing identical findings to `haus check` (→ 12 §Dual invocation).

Discovery: a house dir is taken from the ``TYPEHAUS_HOUSE`` env var (set by CI / the
agent loop); absent, the plugin is inert so unit tests are unaffected.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from typehaus.checks.registry import CheckContext, _suppressed, registered
from typehaus.checks.run import build_context
from typehaus.findings import Result, Severity
from typehaus.source import load_plan


def _house_dir() -> Path | None:
    env = os.environ.get("TYPEHAUS_HOUSE")
    return Path(env) if env else None


def _accepted_hard_findings() -> set[tuple[str, tuple[str, ...]]]:
    """Exact ERROR findings the active house gate has chosen to leave visible.

    This is a test-gate exception only. ``haus check`` still emits every finding, and its
    JSON gate separately asserts that each accepted identity is present in the report.
    """
    raw = os.environ.get("TYPEHAUS_ACCEPTED_CHECK_FINDINGS", "[]")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise pytest.UsageError("TYPEHAUS_ACCEPTED_CHECK_FINDINGS must be JSON") from exc
    if not isinstance(entries, list):
        raise pytest.UsageError("TYPEHAUS_ACCEPTED_CHECK_FINDINGS must be a JSON list")

    accepted: set[tuple[str, tuple[str, ...]]] = set()
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"check_id", "element_tags"}
                or not isinstance(entry["check_id"], str)
                or not isinstance(entry["element_tags"], list)
                or not all(isinstance(tag, str) for tag in entry["element_tags"])):
            raise pytest.UsageError(
                "each accepted finding needs string check_id and element_tags fields")
        accepted.add((entry["check_id"], tuple(sorted(entry["element_tags"]))))
    return accepted


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
    # Match run_checks: a house's authored suppressions apply to each rule's findings.
    findings = [
        finding for finding in registered_check(_check_context)
        if not _suppressed(finding, _check_context.preferences.suppressed)
    ]
    hard = [
        f for f in findings
        if f.severity is Severity.ERROR and f.result is Result.FAIL
    ]
    accepted = _accepted_hard_findings()
    unexpected = [
        f for f in hard
        if (f.check_id, tuple(sorted(f.element_tags or ()))) not in accepted
    ]
    assert not unexpected, "\n".join(f.render() for f in unexpected)
