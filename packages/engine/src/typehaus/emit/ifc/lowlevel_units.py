"""The units a structural analysis view needs, appended to the project's assignment.

``lowlevel.assign_project_units`` writes the four the IFC4 Reference View requires —
length, area, volume, plane angle. An analysis model quotes forces, pressures and
line loads, and a ``IfcLinearForceMeasure`` of ``-2000.`` against a project that declares
no linear-force unit is a number an importer has to guess the unit of. SAP2000 and ETABS
guess *their* current unit set, which is how a 2 kN/m dead load arrives as 2 kip/ft.

Appended to the existing ``IfcUnitAssignment`` rather than creating a second one: IFC4
allows exactly one per project (``IfcProject.UnitsInContext``), and ``unit.assign_unit``
finds and extends the one that is already there.

Kept out of ``lowlevel.py`` deliberately — that file is 562 lines and this is a distinct
concern nothing but the analytical emitters ask for.
"""

from __future__ import annotations

from typing import Any

#: ``IfcDerivedUnitEnum`` member -> the base-unit exponents that define it. IFC4 has no
#: SI unit for any of these; a derived unit is how the schema says "newtons per metre".
_DERIVED = (
    ("LINEARFORCEUNIT", (("FORCEUNIT", 1), ("LENGTHUNIT", -1))),     # N/m
    ("PLANARFORCEUNIT", (("FORCEUNIT", 1), ("LENGTHUNIT", -2))),     # N/m2
    ("TORQUEUNIT", (("FORCEUNIT", 1), ("LENGTHUNIT", 1))),           # N.m
)


def assign_structural_units(f: Any) -> None:
    """Add force (N), pressure (Pa), mass (kg) and the derived line/area/moment units."""
    import ifcopenshell.api.unit

    base = {
        "FORCEUNIT": ifcopenshell.api.unit.add_si_unit(f, unit_type="FORCEUNIT"),
        "PRESSUREUNIT": ifcopenshell.api.unit.add_si_unit(f, unit_type="PRESSUREUNIT"),
        # SI's base mass unit is the GRAM in IFC's own naming; the kilogram is its KILO
        # prefix, and it is what every structural tool expects to read.
        "MASSUNIT": ifcopenshell.api.unit.add_si_unit(f, unit_type="MASSUNIT",
                                                      prefix="KILO"),
        "LENGTHUNIT": _project_metre(f),
    }
    units = [base["FORCEUNIT"], base["PRESSUREUNIT"], base["MASSUNIT"]]
    for unit_type, exponents in _DERIVED:
        elements = [f.create_entity("IfcDerivedUnitElement", Unit=base[name],
                                    Exponent=exponent)
                    for name, exponent in exponents]
        units.append(f.create_entity("IfcDerivedUnit", Elements=elements,
                                     UnitType=unit_type))
    ifcopenshell.api.unit.assign_unit(f, units=units)


def _project_metre(f: Any) -> Any:
    """The metre the project already declares, so the derived units cite one length unit.

    Creating a second ``IfcSIUnit(.LENGTHUNIT.,$,.METRE.)`` for the derived elements would
    leave the file saying "per metre" against a metre that is not the project's own.
    """
    import ifcopenshell.api.unit

    for assignment in f.by_type("IfcUnitAssignment"):
        for unit in assignment.Units or ():
            if unit.is_a("IfcSIUnit") and unit.UnitType == "LENGTHUNIT":
                return unit
    return ifcopenshell.api.unit.add_si_unit(f, unit_type="LENGTHUNIT")
