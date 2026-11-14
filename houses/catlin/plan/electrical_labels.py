# haus: editable
# NEC field labels are derived (resolve/electrical_labels.py, schedule E-605); this holds
# only what the house alone knows and a plaque prints.
#   source_service_contacts — 705.10(2): the emergency phone of each off-site entity that
#     services the power sources. Unauthored on purpose (an owner input, never a default):
#     electrical.label_inputs reports it UNKNOWN until it is filled in.

from typehaus import LabelStandard

LABEL_STANDARD = [
    LabelStandard(uid="Z6A1C30DH7", tag="LBL-STANDARD"),
]
