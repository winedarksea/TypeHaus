"""Section profiles and material grades on structural members, for a reviewing engineer.

An IFC that draws a beam as a box says the beam is 3-1/2" by 11-7/8" only in the sense that
a photograph does. ``IfcMaterialProfileSet`` says it in the terms an analysis tool reads:
this member has *this named section* of *this material*, and here are its dimensions. Bonsai
lists it, ETABS and SAP2000 import it, and a PE checking the model against the calculation
package can confirm the section without measuring the geometry.

**Everything here comes from what the model authors, and nothing is invented.** The section
is ``resolve/framing/profiles.cross_section`` — the same parse the geometry stage uses, so
the profile and the solid cannot disagree. The grade comes off the size string's own suffix
(LVL, GLB, PSL) or off a ``ConcreteSpec``'s f'c. **Species is not authored anywhere in this
engine**, so a sawn member's material is written as "sawn lumber" and not as "SPF #2": a
grade nobody typed is a grade nobody checked, and putting one in an IFC a PE reads would be
this module making a structural claim.

``Pset_MaterialMechanical.YoungModulus`` is written only where an engineering record
actually computed an adjusted E. A published dry-use E on a member the calculation treated
as wet would contradict the calculation sitting beside it in the same file.
"""

from __future__ import annotations

from typing import Any

#: Suffixes in a ``Beam.size`` / member profile that name an engineered product, mapped to
#: the material name a reviewer expects to read. Order matters: the longest match wins.
_ENGINEERED = (
    ("24f-v5m1", "structural glulam 24F-V5M1/SP"),
    ("glb", "structural glulam"),
    ("lvl", "laminated veneer lumber"),
    ("psl", "parallel strand lumber"),
    ("lsl", "laminated strand lumber"),
    ("tji", "wood I-joist"),
    ("i-joist", "wood I-joist"),
)

#: What a member with no product suffix is called. NOT a species and not a grade: this
#: engine does not author either, and inventing one in a file a PE reads would be a claim.
_SAWN = "sawn lumber"


def material_name(profile: str, concrete_fc_psi: float | None = None) -> str:
    """The material a reviewer should see, from what the model actually says."""
    if concrete_fc_psi:
        return f"concrete f'c {concrete_fc_psi:,.0f} psi"
    text = (profile or "").lower()
    for token, name in _ENGINEERED:
        if token in text:
            return name
    return _SAWN


class ProfileCollector:
    """Collects members by section, then writes ONE profile set per distinct section.

    Not one per member, and that is not a micro-optimisation. catlin resolves ~15,000 framed
    members over a few dozen distinct sections; a profile set each would add ~75,000
    entities to a file that is already 11 MB, for no information a reviewer does not get
    from the shared one. IFC's own idiom is a single ``IfcRelAssociatesMaterial`` naming
    many ``RelatedObjects``, which is what this writes.

    Deterministic by construction: sections are emitted in sorted key order and each one's
    members in the order they were collected, which is the emitters' own sorted-by-uid walk.
    """

    def __init__(self) -> None:
        self._by_section: dict[tuple[str, str, float | None], list] = {}

    def add(self, element: Any, profile: str, *, concrete_fc_psi: float | None = None,
            youngs_modulus_psi: float | None = None) -> None:
        if not profile or element is None:
            return
        key = (profile, material_name(profile, concrete_fc_psi), youngs_modulus_psi)
        self._by_section.setdefault(key, []).append(element)

    def flush(self, f: Any) -> int:
        """Write the profile sets and their associations. Returns how many sections."""
        from typehaus.emit.ifc.lowlevel import new_guid

        written = 0
        for (profile, name, modulus), elements in sorted(
                self._by_section.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            shape = _profile_def(f, profile)
            if shape is None:
                continue
            material = f.create_entity("IfcMaterial", Name=name)
            if modulus:
                _mechanical(f, material, modulus)
            material_profile = f.create_entity(
                "IfcMaterialProfile", Name=profile, Material=material, Profile=shape)
            profile_set = f.create_entity(
                "IfcMaterialProfileSet", Name=profile, MaterialProfiles=[material_profile])
            f.create_entity("IfcRelAssociatesMaterial", GlobalId=new_guid(),
                            RelatedObjects=list(elements), RelatingMaterial=profile_set)
            written += 1
        self._by_section.clear()
        return written


def _profile_def(f: Any, name: str) -> Any | None:
    """The IFC profile for one section string, in metres — the file's own unit.

    An I-joist is written as a rectangle of its overall envelope rather than as
    ``IfcIShapeProfileDef``: the I-shape entity is defined for a ROLLED STEEL section, with
    fillet radii and a flange slope a wood I-joist does not have, and a reviewer reading
    those fields would be reading fields nobody filled in. The envelope with the joist's own
    series in ``Name`` ("11.875 TJI 230") is the honest statement, and it is what the series
    identifies anyway.
    """
    from typehaus.resolve.framing.profiles import cross_section

    try:
        section = cross_section(name)
    except (KeyError, ValueError):
        return None
    if section.shape == "round":
        return f.create_entity("IfcCircleProfileDef", ProfileType="AREA", ProfileName=name,
                               Radius=float(section.width_m) / 2.0)
    if section.shape in ("rect", "i_joist"):
        return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA",
                               ProfileName=name, XDim=float(section.width_m),
                               YDim=float(section.depth_m))
    return None


#: psi -> Pa. IFC's mechanical pset is SI, and a modulus written in psi against a metre-unit
#: project is the kind of silent factor-of-6895 error nobody catches by eye.
_PSI_TO_PA = 6894.757293168361


def _mechanical(f: Any, material: Any, youngs_modulus_psi: float) -> None:
    prop = f.create_entity(
        "IfcPropertySingleValue", Name="YoungModulus",
        NominalValue=f.create_entity("IfcModulusOfElasticityMeasure",
                                     float(youngs_modulus_psi) * _PSI_TO_PA))
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical",
                    Properties=[prop], Material=material)


#: The IFC classes a structural section is meaningful on. A slab or a wall is a LAYER set,
#: not a profile set, and already has one.
_PROFILED = ("IfcBeam", "IfcColumn", "IfcMember")


def attach_profiles(f: Any, model: Any, engineering: Any = None) -> int:
    """Give every emitted structural member its section, as a POST-PASS over the file.

    A post-pass rather than a parameter threaded through five emitters, and that is a
    deliberate call. Every member this engine emits already carries its own ``profile``
    string in the ``PSET_SOURCE`` property set — put there for exactly this kind of
    round-trip — so the information is in the file and does not need re-plumbing. A standalone
    beam or column solid carries no profile there (its geometry is an outline prism), so its
    section is read off the AUTHORED element's ``size``, which is where a person typed it.

    Returns the number of distinct sections written.
    """
    import ifcopenshell.util.element as ue

    collector = ProfileCollector()
    moduli = _adjusted_moduli(engineering)
    for kind in _PROFILED:
        try:
            entities = f.by_type(kind)
        except RuntimeError:
            continue
        for element in entities:
            if ue.get_material(element) is not None:
                # The element already has a material association — a finish assembly's
                # layer set, put there by `_assign_solid_material`. IFC gives an element one
                # material association, and a second would leave a reader (and Bonsai)
                # guessing which is the answer. The layer set names the product that was
                # specified, which is the more load-bearing of the two, so it keeps the slot.
                continue
            profile, tag = _section_of(element, model, ue)
            if not profile:
                continue
            collector.add(element, profile,
                          concrete_fc_psi=_concrete_fc(model, tag),
                          youngs_modulus_psi=moduli.get(tag))
    return collector.flush(f)


def _section_of(element: Any, model: Any, ue: Any) -> tuple[str | None, str | None]:
    """``(section string, model tag)`` for one emitted element."""
    from typehaus._meta import PSET_SOURCE

    psets = ue.get_psets(element)
    source = psets.get(PSET_SOURCE) or {}
    tag = source.get("tag")
    profile = source.get("profile")
    if profile:
        return str(profile), tag
    # A standalone beam/column solid: no profile in its source pset, because its geometry
    # is an outline prism rather than a swept section. The size is on the authored element.
    plan = getattr(model, "plan", None)
    if plan is None or not tag:
        return None, tag
    authored = plan.by_tag(str(tag))
    size = getattr(authored, "size", None) or getattr(authored, "profile", None)
    return (str(size) if size else None), tag


def _concrete_fc(model: Any, tag: str | None) -> float | None:
    """f'c off the element's own ``ConcreteSpec``, where it has one. Never guessed."""
    plan = getattr(model, "plan", None)
    if plan is None or not tag:
        return None
    authored = plan.by_tag(str(tag))
    concrete = getattr(authored, "concrete", None)
    fc = getattr(concrete, "fc", None) if concrete is not None else None
    return float(fc) if fc else None


def _adjusted_moduli(engineering: Any) -> dict[str, float]:
    """``tag -> E_adjusted`` from the records that actually computed one.

    Only from a record. A published dry-use E on a member the calculation treated as wet
    would contradict the calculation sitting beside it in the same file.
    """
    moduli: dict[str, float] = {}
    if engineering is None:
        return moduli
    for item_id in sorted(engineering):
        record = engineering[item_id]
        value = next((q.value for q in record.inputs if q.name == "E_adjusted"), None)
        if value:
            for tag in record.element_tags:
                moduli.setdefault(tag, float(value))
    return moduli
