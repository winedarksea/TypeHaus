"""Custom-milled framing reaches the milling schedule (→ takeoff/hardwood_framing.py)."""

from types import SimpleNamespace

from typehaus.model import Material
from typehaus.resolve.model import FramedMember
from typehaus.takeoff.hardwood_framing import framing_rows

M = 0.0254


def _member(key, category, material, length_in=14.5):
    return FramedMember("W1", key, category, "2x6", (0.0, 0.0), (length_in * M, 0.0),
                        0.0, 1.5 * M, length_in * M, material=material)


def test_oak_blocks_are_cut_listed_and_ordinary_framing_is_not():
    materials = {
        "oak": Material(tag="oak", name="Oak 8/4", requires_custom_milling=True,
                        nominal_quarters=8),
        "kdat": Material(tag="kdat", name="KDAT"),
    }
    members = [_member(f"blocking-0-{i:03d}", "blocking", "oak") for i in range(3)]
    members += [_member("blocking-1-000", "blocking", "oak", 2.75),
                _member("plate-bottom", "plate", "kdat", 96.0),
                _member("stud-000", "stud", None, 96.0)]
    model = SimpleNamespace(walls=[SimpleNamespace(uid="W1", tag="W-TEST")], stairs=[],
                            all_members=lambda: members)
    rows = framing_rows(model, materials, 9.0)
    assert {(r["use"], r["material"], r["pieces"]) for r in rows} == {
        ("blocking", "oak", 3), ("blocking", "oak", 1)}
    assert all(r["also_in_framing"] for r in rows)
    assert all(r["tags"] == ["W-TEST"] for r in rows)
