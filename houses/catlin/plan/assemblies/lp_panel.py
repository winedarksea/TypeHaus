"""The sunken court's framed walkout clad in LP SmartSide panel (notes/court_face_lp_panel.md).

EXT_2X6's own stack (studs, CDX, 4" ccSPF, vent gap, KDAT girts at 24") with the cladding
layer swapped and its acrylic coat outboard, aligned on `sheathing-ext` so nothing indoors
moves. The girts at 24" are off LP's 16" table (owner, 2026-11-24: sheltered, small, cheap to
replace); the vertical joints are backed and battened (decision in the note).
"""
from typehaus import Layer, LayerFunction, inch

from .envelope_walls import EXT_2X6
from .interior import _SAUNA_LINER

LP_PANEL_DEPTH = inch(0.375)   # 3/8" nominal, 0.354" actual (LP catalog 2025)
_PAINT = Layer(name="paint", material_ref="lp-panel-paint-exterior", thickness=inch(0.125),
               function=LayerFunction.FINISH)


def _with_lp_panel(assembly, tag):
    layers = []
    for layer in assembly.layers:
        if layer.name == "cladding":
            # 4x8 hung vertically: one sheet covers the court's ~7'-6" walls, no horizontal
            # joint; the vertical joints take 440 trim battens (materials_lp.LP_PANEL_KIT).
            layers += [layer.model_copy(update={
                "material_ref": "lp-smartside-smooth-panel", "thickness": LP_PANEL_DEPTH,
                "sheet_length": inch(96.0),
                "joint_trim_material_ref": "lp-smartside-trim-smooth"}), _PAINT]
        elif layer.name == "outer-girt":
            # ESR-1301 s.4.3 / Table 1 fn 2: every panel edge on 2x framing, so a flat KDAT
            # 2x4 nailer is cut between the girts at each vertical joint.
            framing = layer.framing.model_copy(update={"panel_joint_nailers": True})
            layers.append(layer.model_copy(update={"framing": framing}))
        else:
            layers.append(layer)
    return assembly.model_copy(update={"tag": tag, "layers": tuple(layers),
                                       "source": f"{assembly.tag} clad in LP SmartSide smooth panel"})


EXT_2X6_LP_PANEL = _with_lp_panel(EXT_2X6, "EXT_2X6_LP_PANEL")
SAUNA_LINER_ON_EXT_2X6_LP = EXT_2X6_LP_PANEL.model_copy(update={
    "tag": "SAUNA_LINER_ON_EXT_2X6_LP",
    "layers": (*_SAUNA_LINER, *EXT_2X6_LP_PANEL.layers),
    "default_lining": (),
    "source": "EXT_2X6_LP_PANEL with the sauna liner inboard of the studs (W-B-S2-FR)"})
