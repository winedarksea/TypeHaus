# haus: editable
# Kitchen sink connections; set-out and fitting envelopes: notes/kitchen_sink_installation.md.
# Main room AFF = authored elevation minus 15/16 inch (the resolved concrete-cap finish).
# The purchased tubular J-bend is in install_parts, not another length of PVC pipe.

from typehaus import DrainCleanout, PipeRun, PipeSystem, inch, pt

KITCHEN_CONNECTIONS = [
    DrainCleanout(uid="KTCO24AAAA", tag="CO-M-KITCH-ARM",
                  pipe_ref="PR-M-KITCH-TRAP-ARM",
                  position=pt(inch(347), inch(423.49)), fitting_elevation=inch(17.041666667),
                  cap_position=pt(inch(345.5), inch(419)), cap_elevation=inch(17.041666667),
                  direction="one_way", access="cabinet",
                  clear_width=inch(18), clear_depth=inch(18)),
    # 8-inch developed arm at 1/4 inch/ft; tee is 16 AFF. Disposer points WEST,
    # keeping the trap clear of the two PEX risers east of the drain.
    PipeRun(uid="KTARM24AAA", tag="PR-M-KITCH-TRAP-ARM", system=PipeSystem.DRAIN,
            path=(pt(inch(347), inch(420.49)), pt(inch(347), inch(423.49)),
                  pt(inch(352), inch(423.49))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(17.104166667), inch(17.041666667), inch(16.9375)),
            serves=("FX-M-KITCH-SINK",)),
    # 2-inch waste below the vented tee. Two 45s return to the existing sleeve;
    # the 6.5-inch plan offset has 6.5 inches of fall, above the slab.
    PipeRun(uid="KTDRP24AAA", tag="PR-M-KITCH-LOCAL-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(inch(352), inch(423.49)), pt(inch(352), inch(423.49)),
                  pt(inch(352), inch(416.99))),
            diameter=inch(2), material="pvc",
            elevations=(inch(16.9375), inch(12.9375), inch(6.4375)),
            serves=("FX-M-KITCH-SINK",)),
    # Below flood-rim+6, offsets rise at 45 degrees (UPC vertical), never flat.
    # The east-going diagonal passes below the kitchen rough sill, then rises
    # east of its jack/king pack. The final 18-inch leg rises 3/16 inch.
    PipeRun(uid="KTVNT24AAA", tag="PR-M-KITCH-LOCAL-VENT", system=PipeSystem.VENT,
            path=(pt(inch(352), inch(423.49)), pt(inch(352), inch(423.49)),
                  pt(inch(352), inch(429)), pt(inch(374), inch(429)),
                  pt(inch(374), inch(429)), pt(inch(392), inch(429))),
            diameter=inch(1.5), material="pvc",
            elevations=(inch(16.9375), inch(20.9375), inch(26.4475),
                        inch(48.4475), inch(110.8125), inch(111)),
            wall_refs=(None, None, "W-M-N1", "W-M-N1", "W-M-N1"),
            serves=("FX-M-KITCH-SINK",)),
]
