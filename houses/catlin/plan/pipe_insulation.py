# haus: editable
# Pipe-insulation specs, declared once (decision #154): each hot-water run's `insulation`
# string names a row here, and `mep.pipe_insulation` grades its R against R-3 (2012 IECC
# R403.4.2 as Minn. R. 1322.0010 adopts it). The R is the product's own figure for the wall,
# not thickness x R/in: Owens Corning 722579 fiberglass pipe insulation, k 0.16 by ASTM C547
# (the figures the runs' specs already state; the datasheet is not re-read here).

from typehaus import PipeInsulationRow, PipeInsulationStandard, inch

_OC = "Owens Corning 722579 fiberglass pipe insulation, ASJ jacket, k 0.16 (ASTM C547); R as the run spec states it, datasheet not re-read (2026-11-27)"

PIPE_INSULATION_STANDARD = [
    PipeInsulationStandard(
        uid="1S808ACS2G", tag="PIPE-INSULATION-STANDARD",
        insulations=(
            PipeInsulationRow(spec='1" fiberglass sleeve, ASJ jacket (R-3.5)',
                              thickness=inch(1), r_value=3.5, source=_OC),
            PipeInsulationRow(spec='1/2" fiberglass sleeve, ASJ jacket (R-3.1)',
                              thickness=inch(0.5), r_value=3.1, source=_OC),
        )),
]
