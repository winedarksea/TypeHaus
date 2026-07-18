"""WP1.2 tests — closed arithmetic, parse∘fmt and to_source→eval round-trips."""

from __future__ import annotations

from typehaus.quantities import Length, Pitch, deg, ft, inch, m, mm, r_us


def test_closed_arithmetic() -> None:
    assert (ft(12, 6) + inch(6)).fmt() == "13'-0\""
    assert round((ft(10) - ft(3)).feet, 6) == 7.0
    area = ft(4).times_length(ft(3))
    assert round(area.sq_ft, 3) == 12.0


def test_unit_preservation_through_source() -> None:
    for q in (ft(12, 6), inch(6), mm(1000), m(3)):
        assert type(eval(q.to_source(), {"ft": ft, "inch": inch, "mm": mm, "m": m})) is Length


def test_parse_roundtrip() -> None:
    for text in ("12'-6\"", "48\"", "12'-6 1/2\""):
        parsed = Length.parse(text)
        assert Length.parse(parsed.fmt()) == parsed


def test_pitch_to_angle() -> None:
    assert round(Pitch(rise=12, run=12).to_angle().degrees, 1) == 45.0


def test_r_value_canonical() -> None:
    assert round(r_us(40).r_us, 1) == 40.0
    assert deg(90).radians > 1.5
