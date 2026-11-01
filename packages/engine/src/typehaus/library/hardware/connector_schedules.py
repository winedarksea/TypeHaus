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

from typehaus.hardware.connector_fastening import ConnectorFastening

HDG_8D = "8d common 0.131x2.5"
HDG_10D = "10d common 0.148x3"
HDG_16D = "16d common 0.162x3.5"
HDG_0131_15 = "0.131x1.5 connector nail"
HDG_0148_15 = "0.148x1.5 connector nail"

_CC = "Simpson Strong-Tie C-C-2026"
_RECORD = "transcribed from the catalog record's AllowableLoads.fasteners"


def _pair(count: int, model: str, first: str, second: str) -> tuple:
    return ((count, model, first), (count, model, second))


CONNECTOR_FASTENERS: dict[str, ConnectorFastening] = {
    # A 1-1/4 x 7-1/4 rim in the LUS family: the 2x8-depth (LUS28) row.
    "LUSZ": ConnectorFastening("zmax", ((6, HDG_10D, "header"), (4, HDG_10D, "joist")),
                               f"{_CC} pp.113-114, LUS28 row (rim at 2x8 depth)"),
    "LUS28Z": ConnectorFastening("zmax", ((6, HDG_10D, "header"), (4, HDG_10D, "joist")),
                                 f"{_CC} pp.113-114, LUS28 row"),
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
    "CBSQ66-SDS2": ConnectorFastening(
        "hdg", (), f"{_CC} p.84: the -SDS2 model ships with its (14) SDS 1/4 x 2 screws"),
    "DTT2Z": ConnectorFastening(
        "zmax", (), f"{_CC} p.60: \"Fasteners and crescent washer are included\" (8 SDS25112)"),
    # Bolted: the bolt length is the member's, so it is a site purchase, not a count here.
    "HL33HDG": ConnectorFastening("hdg", (), _RECORD + " — (2) 1/2 in through-bolts"),
    "HL43HDG": ConnectorFastening("hdg", (), _RECORD + " — (2) 3/4 in through-bolts"),
}
