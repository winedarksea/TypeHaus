"""The CONCRETE side of an angle tie — ACI 318-19 Ch. 17 on the anchors, for ``deck_tie``.

Simpson publishes the HL heavy angle wood-to-wood only (C-C-2024 p. 303), so where one leg
lands on a concrete wall the anchor into it is a design, not a table read. This grades it:
one 1/2" x 4" Titen HD per angle, on the wall core's centreline, from ESR-2713's strength
design data (cracked concrete, condition B — no supplementary reinforcement credited).

**The angle's geometry sets the anchor forces** (HL33, C-C-2024 p. 303: legs 3-1/4", 2-1/2"
long, the hole D3 = 2" off the heel). A force ALONG the heel enters the wood leg at the
bolt, 2" above the concrete, and the concrete leg resists that overturning between the
anchor and its far end (L/2 = 1.25"): ``T = F e / (L/2)`` per angle, the pair sharing F. A
force ACROSS the heel pries one angle's concrete leg about its toe (3-1/4 - 2 = 1.25"):
``T = F e / 1.25`` on ONE anchor — the whole of it, since which angle bears and which pulls
is not a question the model answers. Shear is the pair's.

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §10e.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import LimitState

_CITE_ESR = ("ICC-ES ESR-2713 (rev. 2026-03), Tables 1A, 2A, 3: Titen HD 1/2\" at h_nom 4\" — "
             "h_ef 2.99\", k_cr 17, N_sa 20,130 lb, V_sa 7,455 lb, l_e 2.99\", k_cp 2.0, c_min "
             "1-3/4\", s_min 3\"; pullout N/A (does not govern); §5.20 mechanically galvanized "
             "for exterior exposure")
#: ESR-2713, 1/2" Titen HD at 4" nominal embedment.
D_A_IN = 0.5
H_EF_IN = 2.99
L_E_IN = 2.99
K_CR = 17.0
N_SA_LB = 20_130.0
V_SA_LB = 7_455.0
K_CP = 2.0
C_MIN_IN = 1.75
S_MIN_IN = 3.0
#: ACI 318-19 §17.5.3 / ESR-2713: steel tension, steel shear, breakout tension (condition
#: B), breakout and pryout in shear.
PHI_SA_N, PHI_SA_V, PHI_CB_N, PHI_CB_V = 0.65, 0.60, 0.65, 0.70
#: HL33 (C-C-2024 p. 303): bolt height above the heel, half the length, the toe arm.
BOLT_HEIGHT_IN = 2.0
HALF_LENGTH_IN = 1.25
TOE_ARM_IN = 3.25 - 2.0
#: Where one anchor stands off its angle's heel (D3).
ANCHOR_OFF_HEEL_IN = 2.0


@dataclass(frozen=True)
class Group:
    """A joint's anchors: count, spacing along the wall, edge distance to each face."""

    joint: str
    anchors: int
    spacing_in: float
    edge_in: float
    fc_psi: float


def _n_b(fc: float) -> float:
    return K_CR * math.sqrt(fc) * H_EF_IN ** 1.5


def _psi_ed_n(c: float) -> float:
    return 1.0 if c >= 1.5 * H_EF_IN else 0.7 + 0.3 * c / (1.5 * H_EF_IN)


def _a_nc(group: Group) -> float:
    across = 2.0 * min(group.edge_in, 1.5 * H_EF_IN)
    along = 3.0 * H_EF_IN + min(group.spacing_in, 3.0 * H_EF_IN) * (group.anchors - 1)
    return across * along


def tension_capacity(group: Group, e_n_in: float) -> float:
    """φN_cbg (§17.6.2) with ψ_ec,N for a resultant ``e_n_in`` off the group centroid."""
    psi_ec = 1.0 / (1.0 + e_n_in / (1.5 * H_EF_IN))
    return (PHI_CB_N * _a_nc(group) / (9.0 * H_EF_IN ** 2) * psi_ec
            * _psi_ed_n(group.edge_in) * _n_b(group.fc_psi))


def shear_breakout(group: Group) -> float:
    """φV_cbg toward a face (§17.7.2), c = the edge distance, h_a >= 1.5c (a wall top)."""
    c = group.edge_in
    root = math.sqrt(group.fc_psi)
    v_b = min(7.0 * (L_E_IN / D_A_IN) ** 0.2 * math.sqrt(D_A_IN) * root * c ** 1.5,
              9.0 * root * c ** 1.5)
    width = 3.0 * c + min(group.spacing_in, 3.0 * c) * (group.anchors - 1)
    return PHI_CB_V * width * 1.5 * c / (4.5 * c * c) * v_b


def pryout(group: Group) -> float:
    return PHI_CB_V * K_CP * _a_nc(group) / (9.0 * H_EF_IN ** 2) * _psi_ed_n(
        group.edge_in) * _n_b(group.fc_psi)


@dataclass(frozen=True)
class Demand:
    """Strength-level forces on one joint: along the heel, across it, and where from."""

    label: str
    along_heel_lb: float
    across_heel_lb: float
    along_wall_is_heel: bool


def grade(group: Group, demand: Demand) -> tuple[float, float, float, str]:
    """``(tension ratio, shear ratio, interaction ratio, how)`` for one joint and case."""
    n = group.anchors
    t_each = abs(demand.along_heel_lb) / n * BOLT_HEIGHT_IN / HALF_LENGTH_IN
    t_pry = abs(demand.across_heel_lb) * BOLT_HEIGHT_IN / TOE_ARM_IN
    total = n * t_each + t_pry
    e_n = t_pry / total * group.spacing_in / 2.0 if total > 0.0 else 0.0
    tension = max(total / tension_capacity(group, e_n),
                  (t_each + t_pry) / (PHI_SA_N * N_SA_LB))
    # The heel runs ACROSS the wall on a stem tie, so along-heel shear goes toward a face.
    toward_face = abs(demand.across_heel_lb if demand.along_wall_is_heel
                      else demand.along_heel_lb)
    parallel = abs(demand.along_heel_lb if demand.along_wall_is_heel
                   else demand.across_heel_lb)
    breakout = shear_breakout(group)
    resultant = math.hypot(toward_face, parallel)
    shear = max(toward_face / breakout + parallel / (2.0 * breakout),
                resultant / pryout(group),
                resultant / n / (PHI_SA_V * V_SA_LB))
    # §17.8.1/17.8.2: either at or under 0.2 of its strength, the other governs alone.
    both = (max(tension, shear) if tension <= 0.2 or shear <= 0.2
            else (tension + shear) / 1.2)
    how = (f"{group.joint}: T {total:,.0f} lb on the group (e'_N {e_n:.2f}\"), V "
           f"{toward_face:,.0f} lb toward a face + {parallel:,.0f} lb along it, under "
           f"{demand.label}")
    return tension, shear, both, how


def states(worst: dict[str, tuple[float, str]], groups: list[Group]) -> list[LimitState]:
    """The three graded rows (worst over joints and cases) and two detailing rows."""
    names = {"tension": ("wall anchors, tension (breakout / steel)", "§17.6"),
             "shear": ("wall anchors, shear (breakout / pryout / steel)", "§17.7"),
             "both": ("wall anchors, tension-shear interaction", "§17.8.3 (sum / 1.2)")}
    out = [LimitState(names[key][0], ratio, 1.0, "",
                      f"ACI 318-19 {names[key][1]}; {_CITE_ESR}; {how}")
           for key, (ratio, how) in worst.items()]
    edge = min(g.edge_in for g in groups)
    spacing = min(g.spacing_in for g in groups)
    out += [LimitState("wall anchor edge distance", C_MIN_IN, edge, "in",
                       f"ESR-2713 Table 1A c_min 1-3/4\" (s >= 3\"); anchors on the core "
                       f"centreline, {edge:.2f}\" to each face", is_detailing=True),
            LimitState("wall anchor spacing", S_MIN_IN, spacing, "in",
                       "ESR-2713 Table 1A s_min 3\"", is_detailing=True)]
    return out


def group_for(ctx: Any, joint: Any, fc_psi: float) -> Group | None:
    """The joint's anchors, read off its parts and the wall's STRUCTURE layer."""
    from typehaus.model.enums import LayerFunction

    wall = ctx.plan.by_tag(joint.wall)
    assembly = ctx.plan.library.resolve_assembly(getattr(wall, "assembly", "") or "")
    core = next((float(ly.thickness.inches) for ly in getattr(assembly, "layers", ())
                 if ly.function is LayerFunction.STRUCTURE), None)
    parts = [ctx.plan.by_tag(t) for t in joint.parts]
    if core is None or not parts:
        return None
    along = 0 if joint.wall_axis == "x" else 1
    stations = sorted(p.position.xy_m[along] / 0.0254 for p in parts)
    spread = stations[-1] - stations[0]
    spacing = spread + 2.0 * ANCHOR_OFF_HEEL_IN if len(parts) > 1 else 0.0
    return Group(joint.member, len(parts), spacing, core / 2.0, fc_psi)
