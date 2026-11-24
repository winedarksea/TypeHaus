"""Connector fastener schedules: what each coated or stainless connector is nailed with.

Decision #105. Keyed by the EXACT billed part designation. Counts are transcribed from the
record's own ``AllowableLoads.fasteners`` where it has one, otherwise from Simpson C-C-2026;
where the catalog prints Min and Max, Max is billed (the count a "can't be cheaped out"
order has to cover). Zinc connectors take HDG (IRC R317.3.1: a G90 nail through a ZMAX tie
into treated wood is the same corrosion cell); stainless ones take stainless (L-F-SSNAILS
line 1). Out of scope, on purpose: G90 parts into dry SPF (LTP4, SP4/SP6, STHD, MSTC52, the
house-ridge LSTA24) — their nails are commodity and ride in the framing rate.
"""

from __future__ import annotations

from typehaus.hardware.connector_fastening import ConnectorFastening, SiteBolt
from typehaus.library.hardware.ties import HL33HDG_HEAVY_ANGLE, HL43HDG_HEAVY_ANGLE

HDG_8D = "8d common 0.131x2.5"
HDG_10D = "10d common 0.148x3"
HDG_16D = "16d common 0.162x3.5"
HDG_0131_15 = "0.131x1.5 connector nail"
HDG_0148_15 = "0.148x1.5 connector nail"
HDG_0148_25 = "10d short common 0.148x2.5"

_CC = "Simpson Strong-Tie C-C-2026"
_RECORD = "transcribed from the catalog record's AllowableLoads.fasteners"


def _hl_bolts(angle) -> tuple[SiteBolt, ...]:
    dia, per = angle.bolt_diameter_in, angle.bolts_per_leg
    return (SiteBolt(dia, per, 0, "bolt"), SiteBolt(dia, per, 1, "lag", min_length_in=5.0))


def _pair(count: int, model: str, first: str, second: str) -> tuple:
    return ((count, model, first), (count, model, second))


CONNECTOR_FASTENERS: dict[str, ConnectorFastening] = {
    # A 1-1/4 x 7-1/4 rim in the LUS family: the 2x8-depth (LUS28) row.
    "LUSZ": ConnectorFastening("zmax", ((6, HDG_10D, "header"), (4, HDG_10D, "joist")),
                               f"{_CC} pp.113-114, LUS28 row (rim at 2x8 depth)"),
    "LUS28Z": ConnectorFastening("zmax", ((6, HDG_10D, "header"), (4, HDG_10D, "joist")),
                                 f"{_CC} pp.113-114, LUS28 row"),
    # On a 4x4 post a 3 1/2" header nail meets the opposite face's hanger: SD screws, p.26.
    "LUC26Z": ConnectorFastening(
        "zmax", ((6, "SD10112", "header"), (4, "SD9112", "joist")), _RECORD),
    "LUC210Z": ConnectorFastening(
        "zmax", ((10, "SD10112", "header"), (6, "SD9112", "joist")), _RECORD),
    "LUS26-2Z": ConnectorFastening(
        "zmax", ((4, HDG_16D, "header"), (4, HDG_16D, "joist")), _RECORD),
    "LUS210-3Z": ConnectorFastening(
        "zmax", ((8, HDG_16D, "header"), (6, HDG_16D, "joist")), _RECORD),
    "LUS210SS": ConnectorFastening(
        "ss316", ((8, "SSA10D", "header"), (4, "SSA10D", "joist")),
        _RECORD + " (SCNR for the catalog's 0.148 x 3)"),
    "LSCZ": ConnectorFastening(
        "zmax", ((8, HDG_0148_15, "rim"), (8, HDG_0148_15, "stringer wide face"),
                 (1, HDG_0148_15, "stringer narrow face")), f"{_CC} p.321; " + _RECORD),
    # 1-1/2" header nails: opposing hangers share the 3-1/2" ridge (ridge_beam_detail.md).
    "LSSR2.37Z": ConnectorFastening(
        "zmax", ((14, HDG_0148_15, "header"), (12, HDG_0148_15, "joist")),
        f"{_CC} p.178 sloped-only (14) 0.148x1-1/2 header row; " + _RECORD),
    "HU28-2Z": ConnectorFastening(
        "zmax", ((14, HDG_16D, "header"), (6, HDG_10D, "joist")),
        f"{_CC} p.114, HU28-2 Max installation"),
    "H2.5AZ": ConnectorFastening("zmax", _pair(5, HDG_8D, "rafter/joist", "plates"), _RECORD),
    "H2.5ASS": ConnectorFastening("ss316", _pair(5, "SSA8D", "rafter", "plates"), _RECORD),
    "H10ASS": ConnectorFastening("ss316", _pair(9, "SSNA10D", "joist", "beam"), _RECORD),
    "HETA20Z": ConnectorFastening("zmax", ((6, HDG_16D, "member"),),
                                  _RECORD + " (6 per strap; the cast leg takes none)"),
    "ACE6Z": ConnectorFastening("zmax", _pair(10, HDG_16D, "beam", "post"),
                                _RECORD + " (MAX nailing)"),
    "A35Z": ConnectorFastening("zmax", _pair(6, "SD9112", "leg 1", "leg 2"), _RECORD),
    "LTP4Z": ConnectorFastening("zmax", _pair(6, HDG_0131_15, "block", "header"), _RECORD),
    "KBS1Z": ConnectorFastening("zmax", ((12, HDG_8D, "brace and post"),), _RECORD),
    "LS30Z": ConnectorFastening("zmax", _pair(3, HDG_0148_15, "leg 1", "leg 2"), _RECORD),
    # Every nail lands in the pt-syp sill, so the strap is ZMAX too (R317.3.1).
    "MASAZ": ConnectorFastening(
        "zmax", ((3, HDG_0148_15, "sill sides"), (6, HDG_0148_15, "sill top")),
        f"{_CC} p.34, standard installation, 2x sill"),
    "SP4Z": ConnectorFastening("zmax", ((6, HDG_0148_15, "stud"),),
                               f"{_CC}, SP4: (6) 0.148 x 1-1/2 into the stud"),
    # Plain ABU44 is ZMAX: the catalog lists only ABU44Z (C-C-2026 p.76).
    "ABU44": ConnectorFastening("zmax", ((12, HDG_16D, "post"),),
                                f"{_CC} pp.76-77, ABU44Z: (12) 0.162 x 3-1/2 into the post"),
    "CBSTQ66Z-SDS2": ConnectorFastening(
        "zmax", (), f"{_CC} p.84: the -SDS2 model ships with its (14) SDS 1/4 x 2 screws"),
    "DTT2Z": ConnectorFastening(
        "zmax", (), f"{_CC} p.60: \"Fasteners and crescent washer are included\" (8 SDS25112)"),
    # A straight strap: half the nails in each member (General Note d), 2-1/2" over the ZIP
    # (Note b). The landing's collector (params/landing_tie.py).
    "MSTA49Z": ConnectorFastening(
        "zmax", _pair(13, HDG_0148_25, "screen top plate", "W-G-W nailer"),
        f"{_CC} p.290, MSTA49 row: (26) 0.148x2-1/2; p.288 General Notes b, d"),
    # Bolted (decision #147): a through-bolt in the tied member (connects[0]), its length
    # derived from the grip (``takeoff/site_bolts.py``); a lag into the structure tied to
    # (connects[1]), HL fn 7's >= 5".
    "HL33HDG": ConnectorFastening(
        "hdg", (), _RECORD + " — (1) 1/2 in through-bolt + (1) 1/2 in lag >= 5 in (fn 7)",
        site_bolts=_hl_bolts(HL33HDG_HEAVY_ANGLE)),
    "HL43HDG": ConnectorFastening(
        "hdg", (), _RECORD + " — (1) 3/4 in through-bolt + (1) 3/4 in lag >= 5 in (fn 7)",
        site_bolts=_hl_bolts(HL43HDG_HEAVY_ANGLE)),
}
