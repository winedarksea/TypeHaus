# haus: editable
# The east canopy post's structural wood and separate PVC finish.

from typehaus import Assembly, Layer, LayerFunction, inch

POST_KDAT_WRAPPED_PVC = Assembly(
    tag="POST_KDAT_WRAPPED_PVC",
    layers=(
        Layer(name="6x6-kdat-core", material_ref="kdat", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="vented-pvc-jacket", material_ref="pvc-cellular", thickness=inch(0.5),
              function=LayerFunction.FINISH),
    ),
    source="East canopy posts PT-BW-RE/RNE: 6x6 KDAT structural core, 8x8 nominal four-sided cellular PVC jacket as a nonstructural finish. Leave an open, drained cavity above the pier wash and vent beneath the head cap; make one face removable for inspection. Keep the ABU66SS standoff open and fasten the jacket independently of both structural connectors (canopy_garage_diaphragm.md §5a).",
)
