"""The board's own rows for ``thermal_break`` — free body §11a and §11i.

Fresh-concrete pressure on the AUTHORED placement, and the board's summer strain — the
locked-in pour squeeze plus the closing at the neutral point — against its recoverable range.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.thermal_break_geometry import Board

#: ACI 347R-14 unit weight of fresh concrete, pcf — the ``w`` in ``p = w·h``.
CONCRETE_PCF = 150.0
#: Coefficient of thermal expansion, normal-weight concrete, per °F (PCA average).
ALPHA_C_PER_F = 5.5e-6
#: ASTM C578's lowest-rated type of each foam, psi — the floor for a house board whose grade
#: the model never states (Atlas, "ASTM C578 Comparison (EPS vs. XPS)", Table 1).
C578_FLOOR_PSI = {"xps": (15.0, "ASTM C578 Type X"), "eps": (10.0, "ASTM C578 Type I")}

TEMPERATURE_MISSING = (
    "`Site.concrete_service_temperature` with `placement_min_f` — the concrete's service "
    "range and the specified set floor the movement, thrust, opening and racking rows read")


@dataclass(frozen=True)
class Product:
    psi: float
    modulus_psi: float
    source: str
    estimated: bool = False

    @property
    def strain_limit(self) -> float:
        """σ_y / E: where the sheet's linear modulus reaches its own rating — the board's
        recoverable range under an imposed, cyclic displacement (free body §11 inputs)."""
        return self.psi / self.modulus_psi


@dataclass(frozen=True)
class Temps:
    max_f: float
    min_f: float
    set_f: float
    source: str

    @property
    def closing(self) -> float:
        return self.max_f - self.set_f

    @property
    def opening(self) -> float:
        return self.max_f - self.min_f


def temps(ctx) -> Temps | None:
    spec = getattr(ctx.plan.project.site, "concrete_service_temperature", None)
    if spec is None or spec.placement_min_f is None:
        return None
    return Temps(spec.max_f, spec.min_f, spec.placement_min_f, spec.source)


def product_of(element) -> Product | None:
    if element is None or element.modulus_psi is None or element.source is None:
        return None
    return Product(element.psi, element.modulus_psi, element.source,
                   bool(getattr(element, "modulus_estimated", False)))


def pour_head_in(ctx, board: Board) -> tuple[float | None, str]:
    """Head from the top of the placement the board is cast against, and which rule read it.

    A named, existing ``placement_sequence_ref`` means the court element the board faces is
    its own placement (catlin: footings (1), walls (2)); otherwise the whole court structure
    is taken monolithic to its highest top — the conservative sequence.
    """
    ref = getattr(board.element, "placement_sequence_ref", None)
    if ref and ctx.plan.by_tag(ref) is not None and board.court_tag:
        from typehaus.engineering.thermal_break_geometry import z_extent

        ext = z_extent(ctx, board.court_tag)
        if ext is not None:
            return ext[1] - board.bottom_in, f"placement of {board.court_tag} ({ref})"
    tops = [e.top_elevation.inches for e in map(ctx.plan.by_tag, board.structure)
            if getattr(e, "top_elevation", None) is not None]
    if not tops:
        return None, ""
    return max(tops) - board.bottom_in, "monolithic to the court's highest top"


def pressure(ctx, board: Board, product: Product, states, missing, inputs) -> float | None:
    head_in, how = pour_head_in(ctx, board)
    if head_in is None:
        missing.append(f"a top elevation on the structure {board.tag} faces")
        return None
    psi = CONCRETE_PCF * head_in / 12.0 / 144.0
    inputs.append(Quantity("pour_head", head_in / 12.0, "ft", 0.01))
    states.append(LimitState(
        "fresh-concrete pressure", psi, product.psi, "psi",
        f"ACI 347R-14 capped at wh — {CONCRETE_PCF:.0f} pcf x {head_in / 12:.3f}' of head, "
        f"{how}; vs the board's {product.psi:.0f} psi"))
    return psi


def movement(board: Board, product: Product, t: Temps, run: float, closure_in: float,
             pour_psi: float | None, states, inputs, e_scale: float = 1.0) -> None:
    """The board's summer strain — the locked-in pour squeeze plus the closing at the neutral
    point — against t·ε_lim (free body §11i); the ratio is ``(p + σ)/σ_y``."""
    e = product.modulus_psi * e_scale
    pour = (pour_psi or 0.0) * board.t_in / e
    inputs += [Quantity("delta_T", t.closing, "F", 0.1), Quantity("court_run", run, "in", 0.1),
               Quantity("foam_modulus", e, "psi", 1.0),
               Quantity("closure", closure_in, "in", 1e-5)]
    est = " ESTIMATED" if product.estimated else ""
    states.append(LimitState(
        "board strain, pour + closing", pour + closure_in, board.t_in * product.psi / e, "in",
        f"locked-in pour {pour_psi or 0:.3f} psi x {board.t_in:.2f}\"/E {pour:.5f}\" + closing "
        f"{closure_in:.5f}\" at the neutral point ({t.max_f:.0f} - {t.set_f:.0f} F specified "
        f"set); vs {board.t_in:.2f}\" x sigma_y/E = {product.psi:.0f}/{e:,.0f}{est} — "
        f"{product.source}; service range: {t.source}"))


def house_insulation_row(board: Board, layers, sigma: float, pour_psi: float | None,
                         states, missing) -> None:
    """The house foam the board bears on, at the weakest ASTM C578 type of its material."""
    for name, material, _thick in layers:
        floor = C578_FLOOR_PSI.get(material)
        if floor is None:
            missing.append(f"a compressive rating for {board.house_tag}'s `{name}` "
                           f"({material}), which the board bears on")
            continue
        psi, label = floor
        demand = sigma + (pour_psi or 0.0)
        states.append(LimitState(
            "house insulation bearing", demand, psi, "psi",
            f"locked-in pour {pour_psi or 0:.2f} + closing {sigma:.2f} psi at the board's base "
            f"through {board.house_tag}'s "
            f"`{name}`, whose grade the model does not state: graded at {label}, "
            f"{psi:.0f} psi, the lowest the standard admits"))
        return
