# haus: editable
# Wall headers (decision #116): R602.7 sizes every bearing header from its derived load
# (resolve/header_loads.py); the house never frames one smaller than 2-2x8. Nonbearing heads
# up to 8' are the R602.7.4 flat 2x at the wall's depth.

from typehaus import HeaderStandard

HEADER_STANDARD = [
    HeaderStandard(uid="FPEZ7QS5W4", tag="HEADER-STANDARD", min_bearing_header="2-2x8"),
]
