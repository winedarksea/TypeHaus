# haus: editable
# NEC field labels are derived (resolve/electrical_labels.py, schedule E-605); this holds
# only what the house alone knows and a plaque prints.
#   source_service_contacts — 705.10(2): the emergency phone of each off-site entity that
#     services the power sources. () since 2026-11-14 (owner): the owner maintains the PV
#     and ESS, so no off-site servicer is listed. Two placards: 705.10 (with 702.7(A)(1))
#     and 230.70(D)'s own directory.

from typehaus import LabelStandard

LABEL_STANDARD = [
    LabelStandard(uid="Z6A1C30DH7", tag="LBL-STANDARD", source_service_contacts=()),
]
