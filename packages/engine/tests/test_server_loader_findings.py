"""Loader findings must survive the resolve+checks pipeline and reach the client.

`rebuild()` collected them and `_resolve_and_check` then overwrote `self.findings` with the
resolve findings alone, so `loader.uneditable_movable_element` — the error explaining why a
drag will not persist — never reached `GET /model`. The fast edit path zeroed them too.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _loader_errors(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f["check_id"] == "loader.uneditable_movable_element"]


@pytest.fixture
def uneditable_house(tmp_path: Path) -> Path:
    dst = tmp_path / "catlin"
    shutil.copytree(CATLIN, dst)
    mep = dst / "plan" / "mep.py"
    mep.write_text(mep.read_text().replace("# haus: editable\n", "", 1))
    return dst


@pytest.fixture
def client(uneditable_house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(uneditable_house)) as c:
        yield c, uneditable_house


def test_loader_findings_reach_the_model_endpoint(client) -> None:
    c, _ = client
    model = c.get("/model").json()
    errs = _loader_errors(model["findings"])
    assert errs, "loader error was swallowed by the resolve/checks overwrite"
    assert model["ok"] is False


def test_loader_findings_survive_a_fast_edit(client) -> None:
    """The fast path never reloads source, so the load-time findings still hold — dropping
    them would make the error blink out until the next full rebuild."""
    c, _ = client
    model = c.get("/model").json()
    wall = model["walls"][0]
    resp = c.patch("/plan", json={
        "revision": model["revision"],
        "ops": [{"op": "update", "type": "Wall", "tag": wall["tag"], "fields": {}}],
    })
    assert resp.status_code == 200, resp.text
    after = c.get("/model").json()
    assert _loader_errors(after["findings"])


def test_clean_house_has_no_loader_errors(starter_dir: Path, tmp_path: Path) -> None:
    """The merge is behavior-neutral for the shipped houses: neither carries a loader ERROR,
    so nothing that passed before starts failing on `ok`."""
    from typehaus.findings import Severity
    from typehaus.source import load_plan

    for house in (starter_dir, CATLIN):
        result = load_plan(house)
        errs = [f for f in result.findings if f.severity is Severity.ERROR]
        assert not errs, (house.name, [f.check_id for f in errs])
