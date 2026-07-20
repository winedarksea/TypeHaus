"""Physical, exportable exterior-layer continuity across platform framing."""

from __future__ import annotations

from typehaus.resolve.model import ResolvedEnvelopeBand, ResolvedModel


def resolve_platform_envelope_bands(model: ResolvedModel) -> None:
    """Create outboard-layer solids between a lower plate and its stacked wall.

    The cavity batt deliberately ends at the plate; only sheathing and layers outboard
    of it span the rim.  This is the conventional platform-frame envelope sequence and
    gives IFC/glTF importers real objects instead of a display-only patch.
    """
    covered_lower_walls: set[str] = set()
    for upper in model.walls:
        authored = model.plan.by_tag(upper.tag)
        lower_tag = getattr(authored, "stacks_on", None)
        lower = model.wall(lower_tag) if lower_tag else None
        if lower is None or lower.tag in covered_lower_walls:
            continue
        gap = upper.z0_m - lower.z1_m
        sheathing = next((index for index, layer in enumerate(lower.layers)
                          if layer.function == "sheathing"), None)
        if gap <= 1e-6 or gap > 0.5 or sheathing is None:
            continue
        layers = lower.layers[sheathing:]
        if not any(layer.function == "cladding" for layer in layers):
            continue
        model.envelope_bands.append(ResolvedEnvelopeBand(
            uid=f"{lower.uid}:rim-envelope", tag=f"ENV-RIM-{lower.tag}", storey=lower.storey,
            lower_wall=lower.tag, upper_wall=upper.tag, z0_m=lower.z1_m, z1_m=upper.z0_m,
            layers=layers,
        ))
        covered_lower_walls.add(lower.tag)
