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
checked = ["permit card posted"]
requires = ["task/concrete/building/footings"]
attempts = [
  { date = "2027-05-05", result = "fail", corrections = ["bolts off plate layout"] },
]

[entries."footing/court"]
scope = ["FT-SG-*"]
requested = "2027-06-01"

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
    assert state.entries["footing"].attempts[0].corrections == ("bolts off plate layout",)
    # A second instance of the same spec, with its own scope and its own booking.
    assert state.instances("footing") == {
        "footing": state.entries["footing"], "footing/court": state.entries["footing/court"]}
    assert state.entries["footing/court"].scope == ("FT-SG-*",)
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
    ("[entries.footing]\nattempts = [{ date = \"d\", result = \"maybe\" }]\n", "result"),
    ("[entries.footing]\nattempts = [{ date = \"d\", result = \"partial\" }]\n",
     "must name the scope"),
    ("[entries.footing]\nresult = \"pass\"\n", "old single-result spelling"),
    ("[entries.footing]\nwaived = \"DSI said so\"\n", "who granted it"),
    ("[entries.footing]\nfinished = \"yes\"\n", "unknown field"),
    ("[authorities.building]\nphone = \"x\"\n", "missing 'label'"),
    ("[[extra]]\nlabel = \"x\"\n", "missing 'id'"),
    ("[wat]\nx = 1\n", "unknown top-level key"),
    ("[entries.footing]\nattempts = \"one line\"\n", "must be an array"),
])
def test_malformed_files_raise_naming_the_key(tmp_path, text, message) -> None:
    with pytest.raises(ValueError, match=message):
        load_inspections(_house(tmp_path, text))


def test_set_inspection_merges_and_clears(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    state = apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                        "scheduled": "2027-05-08"})
    assert state.entries["footing"].scheduled == "2027-05-08"
    # A field not named is untouched, which is what makes an optimistic single-field write
    # from a phone safe beside the owner's own editing of the file.
    assert state.entries["footing"].requested == "2027-05-04"
    state = apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                        "scheduled": None})
    assert state.entries["footing"].scheduled is None


def test_a_result_only_ever_arrives_as_an_attempt(tmp_path) -> None:
    """The failure this replaces: a second call overwrote the first one's card."""
    state = load_inspections(_house(tmp_path))
    with pytest.raises(ValueError, match="add_attempt"):
        apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                    "result": "pass"})
    state = apply_inspection_op(state, {"op": "add_attempt", "id": "footing",
                                        "date": "2027-05-08", "result": "partial",
                                        "approved": ["FT-B-*"]})
    state = apply_inspection_op(state, {"op": "add_attempt", "id": "footing",
                                        "date": "2027-05-12", "result": "pass"})
    entry = state.entries["footing"]
    assert [a.result for a in entry.attempts] == ["fail", "partial", "pass"]
    assert entry.result == "pass"


def test_a_fail_clears_the_booking_rather_than_keeping_a_reinspect_field(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    state = apply_inspection_op(state, {"op": "set_inspection", "id": "footing",
                                        "scheduled": "2027-05-08"})
    state = apply_inspection_op(state, {"op": "add_attempt", "id": "footing",
                                        "date": "2027-05-08", "result": "fail"})
    assert state.entries["footing"].scheduled is None


def test_an_instance_needs_a_scope(tmp_path) -> None:
    state = load_inspections(_house(tmp_path))
    with pytest.raises(ValueError, match="needs a 'scope'"):
        apply_inspection_op(state, {"op": "set_instance", "id": "slab/garage"})
    with pytest.raises(ValueError, match="instance id"):
        apply_inspection_op(state, {"op": "set_instance", "id": "slab",
                                    "scope": ["SL-G-*"]})
    state = apply_inspection_op(state, {"op": "set_instance", "id": "slab/garage",
                                        "scope": ["SL-G-*"]})
    assert state.entries["slab/garage"].scope == ("SL-G-*",)


def test_the_permit_block_holds_the_code_editions(tmp_path) -> None:
    state = apply_inspection_op(load_inspections(_house(tmp_path)),
                                {"op": "set_permit", "code_edition": "mn-2020",
                                 "nec_edition": "2026"})
    assert state.permit.code_edition == "mn-2020"
    assert state.permit.nec_edition == "2026"


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
    # Saint Paul runs its own electrical inspections on its own number.
    assert state.authorities["electrical"].phone == "651-266-9003"
    assert [x.id for x in state.extra] == ["girt_screws"]
