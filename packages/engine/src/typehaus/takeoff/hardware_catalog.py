"""The catalog record for a piece of structural connection hardware, plus its lookups.

The *type* lives in the engine and the *items* live in ``library/hardware.py`` — the same
split as ``Material`` / ``library/materials.py``. A take-off derives a role ("this joint
needs a sloped joist hanger, 10 in of screw"); the catalog is what turns that role into a
manufacturer part number with a citable source.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Stable role keys the take-off selects hardware by. A role is a *condition* in the resolved
# model, never a product: several products may serve one role, and the catalog decides.
ROLE_EXTERIOR_INSULATION_SCREW = "exterior_insulation_screw"
ROLE_SLOPED_JOIST_HANGER = "sloped_joist_hanger"
ROLE_FACE_MOUNT_JOIST_HANGER = "face_mount_joist_hanger"
ROLE_CONCRETE_FACE_MOUNT_HANGER = "concrete_face_mount_hanger"
ROLE_KNEE_BRACE = "knee_brace"
ROLE_MUDSILL_ANCHOR = "mudsill_anchor"
ROLE_EMBEDDED_STRAP_HOLDOWN = "embedded_strap_holdown"
ROLE_STUD_PLATE_TIE = "stud_plate_tie"
ROLE_COIL_STRAP = "coil_strap"
ROLE_POST_BASE = "post_base"
ROLE_HURRICANE_TIE = "hurricane_tie"
ROLE_STANDING_SEAM_CLAMP = "standing_seam_clamp"


@dataclass(frozen=True)
class StructuralHardware:
    """One catalog connector/fastener: a stable tag, a role, a part number, and a source."""

    tag: str                      # stable catalog id, e.g. "simpson-masa-mudsill-anchor"
    name: str                     # human name for the BOM line
    role: str                     # one of the ROLE_* keys above
    manufacturer: str
    model: str                    # published part/family designation, e.g. "MASA"
    source: str                   # the manufacturer system/product this record describes
    unit: str = "each"            # purchase unit ("each" | "coil")
    # Length-selected fasteners: available lengths mapped to their published part numbers.
    part_number_by_length_in: dict = field(default_factory=dict)
    # Nominal member sizes this part is published for (empty = size-independent).
    fits_nominal: tuple = ()

    @property
    def available_lengths_in(self) -> tuple:
        return tuple(sorted(self.part_number_by_length_in))


def structural_hardware_catalog() -> tuple:
    """The shared ``library/hardware.py`` catalog.

    Imported lazily: the engine package must import without the repo-root ``library``
    package on ``sys.path`` (the plan loader puts it there when a house is loaded).
    """
    from library.hardware import STRUCTURAL_HARDWARE

    return STRUCTURAL_HARDWARE


def hardware_for_role(role: str) -> StructuralHardware:
    """The single catalog item serving ``role``, or raise — a BOM line without a part is
    not a bill of materials, so an unserved role is a catalog bug, not a silent blank."""
    items = [item for item in structural_hardware_catalog() if item.role == role]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r}, "
                          f"found {[item.tag for item in items]}")
    return items[0]


def hardware_for_role_and_nominal(role: str, nominal: str) -> StructuralHardware:
    """The catalog item serving ``role`` for a nominal member size (e.g. a 2x6 stud)."""
    items = [item for item in structural_hardware_catalog()
             if item.role == role and nominal in item.fits_nominal]
    if len(items) != 1:
        raise LookupError(f"expected exactly one library hardware item for role {role!r} at "
                          f"{nominal}, found {[item.tag for item in items]}")
    return items[0]


def hardware_by_model(model: str) -> "StructuralHardware | None":
    """Look a catalog item up by the part designation a plan authored (``Connector.size``).

    A plan may author a specific size within a family ("LUS210" of the LUS family), so an
    exact match wins and a family-prefix match is the fallback.
    """
    catalog = structural_hardware_catalog()
    exact = next((item for item in catalog if item.model == model), None)
    if exact is not None:
        return exact
    family = [item for item in catalog if model.startswith(item.model)]
    return max(family, key=lambda item: len(item.model)) if family else None


def hardware_row(item: "StructuralHardware | None", *, scope: str, count: int, basis: str,
                 part_number: str | None = None, size: str | None = None,
                 length_ft: float | None = None, coils: int | None = None,
                 by_storey: dict | None = None) -> dict:
    """One BOM line: what it is, how many, and the rule that produced the number.

    ``basis`` is not decoration — a hardware count is only auditable if the line carries
    the spacing/condition it came from, so every row states it.
    """
    return {
        "scope": scope,
        "role": item.role if item else None,
        "hardware_tag": item.tag if item else None,
        "description": item.name if item else scope,
        "manufacturer": item.manufacturer if item else None,
        "part_number": part_number if part_number is not None else (item.model if item else None),
        "size": size,
        "unit": item.unit if item else "each",
        "count": count,
        "length_ft": round(length_ft, 1) if length_ft is not None else None,
        "coils": coils,
        "basis": basis,
        "source": item.source if item else None,
        "by_storey": by_storey,
    }


def screw_for_required_length(role: str, required_length_in: float) -> tuple:
    """Shortest catalogued screw in ``role`` that still reaches ``required_length_in``.

    Returns ``(item, length_in, part_number)``. Raises when no catalogued length is long
    enough — an under-length structural screw is a real failure, not a rounding decision.
    """
    candidates = [(length_in, item)
                  for item in structural_hardware_catalog() if item.role == role
                  for length_in in item.available_lengths_in
                  if length_in + 1e-9 >= required_length_in]
    if not candidates:
        raise LookupError(f"no catalogued {role} reaches {required_length_in:.2f} in")
    length_in, item = min(candidates, key=lambda pair: pair[0])
    return item, length_in, item.part_number_by_length_in[length_in]
