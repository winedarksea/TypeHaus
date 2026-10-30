"""One owner parameter for themed bath faucets; utility faucets stay stainless."""

from typehaus.model import Material, ProductPart
from typehaus.source.parameter_overrides import parameter

THEME = parameter("finish.bath_theme", "chrome")
_SUFFIX = {"chrome": "", "brushed-nickel": "BN"}[THEME]
THEME_FAUCET_PART = ProductPart(role="faucet", product_ref=f"PROD-MOEN-6702{_SUFFIX}")
THEME_MATERIAL_REFS = {"faucet": f"faucet-{THEME}"}
UTILITY_FAUCET_PART = ProductPart(role="faucet", product_ref="PROD-KRAUS-KBF-1401-SFS")
UTILITY_MATERIAL_REFS = {"faucet": "faucet-stainless"}
FAUCET_MATERIALS = (
    Material(tag="faucet-chrome", name="Polished chrome faucet finish", color="#cbd2d8", finish="polished"),
    Material(tag="faucet-brushed-nickel", name="Brushed nickel faucet finish", color="#aaa79e", finish="brushed"),
    Material(tag="faucet-stainless", name="Spot-free stainless faucet finish", color="#aeb6b8", finish="brushed"),
)
