"""SI analytical graph → PyNite's pound/inch inputs. Pure conversion, no solving.

**Axis convention: our Z-up frame maps straight through** (X→X, Y→Y, Z→Z). PyNite draws
and documents itself Y-up, but its solver is axis-agnostic: nothing in the stiffness
assembly privileges an axis. A permutation would make every coordinate in the exported
script disagree with the IFC and the DXF beside it, and a reviewer comparing the three
would have to undo it by hand — and RISA/SAP conventions differ from PyNite's anyway, so
there is no permutation that pleases everybody. Straight through, stated everywhere.

**What that costs, and where it is paid.** PyNite builds a member's local axes with Y up
(``Member3D.T``): for a member with equal end Y — every horizontal member in a Z-up model —
it takes local **y = global Y** and local **z = x × y**, which for a beam along global X is
global **Z**. So a gravity load bends a horizontal member in its local *z* direction, i.e.
**about its local y-axis**. ``section_properties`` therefore returns the *strong* (depth)
moment of inertia as **Iy** and the weak one as Iz — the mirror of PyNite's own Y-up
examples, and the reason the fixture's beam reports its wl²/8 under ``max_moment('My')``.
A column running along global Z lands in the same branch (its ends share Y), giving local
y = global Y and local z = global −X, so its Iy resists sway in global X.

A rectangular column whose depth face does not front global X needs ``Member.roll_deg``;
it is passed through as PyNite's ``rotation``. Nothing here guesses one.

Self weight is **not** applied: ``rho`` is zero for every material. The dead case carries
the loads the engineering records consumed, and a solver that quietly added a second dead
load on top of them would disagree with the calc sheet beside it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from typehaus.analytical.graph import AnalyticalModel, Fixity, Member, Support
from typehaus.resolve.framing.profiles import CrossSection

# ---------------------------------------------------------------- unit conversions
M_TO_IN = 1.0 / 0.0254
N_TO_LB = 0.2248089430997105          # 1 N in pounds-force (exact from 4.4482216152605)
PA_TO_PSI = N_TO_LB / (M_TO_IN**2)    # N/m² → lb/in²
N_PER_M_TO_LB_PER_IN = N_TO_LB / M_TO_IN
NM_TO_LB_IN = N_TO_LB * M_TO_IN
LB_PER_FT_PER_N_PER_M = N_TO_LB * 0.3048   # N/m → plf

#: Shear modulus as a fraction of E, by material family, with the source. Wood has no
#: published G in the design values a residential job uses; NDS 2018 Appendix F and the
#: APA/AWC glulam literature both take **G = E/16** for sawn lumber and glulam, and every
#: US wood design tool defaults to it. Concrete and steel get the isotropic relation
#: G = E / (2(1+ν)) at their conventional Poisson's ratios: ACI 318-19 R19.2.2 takes
#: ν ≈ 0.2 for normalweight concrete, AISC 360-16 §A3 takes ν = 0.3 for steel.
_MATERIAL_FAMILIES: tuple[tuple[tuple[str, ...], str, float, float], ...] = (
    # (name fragments, family, poisson, G as a fraction of E)
    (("concrete", "conc ", "cast"), "concrete", 0.20, 1.0 / 2.4),
    (("steel", "hss", "w-shape", "wide flange"), "steel", 0.30, 1.0 / 2.6),
)
_WOOD_POISSON = 0.20          # nominal; wood is orthotropic and no single ν describes it
_WOOD_G_OVER_E = 1.0 / 16.0
#: Densities are deliberately zero — see the module docstring.
_RHO_PCI = 0.0

_ILLEGAL_NAME_CHARS = re.compile(r"[^A-Z0-9_.-]+")
_DIRECTION_TO_PYNITE = {"GX": "FX", "GY": "FY", "GZ": "FZ"}


# ---------------------------------------------------------------- section properties
def section_properties(section: CrossSection) -> tuple[float, float, float, float]:
    """``(A_in2, Iy_in4, Iz_in4, J_in4)`` for one cross-section.

    **Iy is the strong axis** (bending in the ``depth_m`` direction) and Iz the weak one,
    for the reason set out in the module docstring. ``plies`` is already folded into
    ``width_m`` by ``profiles.py``, so it is not applied again here.

    ``J`` is **approximate** for everything but the round section: the rectangle uses the
    Saint-Venant series (Roark 7e Table 10.1 case 4), the I-joist the open thin-walled sum
    ``Σ b t³/3``, which ignores warping restraint. Neither matters for a member whose
    torsion is not being designed; a member whose torsion *is* wants a real section.
    """
    if section.shape == "round":
        d = section.width_m * M_TO_IN
        i = math.pi * d**4 / 64.0
        return (math.pi * d * d / 4.0, i, i, 2.0 * i)

    if section.shape == "rect":
        b = section.width_m * M_TO_IN      # thickness
        h = section.depth_m * M_TO_IN      # wide face
        return (b * h, b * h**3 / 12.0, h * b**3 / 12.0, _rect_torsion_in4(b, h))

    if section.shape == "angle":
        return _angle_properties(section)

    if section.shape == "i_joist":
        return _i_joist_properties(section)

    raise ValueError(
        f"no section properties for shape {section.shape!r}; add a branch rather than "
        "letting it fall through to a rectangle"
    )


def _rect_torsion_in4(b: float, h: float) -> float:
    """Saint-Venant J for a solid rectangle, long side ``a``, short side ``t``."""
    a, t = (h, b) if h >= b else (b, h)
    return a * t**3 * (1.0 / 3.0 - 0.21 * (t / a) * (1.0 - t**4 / (12.0 * a**4)))


def _angle_properties(section: CrossSection) -> tuple[float, float, float, float]:
    """A rolled angle as two rectangles, about its GEOMETRIC (leg-parallel) axes.

    Computed, not transcribed. Against AISC's L3-1/2x3-1/2x1/4 the two-rectangle model gives
    A 1.6875 in2 (published 1.69, 0.15% low) and I 2.010 in4 (published 1.99, 1.0% high);
    the residual is the fillet at the heel, which this decomposition omits — it adds a little
    area at small radius, so it raises A and lowers I, exactly the pair of signs seen.

    **Geometric axes, not principal ones, and that is the right answer here.** An angle's
    principal axes are rotated off its legs, and AISC publishes both sets. A lintel bends
    about a horizontal axis because the masonry it carries holds it there; it is not free to
    deflect about its weak principal axis. A member that IS free to — an unbraced angle
    strut — wants the principal values, and this function does not give them.

    ``J`` is the open thin-walled sum and is approximate, as the module docstring says: it
    reads 0.0352 in4 against AISC's 0.0332.
    """
    if not section.web_thickness_m:
        raise ValueError("angle section is missing its leg thickness (web_thickness_m)")
    a = section.width_m * M_TO_IN        # leg along u
    b = section.depth_m * M_TO_IN        # leg along v
    t = section.web_thickness_m * M_TO_IN
    area = t * (a + b - t)
    # Centroid from the heel, each axis: the full leg plus the other leg less the overlap.
    v_bar = (b * b + (a - t) * t) / (2.0 * (a + b - t))
    u_bar = (a * a + (b - t) * t) / (2.0 * (a + b - t))
    iy = (t * b**3 / 12.0 + b * t * (b / 2.0 - v_bar) ** 2
          + (a - t) * t**3 / 12.0 + (a - t) * t * (v_bar - t / 2.0) ** 2)
    iz = (t * a**3 / 12.0 + a * t * (a / 2.0 - u_bar) ** 2
          + (b - t) * t**3 / 12.0 + (b - t) * t * (u_bar - t / 2.0) ** 2)
    j = t**3 * (a + b - t) / 3.0
    return (area, iy, iz, j)


def _i_joist_properties(section: CrossSection) -> tuple[float, float, float, float]:
    if not (section.flange_width_m and section.flange_thickness_m and section.web_thickness_m):
        raise ValueError("i_joist section is missing its flange/web dimensions")
    bf = section.flange_width_m * M_TO_IN
    tf = section.flange_thickness_m * M_TO_IN
    tw = section.web_thickness_m * M_TO_IN
    d = section.depth_m * M_TO_IN
    hw = d - 2.0 * tf                      # clear web depth
    area = 2.0 * bf * tf + hw * tw
    iy = (bf * d**3 - (bf - tw) * hw**3) / 12.0
    iz = (2.0 * tf * bf**3 + hw * tw**3) / 12.0
    j = (2.0 * bf * tf**3 + hw * tw**3) / 3.0
    return (area, iy, iz, j)


# ---------------------------------------------------------------- names
def _sanitise(text: str) -> str:
    """Uppercase, DXF/RISA-legal (``A-Z 0-9 _ . -``), no leading/trailing separator."""
    return _ILLEGAL_NAME_CHARS.sub("_", text.upper()).strip("_") or "UNNAMED"


def _section_token(section: CrossSection) -> str:
    if section.shape == "round":
        return f"{section.width_m * M_TO_IN:g}_RD"
    if section.shape == "angle":
        thk = (section.web_thickness_m or 0.0) * M_TO_IN
        return (f"L{section.width_m * M_TO_IN:g}X{section.depth_m * M_TO_IN:g}X{thk:g}")
    suffix = "_IJ" if section.shape == "i_joist" else ""
    return f"{section.width_m * M_TO_IN:g}X{section.depth_m * M_TO_IN:g}{suffix}"


def section_name(member: Member) -> str:
    """The one name a section is known by — PyNite's section, the DXF layer, the CSV cell.

    ``3.5X11.875_GLULAM``, ``12_RD_CONCRETE``. Geometry plus the first word of the material,
    because RISA's DXF import reads the layer name as the section-set name and a set called
    ``3.5X11.875`` that is glulam in one place and LVL in another is a set nobody can price.
    """
    family = _sanitise(member.material.split()[0]) if member.material.split() else "UNSPEC"
    return f"{_section_token(member.section)}_{family}"


def support_label(support: Support, separator: str = "+") -> str:
    """``fixed`` | ``pinned`` | ``pinned+RX`` — what a reader needs to see at a node.

    The fixity alone no longer tells the whole story: a beam end bearing on a wall is pinned
    for bending and still restrained against rolling about its own axis. Naming the extra
    rotations is the difference between a support a reviewer can check and one they have to
    take on trust. Shared by the CSV and the DXF so the two cannot spell it differently.
    """
    restrained = support.restrained_rotations()
    named = [axis for axis, on in zip(("RX", "RY", "RZ"), restrained, strict=True) if on]
    implied = (True, True, True) if support.fixity is Fixity.FIXED else (False, False, False)
    if restrained == implied:
        return support.fixity.value
    return separator.join([support.fixity.value, *named]) if named else support.fixity.value


def material_names(model: AnalyticalModel) -> dict[tuple[str, float], str]:
    """``(material string, E) → PyNite material name``, disambiguated only where needed."""
    keys = sorted({(m.material, m.e_pa) for m in model.members}
                  | {(p.material, p.e_pa) for p in model.plates})
    by_base: dict[str, list[tuple[str, float]]] = {}
    for key in keys:
        by_base.setdefault(_sanitise(key[0]), []).append(key)
    names: dict[tuple[str, float], str] = {}
    for base, group in by_base.items():
        for key in group:
            # Two E values under one material string is a real distinction (an adjusted
            # modulus against a published one); the suffix keeps both, in psi.
            names[key] = base if len(group) == 1 else f"{base}_E{key[1] * PA_TO_PSI:.0f}"
    return names


# ---------------------------------------------------------------- the call list
@dataclass(frozen=True)
class PyniteInputs:
    """Exactly the PyNite calls to make, in order, in pounds and inches.

    One list, two consumers: ``analytical/solve.py`` runs it in process and
    ``emit/analytical/pynite_script.py`` writes it out as literal data. A generated script
    that disagreed with the solve beside it would be worse than no script.

    Every tuple is plain data (str / float / bool) so it round-trips through ``repr`` into
    the generated file unchanged.
    """

    nodes: tuple[tuple[str, float, float, float], ...]
    materials: tuple[tuple[str, float, float, float, float], ...]          # name, E, G, nu, rho
    sections: tuple[tuple[str, float, float, float, float], ...]           # name, A, Iy, Iz, J
    members: tuple[tuple[str, str, str, str, str, float], ...]             # name,i,j,mat,sec,rot
    supports: tuple[tuple[str, bool, bool, bool, bool, bool, bool], ...]
    releases: tuple[tuple[str, tuple[bool, ...]], ...]                     # name, 12 flags
    dist_loads: tuple[tuple[str, str, float, float, float, float, str], ...]
    pt_loads: tuple[tuple[str, str, float, float, str], ...]
    node_loads: tuple[tuple[str, str, float, str], ...]
    combos: tuple[tuple[str, tuple[tuple[str, float], ...]], ...]
    quads: tuple[tuple[str, str, str, str, str, float, str], ...]
    support_springs: tuple[tuple[str, str, float, str | None], ...]
    quad_pressures: tuple[tuple[str, float, str], ...]

    @property
    def combo_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.combos)


def build_inputs(model: AnalyticalModel) -> PyniteInputs:
    """Convert the SI graph to the pound/inch call list. Deterministic: everything sorted."""
    mats = material_names(model)
    lengths = {m.id: model.length_m(m) * M_TO_IN for m in model.members}

    nodes = tuple(sorted(
        (n.id, n.x_m * M_TO_IN, n.y_m * M_TO_IN, n.z_m * M_TO_IN) for n in model.nodes
    ))
    plate_poisson = {(plate.material, plate.e_pa): plate.poisson for plate in model.plates}
    materials = tuple(sorted(
        (name, e_pa * PA_TO_PSI,
         e_pa * PA_TO_PSI / (2.0 * (1.0 + plate_poisson[(mat, e_pa)]))
         if (mat, e_pa) in plate_poisson else e_pa * PA_TO_PSI * _g_over_e(mat),
         plate_poisson.get((mat, e_pa), _poisson(mat)), _RHO_PCI)
        for (mat, e_pa), name in mats.items()
    ))
    sections = tuple(sorted(
        {(section_name(m), *section_properties(m.section)) for m in model.members}
    ))
    members = tuple(sorted(
        (m.id, m.n0, m.n1, mats[(m.material, m.e_pa)], section_name(m), float(m.roll_deg))
        for m in model.members
    ))
    supports = tuple(sorted(
        (s.node, True, True, True, *s.restrained_rotations()) for s in model.supports
    ))
    releases = tuple(sorted(
        (m.id, _release_flags(m, model)) for m in model.members if m.releases.any
    ))

    dist_loads = tuple(sorted(
        (
            load.member,
            _DIRECTION_TO_PYNITE[load.direction],
            load.w0_n_m * N_PER_M_TO_LB_PER_IN,
            load.w1_n_m * N_PER_M_TO_LB_PER_IN,
            load.x0 * lengths[load.member],
            load.x1 * lengths[load.member],
            load.case.value,
        )
        for load in model.member_loads
    ))
    pt_loads = tuple(sorted(
        (
            load.member,
            _DIRECTION_TO_PYNITE[load.direction],
            load.p_n * N_TO_LB,
            load.x * lengths[load.member],
            load.case.value,
        )
        for load in model.member_point_loads
    ))
    node_loads = tuple(sorted(_node_load_calls(model)))
    quads = tuple(sorted(
        (plate.id, plate.i, plate.j, plate.m, plate.n, plate.thickness_m * M_TO_IN,
         mats[(plate.material, plate.e_pa)])
        for plate in model.plates
    ))
    support_springs = tuple(sorted(
        (spring.node, spring.dof,
         spring.stiffness_n_m * (NM_TO_LB_IN if spring.dof.startswith("R")
                                 else N_TO_LB / M_TO_IN),
         spring.direction)
        for spring in model.support_springs
    ))
    quad_pressures = tuple(sorted(
        (pressure.plate, pressure.pressure_pa * PA_TO_PSI, pressure.case.value)
        for pressure in model.plate_pressures
    ))
    return PyniteInputs(
        nodes=nodes, materials=materials, sections=sections, members=members,
        supports=supports, releases=releases, dist_loads=dist_loads, pt_loads=pt_loads,
        node_loads=node_loads, combos=_combos(model), quads=quads,
        support_springs=support_springs, quad_pressures=quad_pressures,
    )


def _node_load_calls(model: AnalyticalModel) -> list[tuple[str, str, float, str]]:
    calls: list[tuple[str, str, float, str]] = []
    for load in model.node_loads:
        for direction, value, scale in (
            ("FX", load.fx_n, N_TO_LB), ("FY", load.fy_n, N_TO_LB), ("FZ", load.fz_n, N_TO_LB),
            ("MX", load.mx_nm, NM_TO_LB_IN), ("MY", load.my_nm, NM_TO_LB_IN),
            ("MZ", load.mz_nm, NM_TO_LB_IN),
        ):
            if value:
                calls.append((load.node, direction, value * scale, load.case.value))
    return calls


def _combos(model: AnalyticalModel) -> tuple[tuple[str, tuple[tuple[str, float], ...]], ...]:
    """One unit combo per case, named for the case, plus the authored combinations.

    The per-case combos are what makes ``reactions[(node, "wind")]`` mean the wind case
    alone — PyNite reports results per *combination*, never per case.
    """
    case_names = (sorted({c.kind.value for c in model.cases})
                  if model.include_unit_case_combinations else [])
    combos = [(name, ((name, 1.0),)) for name in case_names]
    taken = set(case_names)
    for combination in sorted(model.combinations, key=lambda c: c.name):
        # A combination sharing a case's name would silently replace it in PyNite's dict.
        name = combination.name if combination.name not in taken else f"{combination.name}_COMBO"
        taken.add(name)
        combos.append((name, tuple(sorted(
            (kind.value, float(f)) for kind, f in combination.factors.items()
        ))))
    return tuple(combos)


#: ``def_support``'s six flags are DX, DY, DZ, RX, RY, RZ. Translations are always
#: restrained — a support that let a member fall is not a support — and the three
#: rotations come from ``Support.restrained_rotations()``, never from the fixity here.
#: A PINNED beam end that cannot roll about its own axis restrains one rotation and stays
#: pinned for bending; deriving the flags from ``Fixity`` alone would drop that and leave a
#: moment-released beam between two pins as a mechanism.


def _release_flags(member: Member, model: AnalyticalModel) -> tuple[bool, ...]:
    """``def_releases``'s twelve flags: Dxi Dyi Dzi Rxi Ryi Rzi Dxj Dyj Dzj Rxj Ryj Rzj.

    A moment release frees bending about **both** local axes (Ry and Rz) and not torsion:
    a beam bearing on a post top is free to rotate either way over the bearing, but a
    torsional release on top of it would leave a member spinning on its own axis when the
    other end is released too, and PyNite would report the frame unstable rather than the
    modelling mistake it is. A hinge frees the ONE local axis parallel to its global axis.
    """
    r = member.releases
    i_y, i_z = (True, True) if r.i_moment else _hinge_flags(member, model, r.i_hinge)
    j_y, j_z = (True, True) if r.j_moment else _hinge_flags(member, model, r.j_hinge)
    return (False, False, False, False, i_y, i_z, False, False, False, False, j_y, j_z)


def _hinge_flags(member: Member, model: AnalyticalModel,
                 axis: str | None) -> tuple[bool, bool]:
    """``(Ry, Rz)`` for a hinge about global ``axis``. Mapped on an unrolled Z-vertical
    member only: PyNite takes its local y = global Y and local z = x × Y = ∓global X
    (``Member3D.T``'s equal-end-Y branch), so X → Rz and Y → Ry."""
    if axis is None:
        return (False, False)
    a, b = model.node(member.n0), model.node(member.n1)
    if member.roll_deg or not (math.isclose(a.x_m, b.x_m, abs_tol=1e-9)
                               and math.isclose(a.y_m, b.y_m, abs_tol=1e-9)):
        raise ValueError(f"{member.id}: a hinge maps only onto an unrolled vertical member")
    return (axis == "Y", axis == "X")


def _family(material: str) -> tuple[str, float, float]:
    lowered = material.lower()
    for fragments, family, poisson, g_over_e in _MATERIAL_FAMILIES:
        if any(fragment in lowered for fragment in fragments):
            return (family, poisson, g_over_e)
    return ("wood", _WOOD_POISSON, _WOOD_G_OVER_E)


def _poisson(material: str) -> float:
    return _family(material)[1]


def _g_over_e(material: str) -> float:
    return _family(material)[2]
