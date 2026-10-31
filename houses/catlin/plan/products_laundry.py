"""The laundry utility tub, selected 2026-10-24: identity only, never a price.

The cabinet and its faucet are one purchase, bought twice: the main-floor laundry tub and
the furnace room's utility sink. The listing carries the flex-neck faucet with a garden-hose
adapter; the laundry declines it, the utility sink uses it behind a hose-connection vacuum
breaker (PA-B-USINK-VB). Spec sheet not retrieved: the
listing page refused automated reads, so every dimension here is the listing's own.
"""

from typehaus.model import Product

GLACIER_BAY_QL033Y = Product(
    tag="PROD-GLACIER-BAY-QL033Y", brand="Glacier Bay", model="QL033Y",
    name="24 x 21 x 34 in. stainless laundry utility tub in a white cabinet",
    url="https://www.homedepot.com/p/Glacier-Bay-24-in-W-x-21-in-D-x-34-in-L-Stainless-Steel-Laundry-Utility-Sink-with-Faucet-and-Cabinet-in-White-QL033Y/206057007",
    source="Home Depot listing, internet #206057007, read 2026-10-24 (search summary; the page "
           "returned 403 to automated reads, spec sheet not retrieved). 24 x 21 x 34 in., "
           "stainless basin, white cabinet. Rim is the cabinet top at 34 in.; the declared 43 in. "
           "box includes the gooseneck. Basin capacity, drain size and warranty unverified.",
)
GLACIER_BAY_QL033Y_FAUCET = Product(
    tag="PROD-GLACIER-BAY-QL033Y-FAUCET", brand="Glacier Bay", model="QL033Y bundled faucet",
    name="Flex-neck laundry faucet with sprayer and garden-hose adapter, bundled with QL033Y",
    source="Bundled with PROD-GLACIER-BAY-QL033Y, read 2026-10-24 (listing summary only; HD "
           "Q&A, re-read 2026-10-31, names the hose adapter). The adapter's thread (3/4 in. "
           "GHT assumed), finish, spout reach and supply connections are unverified: confirm "
           "on the delivered carton.",
)

LAUNDRY_PRODUCTS = (GLACIER_BAY_QL033Y, GLACIER_BAY_QL033Y_FAUCET)
