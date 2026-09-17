"""P3/P6 — loader-discovered storey modules, ``POST /storeys`` and ``/project`` routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from _helpers import copy_house
from typer.testing import CliRunner

from typehaus.findings import Severity
from typehaus.model.elements import Wall
from typehaus.source.loader import load_plan
from typehaus.source.storey_modules import discover, render_storey_module


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    return copy_house(starter_dir, tmp_path / "starter")


@pytest.fixture
def client(house: Path):
    testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with testclient.TestClient(create_app(house)) as c:
        yield c, house


def _write_module(house: Path, tag: str, uid: str = "STATTCAAAA", stem: str | None = None):
    path = house / "plan" / "storeys" / f"{stem or tag}.py"
    path.write_text(render_storey_module(tag, "ft(18)", "ft(8)", uid))
    return path


def test_rendered_module_is_discovered_and_loads(house: Path) -> None:
    path = _write_module(house, "attic")
    assert discover(house) == [path]  # main.py/upper.py are wired, not discovered
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity is Severity.ERROR]
    assert [s.tag for s in result.plan.storeys] == ["main", "upper", "attic"]
    assert result.plan.storey_elements("attic") == ()


def test_duplicate_storey_tag_is_a_load_error(house: Path) -> None:
    _write_module(house, "upper", uid="STDUPEAAAA", stem="upper_again")
    result = load_plan(house)
    assert any(f.check_id == "loader.storey_duplicate" and f.severity is Severity.ERROR
               for f in result.findings)


def test_render_rejects_a_bad_tag() -> None:
    with pytest.raises(ValueError):
        render_storey_module("Attic", "ft(0)", "ft(8)", "STBADAAAAA")


def test_post_storeys_then_draw_lands_in_the_new_file(client) -> None:
    c, house = client
    res = c.post("/storeys", json={"tag": "attic", "elevation": "18'", "ceiling_height": "8'"})
    assert res.status_code == 200, res.text
    assert (house / "plan" / "storeys" / "attic.py").is_file()
    assert c.post("/storeys", json={"tag": "attic", "elevation": 0,
                                    "ceiling_height": 2}).status_code == 422
    res = c.post("/macro", json={"macro": "draw_room_rect", "storey": "attic", "a": [0, 0],
                                 "b": [4, 3], "assembly": _assembly(house),
                                 "occupancy": "living"})
    assert res.status_code == 200, res.text
    assert any(t.startswith("RM-") for t in res.json()["minted"])
    c.app.state.project._flush_writes()
    plan = load_plan(house).plan
    walls = [e for e in plan.storey_elements("attic") if isinstance(e, Wall)]
    assert len(walls) == 4
    assert "Room(" in (house / "plan" / "storeys" / "attic.py").read_text()


def test_copy_from_copies_the_wall_graph_with_fresh_tags(client) -> None:
    c, house = client
    res = c.post("/storeys", json={"tag": "attic", "elevation": "18'",
                                   "ceiling_height": "8'", "copy_from": "main"})
    assert res.status_code == 200, res.text
    assert res.json()["undo"] == 1
    state = c.app.state.project
    state._flush_writes()
    state._flush_checks()
    plan = state.plan
    main = [e for e in plan.storey_elements("main") if isinstance(e, Wall)]
    attic = [e for e in plan.storey_elements("attic") if isinstance(e, Wall)]
    assert len(attic) == len(main) > 0
    tags = [e.tag for group in plan.elements.values() for e in group]
    assert len(tags) == len(set(tags))
    assert not any(f.check_id == "integrity.stack_ambiguous" for f in state.findings)
    reloaded = load_plan(house)
    assert reloaded.ok, [f.message for f in reloaded.findings
                         if f.severity is Severity.ERROR]
    assert len([e for e in reloaded.plan.storey_elements("attic")
                if isinstance(e, Wall)]) == len(main)


def test_haus_build_accepts_a_discovered_storey(house: Path) -> None:
    from typehaus.cli.app import app

    _write_module(house, "attic")
    result = CliRunner().invoke(app, ["build", str(house)])
    assert result.exit_code == 0, result.output


def test_get_project_reports_the_house(client) -> None:
    c, house = client
    body = c.get("/project").json()
    assert Path(body["house_dir"]) == house.resolve()
    assert body["revision"]
    assert "starter" in body["templates"]
    assert {"add_storey", "project_new", "draw_wall", "copy_storey_layout"} <= set(
        body["capabilities"])


def test_post_project_new_scaffolds_a_loadable_house(client, tmp_path: Path) -> None:
    c, house = client
    target = tmp_path / "fresh"
    res = c.post("/project/new", json={"directory": str(target), "name": "Fresh"})
    assert res.status_code == 200, res.text
    assert res.json()["command"].startswith("haus serve ")
    assert load_plan(target).plan is not None
    # The live server still serves the original house.
    assert Path(c.get("/project").json()["house_dir"]) == house.resolve()
    assert c.post("/project/new", json={"directory": str(target)}).status_code == 422


def test_post_project_new_will_not_write_outside_the_house_root(client, tmp_path: Path) -> None:
    """The route creates directories and writes files, and --host 0.0.0.0 puts it on the LAN.

    New houses land beside the served one. A relative name resolves under that root; an
    absolute path or a ``..`` walk outside it is refused rather than clamped, and so is a
    symlink inside the root that points out of it.
    """
    c, house = client
    outside = tmp_path.parent / "escaped-house"
    for directory in (str(outside), "../escaped-house", f"{house}/../../escaped-house"):
        res = c.post("/project/new", json={"directory": directory})
        assert res.status_code == 422, f"{directory} was allowed: {res.text}"
        assert "outside it" in res.json()["error"]
    assert not outside.exists()

    link = house.parent / "sideways"
    link.symlink_to(tmp_path.parent, target_is_directory=True)
    res = c.post("/project/new", json={"directory": "sideways/escaped-house"})
    assert res.status_code == 422, res.text
    assert not outside.exists()

    # A plain relative name is the ordinary case and still works.
    assert c.post("/project/new", json={"directory": "next-door"}).status_code == 200
    assert (house.parent / "next-door" / "plan" / "manifest.py").is_file()


def _assembly(house: Path) -> str:
    return next(e.assembly for e in load_plan(house).plan.storey_elements("main")
                if isinstance(e, Wall))
