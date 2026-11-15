"""NFPA 780 (lightning protection) sections, beside ``model/nec.py``."""

from __future__ import annotations

from typing import Final


class NFPA780:
    """NFPA 780 (lightning protection), not NEC: cited by advisories only. The owner read
    4.1-4.5, 4.12.8-4.15 and 4.19 in print on 2026-11-14 (2026 ed.); paraphrase and what
    grades each in
    ``docs/code-notes/nfpa-780-paraphrase.md``. GROUND_RING is a cross-reference only."""

    EDITION: Final = "NFPA 780-2026"
    CONDUCTORS: Final = "NFPA 780 4.1.1.1 / Table 4.1.1.1.1"
    GROUND_RING: Final = "NFPA 780 4.12.4"
    DISSIMILAR_METALS: Final = "NFPA 780 4.2.2.3.1 / 4.3.4.3 (no Al within 18 in of earth)"
    COMMON_GROUNDING: Final = "NFPA 780 4.13"
    SURGE: Final = "NFPA 780 4.19.2"
