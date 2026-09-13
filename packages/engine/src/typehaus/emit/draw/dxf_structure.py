"""3-D centreline DXF of the analytical model — the file RISA-3D actually reads.

RISA-3D imports no IFC (plan 31 §2). What it does read is a DXF of member centrelines:
one ``LINE`` per member, one ``POINT`` per node, and the **layer name taken as the section
set name** on import. Its import dialog picks the length unit and offers a rotate-to-Y-up,
so this writes what the rest of the bundle uses — **inches, Z up** — and lets the dialog do
the rotation rather than baking a permutation nobody downstream can see.

Loads are **not drawn**. A DXF has no load entity; a line pretending to be one imports as a
member. The load cases live in the PyNite script, the CSV and the IFC, and a ``NOTES`` text
in the drawing says so, next to the units, the axis convention, the assumptions and the gaps.

Byte-deterministic. ezdxf stamps ``$VERSIONGUID`` and two ``created/written by ezdxf``
timestamps at save time, inside ``Drawing.update_all()``, so they cannot be pinned before
the write; ``_normalise`` replaces them in the emitted text instead. Handles are stable
because every entity is added in a sorted, fixed order.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from typehaus.analytical.graph import AnalyticalModel, Member
from typehaus.analytical.pynite_map import M_TO_IN, section_name, support_label

LAYER_NODES = "NODES"
LAYER_LABELS = "LABELS"
LAYER_SUPPORTS = "SUPPORTS"
LAYER_NOTES = "NOTES"

#: Text sizes in model inches. A building is tens of feet across in these units, so 3" is a
#: legible member label and 6" a heading — the same ratio a 1/4" sheet uses.
_LABEL_HEIGHT_IN = 3.0
_NOTE_HEIGHT_IN = 6.0
#: Notes stack below the model, clear of it by one line.
_NOTE_PITCH_IN = 9.0

_NIL_GUID = "{00000000-0000-0000-0000-000000000000}"
_EZDXF_MARKER = re.compile(r"^\d+\.\d+[\w.]* @ \d{4}-\d\d-\d\dT[\d:.+\-]+$")
_EZDXF_MARKER_PINNED = "typehaus-deterministic"
_GUID_HEADER_VARS = ("$FINGERPRINTGUID", "$VERSIONGUID")
_DATE_HEADER_VARS = ("$TDCREATE", "$TDUCREATE", "$TDUPDATE", "$TDUUPDATE")
_EPOCH_JULIAN = 2444239.5  # 1980-01-01, the same pin the handoff zip uses


def write_structure_dxf(model: AnalyticalModel, path: Path) -> Path:
    import ezdxf

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 1          # inches, matching the rest of the bundle
    for var in _GUID_HEADER_VARS:
        doc.header[var] = _NIL_GUID
    # ezdxf stamps the wall clock as a Julian date in four header variables; the update pair
    # is re-stamped during `write`, so `_normalise` also catches it. Two writes a second apart
    # differed here and nowhere else (the handoff manifest is what noticed).
    for var in _DATE_HEADER_VARS:
        doc.header[var] = _EPOCH_JULIAN
    for name in _layer_names(model):
        doc.layers.add(name)

    msp = doc.modelspace()
    for node in sorted(model.nodes, key=lambda n: n.id):
        msp.add_point(_xyz(node.xyz), dxfattribs={"layer": LAYER_NODES})
    for member in sorted(model.members, key=lambda m: m.id):
        _add_member(msp, model, member)
    for support in sorted(model.supports, key=lambda s: (s.node, s.fixity.value)):
        msp.add_text(
            support_label(support, " ").upper(),   # "FIXED", "PINNED", "PINNED RX"
            dxfattribs={"layer": LAYER_SUPPORTS, "height": _LABEL_HEIGHT_IN,
                        "insert": _xyz(model.node(support.node).xyz)},
        )
    _add_notes(msp, model)

    path.parent.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    doc.write(stream)
    path.write_text(_normalise(stream.getvalue()), encoding="utf-8", newline="\n")
    return path


def _layer_names(model: AnalyticalModel) -> tuple[str, ...]:
    sections = {section_name(m) for m in model.members}
    return tuple(sorted(sections | {LAYER_NODES, LAYER_LABELS, LAYER_SUPPORTS, LAYER_NOTES}))


def _add_member(msp, model: AnalyticalModel, member: Member) -> None:
    a, b = model.node(member.n0).xyz, model.node(member.n1).xyz
    layer = section_name(member)
    msp.add_line(_xyz(a), _xyz(b), dxfattribs={"layer": layer})
    items = " ".join(member.item_ids) or "(no engineering item)"
    msp.add_text(
        f"{member.id} | {layer} | {items}",
        dxfattribs={
            "layer": LAYER_LABELS,
            "height": _LABEL_HEIGHT_IN,
            "insert": _xyz(tuple((p + q) / 2.0 for p, q in zip(a, b, strict=True))),
        },
    )


def _add_notes(msp, model: AnalyticalModel) -> None:
    """The header block: what the file is, and every claim it carries, one TEXT per line."""
    lines = [
        "TYPE:HAUS ANALYTICAL CENTRELINE MODEL",
        "UNITS: INCHES ($INSUNITS=1). AXES: X, Y, Z WITH Z UP (RISA IMPORT CAN ROTATE TO Y UP).",
        "LAYER PER MEMBER = SECTION SET NAME. LINE = MEMBER, POINT = NODE.",
        "LOADS ARE NOT DRAWN - SEE members.csv AND model.pynite.py FOR THE LOAD CASES.",
        f"SCOPE: {', '.join(model.scope) if model.scope else '(none recorded)'}",
    ]
    lines += [f"ASSUMPTION: {line}" for line in model.assumptions]
    lines += [f"GAP: {line}" for line in model.gaps]

    x0 = min((n.x_m for n in model.nodes), default=0.0) * M_TO_IN
    y0 = min((n.y_m for n in model.nodes), default=0.0) * M_TO_IN
    for index, line in enumerate(lines):
        msp.add_text(line, dxfattribs={
            "layer": LAYER_NOTES, "height": _NOTE_HEIGHT_IN,
            "insert": (x0, y0 - (index + 1) * _NOTE_PITCH_IN, 0.0),
        })


def _xyz(point: tuple[float, ...]) -> tuple[float, float, float]:
    x, y, z = point
    return (x * M_TO_IN, y * M_TO_IN, z * M_TO_IN)


#: Sections whose records ezdxf does not emit in a stable order between processes.
#: **CLASSES only.** The OBJECTS section drifts too, but its first record must be the root
#: DICTIONARY — sorting it makes a file ezdxf itself refuses to read back ("invalid root
#: dictionary entity"). A CLASS record is reached by name and has no such rule.
_SORTED_SECTIONS = ("CLASSES",)


def _sort_records(lines: list[str], section: str) -> list[str]:
    """Put one section's top-level records in a canonical order.

    ezdxf emits the boilerplate it builds for a new drawing — the registered CLASS records,
    the layout dictionary and its plot-style placeholder — in an order that is **not stable
    between processes**: roughly one write in two swaps ``LAYOUT`` with ``ACDBPLACEHOLDER``.
    Nothing downstream cares, because a DXF reader reaches a class by name and an object by
    handle rather than by position, but the handoff manifest cares very much — a bundle
    whose sha256 changes on a re-run stops being evidence that the model changed.

    So each of these sections is re-emitted sorted by its records' own content. Only whole
    records move; the tags inside one keep the order ezdxf wrote them in.
    """
    try:
        start = next(i for i in range(len(lines) - 3)
                     if lines[i].strip() == "SECTION" and lines[i + 2].strip() == section)
    except StopIteration:
        return lines
    body = start + 3                       # first line after the "  2 / <section>" pair
    end = next(i for i in range(body, len(lines)) if lines[i].strip() == "ENDSEC")
    # A DXF tag stream is strictly (group code, value) pairs, so the parity from the start
    # of the section is what says whether a "0" line is a code or a value — testing the line
    # before it is not enough, because "0" is a perfectly ordinary VALUE (every 281 flag in
    # a CLASS record is one) and that misreading shifts every record by a line.
    records: list[list[str]] = []
    for index in range(body, end - 1, 2):
        if lines[index].strip() == "0":
            records.append([])
        if records:
            records[-1].extend(lines[index:index + 2])
    if not records:
        return lines
    ordered = [line for record in sorted(records, key=tuple) for line in record]
    return lines[:body] + ordered + lines[end - 1:]


def _normalise(text: str) -> str:
    """Strip the three things ezdxf writes fresh on every save.

    ``$VERSIONGUID`` is regenerated inside ``update_all()`` during the write, the ezdxf
    metadata dictionary carries ``<version> @ <ISO timestamp>`` markers, and ``$TDUPDATE``
    is the wall clock. All three are pure
    provenance; neither changes what any reader imports. Working on the emitted tag stream
    is the only place they can be reached, so the pass is line-based on the DXF group codes:
    a GUID line is the one after a GUID header variable name, and a marker line matches its
    own shape exactly.
    """
    out: list[str] = []
    pending_guid = False
    pending_date = False
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        stripped = line.strip()
        if stripped in _GUID_HEADER_VARS:
            pending_guid = True          # the value follows two group-code lines later
        elif stripped in _DATE_HEADER_VARS:
            pending_date = True          # $TDUPDATE is re-stamped inside `write`
        elif pending_guid and stripped.startswith("{") and stripped.endswith("}"):
            out.append(_NIL_GUID)
            pending_guid = False
            continue
        elif pending_date and "." in stripped and stripped.replace(".", "", 1).isdigit():
            # a Julian date has a decimal point; the bare " 40" group code before it does not
            out.append(f"{_EPOCH_JULIAN}")
            pending_date = False
            continue
        elif stripped.startswith("$"):
            pending_guid = pending_date = False   # a different header variable intervened
        out.append(_EZDXF_MARKER_PINNED if _EZDXF_MARKER.match(stripped) else line)
    for section in _SORTED_SECTIONS:
        out = _sort_records(out, section)
    return "\n".join(out) + "\n"
