"""``inspections.toml`` round-trips deterministically, and refuses nonsense loudly."""

from __future__ import annotations

import pytest

from typehaus.schedule.inspection_state import (
    InspectionsState,
    apply_inspection_op,
    load_inspections,
    write_inspections,
)

_SAMPLE = '''
[authorities.building]
label = "Saint Paul DSI"
phone = "651-266-9002"
window = "7:30-9:00 M-F"
lead_days = 1

[entries.footing]
requested = "2027-05-04"
result = "fail"
result_date = "2027-05-05"
history = ["2027-05-05 fail: bolts off plate layout"]
checked = ["permit card posted"]
requires = ["task/concrete/building/footings"]

[[extra]]
id = "girt_screws"
label = "Girt screws verified"
authority = "owner"
after = ["framing"]
gates = ["walls"]
milestone = "weathertight"
'''


def _house(tmp_path, text=_SAMPLE):
    (tmp_path / "inspections.toml").write_text(text)
    return tmp_path


def test_absent_file_is_empty_state(tmp_path) -> None:
    assert load_inspections(tmp_path) == InspectionsState()


def test_loads_all_three_sections(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    assert state.authorities["building"].lead_days == 1
    assert state.entries["footing"].result == "fail"
    assert state.entries["footing"].requires == ("task/concrete/building/footings",)
    assert state.extra[0].gates == ("walls",)
    assert state.extra[0].milestone == "weathertight"


def test_round_trips(tmp_path) -> None:
    directory = _house(tmp_path)
    first = load_inspections(directory)
    write_inspections(directory, first)
    assert load_inspections(directory) == first
    once = (directory / "inspections.toml").read_text()
    write_inspections(directory, load_inspections(directory))
    assert (directory / "inspections.toml").read_text() == once


def test_an_extra_becomes_a_real_spec(tmp_path) -> None:
    spec = load_inspections(_house(tmp_path)).extra[0].as_spec()
    assert spec.id == "girt_screws" and spec.authority == "owner"
    assert spec.gates == ("walls",)


@pytest.mark.parametrize("text,message", [
    ("[entries.footing]\nresult = \"maybe\"\n", "result"),
    ("[entries.footing]\nfinished = \"yes\"\n", "unknown field"),
    ("[authorities.building]\nphone = \"x\"\n", "missing 'label'"),
    ("[[extra]]\nlabel = \"x\"\n", "missing 'id'"),
    ("[wat]\nx = 1\n", "unknown top-level key"),
    ("[entries.footing]\nhistory = \"one line\"\n", "must be an array"),
])
def test_malformed_files_raise_naming_the_key(tmp_path, text, message) -> None:
    with pytest.raises(ValueError, match=message):
        load_inspections(_house(tmp_path, text))


def test_set_inspection_merges_and_clears(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    state = apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                        "result": "pass", "result_date": "2027-05-08"})
    assert state.entries["footing"].result == "pass"
    # A field not named is untouched, which is what makes an optimistic single-field write
    # from a phone safe beside the owner's own editing of the file.
    assert state.entries["footing"].requested == "2027-05-04"
    state = apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                        "result": None})
    assert state.entries["footing"].result is None


def test_set_and_remove_extra(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    state = apply_inspection_op(state, {"op": "set_extra_inspection",
                                        "id": "as_built_survey",
                                        "label": "As-built survey", "gates": ["earth"]})
    assert {x.id for x in state.extra} == {"girt_screws", "as_built_survey"}
    state = apply_inspection_op(state, {"op": "remove_extra_inspection",
                                        "id": "girt_screws"})
    assert {x.id for x in state.extra} == {"as_built_survey"}


def test_bad_ops_raise() -> None:
    with pytest.raises(ValueError, match="unknown inspection op"):
        apply_inspection_op(InspectionsState(), {"op": "set_thing"})
    with pytest.raises(ValueError, match="missing id"):
        apply_inspection_op(InspectionsState(), {"op": "set_inspection"})
    with pytest.raises(ValueError, match="unknown field"):
        apply_inspection_op(InspectionsState(),
                            {"op": "set_inspection", "id": "footing", "duration": 3})


def test_the_catlin_file_loads() -> None:
    """The reference house's own file is the format's first user."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    state = load_inspections(root / "houses" / "catlin")
    assert "building" in state.authorities
    assert state.authorities["electrical"].label.startswith("MN DLI")
    assert [x.id for x in state.extra] == ["girt_screws"]
