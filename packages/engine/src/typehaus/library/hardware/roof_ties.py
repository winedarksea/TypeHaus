"""Lateral tie plates, sill anchors, hurricane and gable ties, masonry gussets.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_EMBEDDED_BEAM_ANCHOR,
    ROLE_GABLE_END_TIE,
    ROLE_GABLE_TRUSS_ANCHOR,
    ROLE_HURRICANE_TIE,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_MASONRY_GUSSET_ANGLE,
    ROLE_SILL_ANCHOR_BOLT,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON
from typehaus.library.hardware.simpson_hangers import _C_C_H_TIES
from typehaus.library.hardware.simpson_post_bases import _L_F_SSNAILS

LTP4_LATERAL_TIE_PLATE = StructuralHardware(
    tag="simpson-ltp4-lateral-tie-plate",
    name="LTP4 lateral tie plate",
    role=ROLE_LATERAL_TIE_PLATE,
    manufacturer=_SIMPSON,
    model="LTP4",
    source="Simpson Strong-Tie LTP4 lateral tie plate (strongtie.com/ltp) — transfers "
           "lateral load between a plate and the framing or rim under it",
)

# A threaded rod set in wet concrete, plus the square plate washer that IRC R602.11.1 makes
# mandatory. Two parts, one joint: they are catalogued as one item because neither is
# ordered without the other and a bolt counted without its washer is not a buildable line.
# The model string leads with "AB-" so ``cost_codes.KEY_PATTERNS`` can file it with the
# concrete sub who sets it, not with the framer who lands on it.
SILL_ANCHOR_BOLT = StructuralHardware(
    tag="sill-anchor-bolt-half-inch",
    name="1/2 in x 10 in sill anchor bolt with BP1/2 plate washer",
    role=ROLE_SILL_ANCHOR_BOLT,
    manufacturer=_SIMPSON,
    model="AB-050-10-BP",
    source="IRC R403.1.6 anchor bolt (1/2 in diameter, 7 in embedment) with the "
           "Simpson Strong-Tie BP 1/2 plate washer R602.11.1 requires "
           "(strongtie.com/bp) — set in wet concrete between the mudsill anchors",
)

H25A_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5a-hurricane-tie",
    name="H2.5A hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H2.5A",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie H2.5A tie (strongtie.com/h25a) — rafter/joist-to-plate "
           "uplift connection. **G90 zinc, so DRY wood contact only.** It took every "
           "derived bearing tie in the house until 2026-09-12, including the twenty-four "
           "on the sunken garden's treated frame, because the role held one product and "
           "``hardware_for_role`` could not ask a second question. H25AZ_HURRICANE_TIE "
           "below is that joint\'s part; this one keeps the ~270 dry ones",
    # ESR-2613 Table 1, H2.5A row. **The lateral values are the ones to notice: 110 lbf,
    # against 700 lbf uplift.** A check that compared a lateral demand against "the H2.5A's
    # 700 lb capacity" would pass a joint six times overloaded, which is precisely why
    # AllowableLoads is a vector. Footnote 2 goes further and requires a unity equation
    # across all three directions when a joint sees more than one at once.
    #
    # ** 700 -> 615 ON 2026-09-14: THE SPF NUMBER EXISTS AND THIS RECORD SAID IT DID NOT. **
    # It read: "Simpson do not print an SPF column for the hurricane ties the way they do for
    # the KBS1Z and the HGAM10, so there is no honest SPF number to record here." Half of that
    # was right. ESR-2613 has no species columns at all and governs species globally in
    # §3.2.2 at SG 0.50 — true, and true again in the June 2026 reissue. But Simpson's own
    # CATALOG splits the H/TSP table by species, and the SPF/HF uplift for this tie is **615
    # lbf at 160%**. The gap was in which document had been read, not in the data.
    #
    # **So this record now carries the SPF value**, which is the convention ``species``
    # already states: where the report gives both, record the column this house is built in.
    # The DF/SP 700 stays named in the species field, because it is the right number for the
    # same stamping bedded in southern pine — which is exactly what the H2.5AZ and H2.5ASS
    # records below are for, and why theirs did NOT move.
    #
    # It is 12% down, and the direction matters: every derived tie in this house was being
    # graded against a capacity 85 lbf higher than the framing can develop.
    #
    # **Do not derive this by factoring.** Simpson's General Note e sends a mixed-species
    # joint to the LOWEST specific gravity in it — here the SPF plate at 0.42, under an I-joist
    # flange at ~0.50 — and the only published multiplier on this page (0.86) belongs to the
    # stud-to-bottom-plate detail alone. NDS Table 12.3.3 governs individual fasteners, not a
    # tested proprietary connector whose capacity is part steel. A species Simpson does not
    # rate at all goes to their letter L-ALTSPECIES, not to arithmetic of ours.
    allowable=AllowableLoads(
        uplift_lb=615.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="SPF / HF (assigned SG 0.42 / 0.43) — the column this house is framed in, "
                "and the reason the value is 615 rather than the 700 lbf the same tie "
                "carries in DF-L / SP (SG 0.50 / 0.55). ESR-2613 publishes only the DF/SP "
                "figure; the SPF/HF column is the catalog's",
        fasteners="5 - 0.131 in x 2-1/2 in to the rafter and 5 - 0.131 in x 2-1/2 in to "
                  "the plates (ESR-3096 Table publishes 625/450/110 lbf for the same tie "
                  "with 5-SD9112 screws each side — a different fastener, different values)",
        citation=(_C_C_H_TIES + ". The SPF/HF uplift is 615 lbf; the DF/SP half of the same "
                  "row reads 700 lbf and reproduces ICC-ES ESR-2613 (Simpson hurricane ties) "
                  "Table 1, H2.5A row, read 2026-08-30 — where footnote 2 requires a unity "
                  "check across uplift + both lateral directions for simultaneous loading "
                  "and footnote 5 states the uplift is already increased for wind with no "
                  "further increase allowed. The lateral F1/F2 do not move with species on "
                  "this page: 110 lbf in both halves"),
    ),
)

H25AZ_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5az-hurricane-tie",
    name="H2.5AZ ZMAX hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    exposure=EXPOSURE_TREATED,
    manufacturer=_SIMPSON,
    model="H2.5AZ",
    source="Simpson Strong-Tie H2.5AZ — the H2.5A above in ZMAX, Simpson\'s G185 "
           "hot-dip-galvanized-after-fabrication coating (strongtie.com/h25az). **The "
           "coating is the whole record.** IRC R317.3.1 requires fasteners and connectors "
           "in contact with preservative-treated wood to be hot-dip galvanized, stainless, "
           "silicon bronze or copper; the copper in a modern ACQ/CA preservative corrodes "
           "plain G90 zinc, and Simpson publish the same instruction per part. The twenty-"
           "four ties on the sunken garden\'s treated glulam beams and KDAT porch beams "
           "were billed as G90 H2.5A until 2026-09-12, at 0 FAIL, because "
           "``hardware_for_role`` held one product per role and had no way to ask.",
    # **Same steel, same holes, same report row — only the coating differs.** ESR-2613 is a
    # structural report: it tabulates the H2.5A's allowable loads through a stated fastener
    # schedule and says nothing about zinc thickness, so the Z model is the same row. That is
    # a copy of a published value, not a derivation across a family:
    # `_H25AZ_ESR2613` names the table, the row, and the date it was read, and the ZMAX
    # coverage is the catalog's own — Simpson list the H2.5AZ under the same H2.5A entry.
    #
    # **The species caveat rides across unchanged and is, here, satisfied rather than
    # carried:** every joint this part is selected for lands on KDAT southern pine or treated
    # SYP glulam, both SG 0.55, which is inside the DF/SP column these values come from.
    #
    # ** SO THIS RECORD KEEPS 700 WHERE THE G90 H2.5A WENT TO 615 ON 2026-09-14, AND THAT IS
    # THE POINT OF THE SPLIT. ** Simpson's catalog publishes an SPF/HF column the ESR does
    # not (``_C_C_H_TIES``), and the galvanized record took it because it lands on SPF
    # plates. This one does not, because it does not. Same stamping, same report row, two
    # species columns, two houses' worth of framing — and General Note e is what decides
    # which: the LOWEST specific gravity in the connection.
    allowable=AllowableLoads(
        uplift_lb=700.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="DF-L / SP (assigned SG 0.50 / 0.55) — and unlike the galvanized record "
                "above, that is not a caveat in force here: the joints that select this "
                "part are all on SYP (KDAT and treated glulam, SG 0.55), inside the "
                "published column. The catalog's SPF/HF figure for the same tie is 615 lbf "
                "and is the galvanized record's, not this one's",
        fasteners="5 - 0.131 in x 2-1/2 in to the rafter/joist and 5 - 0.131 in x 2-1/2 in "
                  "to the plates — the carbon schedule, unchanged. **Drive it with "
                  "hot-dip-galvanized nails, not electrogalvanized**: R317.3.1 governs the "
                  "nail as much as the connector, and a G90 nail through a ZMAX tie into "
                  "treated wood is the same corrosion cell with a smaller anode",
        citation=("ICC-ES ESR-2613 (Simpson hurricane ties) Table 1, H2.5A row, read "
                  "2026-08-30 — the report tabulates the tie\'s structural capacity through "
                  "a stated nail schedule and does not distinguish the G90 and ZMAX "
                  "coatings, which are the same stamping; footnote 2 requires a unity check "
                  "across uplift + both lateral directions under simultaneous loading, "
                  "footnote 5 states the uplift already carries the wind increase"),
    ),
)
LS30_GABLE_END_TIE = StructuralHardware(
    tag="simpson-ls30-gable-end-tie",
    name="LS30 skewable angle, gable-end stud to rafter",
    role=ROLE_GABLE_END_TIE,
    manufacturer=_SIMPSON,
    model="LS30",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie LS30 skewable angle, 18 ga, 3-3/8 in long, 2-1/4 in legs, "
           "field-bent 0-135 degrees (once). One leg on the 5-1/2 in face of a gable-end "
           "stud, the other bent to the bottom flange of the TJI 230 rafter above. A trussed "
           "gable takes an LTP4 instead. **The joint is lateral, not "
           "uplift:** no rafter bears on a non-bearing gable wall, and what the tie carries "
           "is the wall's out-of-plane reaction into the roof. Replaced the H10A on "
           "2026-09-16 (owner): that row assumes a sawn 2x rafter (ESR-2613 Table 1 fn.1) "
           "and its rafter-leg nails do not fit a 1-1/2 in I-joist flange; the H6 was "
           "rejected because ESR-2613 publishes it for uplift only (F1/F2 blank).",
    # C-C-2019 p.284 publishes the LS in F1 ONLY — no F2, no uplift — and draws F1 for a
    # member crossing its support, loaded along itself. This joint loads the angle across
    # the wall; the owner's detail, not a table read. Unverified: Weyerhaeuser's rules for
    # nailing up into a TJI flange (1-1/2 in nails, so they stay inside it).
    allowable=AllowableLoads(
        lateral_f1_lb=275.0,
        load_duration_factor=1.6,
        species="SPF / HF — the column this house is framed in (DF/SP reads 320 lbf)",
        fasteners="6 - 0.148 in x 1-1/2 in, three per leg. The 3 in nail row (340 lbf SPF) "
                  "is not used: it would pass through a 1-1/2 in flange",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2019 p.284, "
                  "\"L/LS/GA Reinforcing and Skewable Angles\", LS30 row, SPF/HF "
                  "Wind/Seismic (160) column, read 2026-09-16. Installation note: the joist "
                  "must be constrained against rotation when a single LS is used per "
                  "connection"),
    ),
)

LTP4_GABLE_TRUSS_ANCHOR = StructuralHardware(
    tag="simpson-ltp4-gable-truss-anchor",
    name="LTP4 lateral tie plate, gable-end truss to top plate",
    role=ROLE_GABLE_TRUSS_ANCHOR,
    manufacturer=_SIMPSON,
    model="LTP4",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie LTP4 lateral tie plate (strongtie.com/ltp), one mid-span "
           "on each gable-end truss, bottom chord to the wall's top plate. Lateral only: "
           "uplift is the H2.5A at each heel, which the bearing rule already derives. "
           "Replaced the HGA10 on 2026-09-16 (owner).",
)

#: The heavier stainless tie on a joist crossing a beam: H10A geometry in Type 316 (owner,
#: 2026-09-22, catlin's balcony joists on their glulams). Its own record so
#: ``hardware_by_model`` does not caption it as the H10A.
H10ASS_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h10ass-hurricane-tie",
    name="H10ASS stainless hurricane tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H10ASS",
    source="Simpson Strong-Tie H10A in Type 316 stainless — joist to beam where the joist "
           "crosses a treated glulam",
    # C-C-2026 p.300 prints the H10ASS at 970/565/170 (DF/SP) with smooth-shank nails and,
    # footnote 10, the H10A's 1,040/565/285 with SCNR ring-shank nails — the H2.5ASS's rule.
    allowable=AllowableLoads(
        uplift_lb=1040.0,
        lateral_f1_lb=565.0,
        lateral_f2_lb=285.0,
        load_duration_factor=1.6,
        species="DF-L / SP — the joists are KDAT southern pine",
        fasteners="9 - SCNR Type 316 ring-shank to the joist and 9 to the beam, in place of "
                  "the catalog's 0.148 in x 1-1/2 in. **With stainless SMOOTH-shank nails "
                  "this is a 970/565/170 part**",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2026, p.300, H/TSP "
                  "table, H10A and H10ASS rows and footnotes 9-10, read 2026-09-22; "
                  + _L_F_SSNAILS + ". H10ASS is not in ICC-ES ESR-2613"),
    ),
)

H25ASS_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5ass-hurricane-tie",
    name="H2.5ASS stainless hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H2.5ASS",
    source="Simpson Strong-Tie H2.5ASS, 18 ga Type 316 stainless — the H2.5A above in "
           "stainless, and the only tie at RF-BW-CANOPY's eight truss bearings. It is a "
           "SEPARATE record and not a size within the H2.5A family on purpose: "
           '"H2.5ASS".startswith("H2.5A") is true, so without this row the canopy\'s '
           "stainless ties would silently take the galvanized tie's price and its 700 lbf. "
           "The house buys stainless at every KDAT joint (owner, 2026-09-10), and this "
           "connector is nailed into treated southern pine headers at an entry that is "
           "salted every winter.",
    # ** RESOLVED 2026-09-11, AND THE OLD NOTE'S PUZZLE IS WHAT RESOLVED IT. ** This record
    # carried no allowable for a day on the grounds that the figures in circulation for the
    # H2.5ASS were materially lower than the galvanized H2.5A's 700 lbf — a 440/75/70
    # uplift-F1-F2 row in secondary listings of the C-C catalog — and could not be tied to a
    # primary table. `_L_F_SSNAILS` explains both halves at once: the 440/75/70 row is a real
    # Simpson table, the STAINLESS SMOOTH-SHANK one, and the letter says the full carbon
    # values are recovered by substituting Strong-Drive SCNR ring-shank nails. The number was
    # not wrong; it was the answer to a different installation.
    #
    # ** WHICH MAKES THE NAIL A SPECIFICATION ITEM, NOT A PURCHASING DETAIL. ** 700 lbf here
    # is conditional on SSA8D. Drive this tie with stainless smooth-shank nails and the joint
    # is worth 440 lbf, at 0 FAIL, with nothing in the model able to tell. The demand is in
    # `notes/north_entry_piers.md` §4a — about 256 lbf per tie under 0.6W with no dead relief
    # — so the canopy survives either nail; the record says SSA8D because the next house may
    # not.
    allowable=AllowableLoads(
        uplift_lb=700.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="DF-L / SP (assigned SG 0.50 / 0.55) — in force and satisfied: this tie is "
                "nailed into treated southern pine headers (SG 0.55), inside the published "
                "column. The catalog's SPF/HF figure for the same stamping is 615 lbf "
                "(``_C_C_H_TIES``) and belongs to the G90 record, which lands on SPF "
                "plates; stainless parity is about the steel and the nails and says nothing "
                "about species either way",
        fasteners="5 - SSA8D stainless ring-shank to the rafter and 5 - SSA8D to the plates "
                  "— the letter's substitution for the catalog's 5 - 0.131 in x 2-1/2 in "
                  "(8d common) each side. **With stainless SMOOTH-shank nails instead, this "
                  "tie is a 440/75/70 part, not a 700/110/110 one**",
        citation=(_L_F_SSNAILS + ". The values are the H2.5A row of ICC-ES ESR-2613 "
                  "(Simpson hurricane ties) Table 1, read 2026-08-30; H2.5ASS is not in "
                  "that report and the parity is the letter's. ESR-2613 footnote 2 requires "
                  "a unity check across uplift + both lateral directions under simultaneous "
                  "loading, footnote 5 states the uplift already carries the wind increase"),
    ),
)

HGAM10_MASONRY_GUSSET = StructuralHardware(
    tag="simpson-hgam10-masonry-gusset-angle",
    name="HGAM10 masonry gusset angle",
    role=ROLE_MASONRY_GUSSET_ANGLE,
    manufacturer=_SIMPSON,
    model="HGAM10",
    source="Simpson Strong-Tie HGAM masonry/concrete gusset angle (strongtie.com/hgam) — "
           "#14 screws into the wood leg, Titen Turbo concrete screws into the masonry leg; "
           "1-1/2 in minimum edge distance to the anchors",
    # Florida product approval FL11473 Table 1, HGAM10 row — the SPF/HF column, which is what
    # this house frames in and which is published here (unlike the hurricane ties above,
    # Simpson do print both species for the masonry connectors).
    #
    # ** F1 630, NOT 870 — RE-VERIFIED 2026-09-21. ** The 870 (and F2 950) that search results
    # quote is FL11473-R0's (report SIM200802, 2008) note 3, superseded. R4 (sealed
    # 2017-10-19) and R5 (sealed 2020-10-13) both print 585 / 630 / 795 into, 460 away.
    #
    # F2 is directional and the table says so in footnote 5: 795 lbf for force INTO the
    # connector, 460 lbf away from it. **The lower, away-from figure is recorded**, because
    # nothing in this model orients a gusset against a load direction, and a value that only
    # holds for one sign of the load is not a capacity a check can use. The 795 is in the
    # citation for a reviewer who can establish the sign.
    #
    # **This said "the two HGAM10s at the cast column tops" until 2026-09-14, when there were
    # already twelve.** There are twenty-four now: every one of the twelve joints carries a
    # PAIR, one gusset each side of the beam, because a single angle is an eccentric rotation
    # restraint and NDS 3.3.3 wants beam ends restrained against rotation. Footnote 4 is the
    # condition that permits it — a minimum 2-1/2" member "where anchors are installed on each
    # side" — and every beam at these joints is 3" or wider.
    #
    # A pair does NOT raise the recorded number, and it is worth being explicit about why the
    # temptation exists. With gussets on opposing faces, whichever way the load goes one of
    # them takes it as force INTO the connector, so the 795 is always available to *some*
    # gusset. That is a real observation and it is still not a capacity to record here: which
    # gusset, under which load case, is a question this model cannot answer. The recorded
    # value stays 460.
    #
    # (That sentence used to lean on a second argument — "the three `lateral_uplift` items
    # are UNKNOWN pending a PE seal regardless" — which stopped being true on 2026-09-14
    # when that kind retired. It was never the load-bearing half: an unanswerable question
    # is not recordable whether or not something downstream is blocked, and a capacity that
    # only held while a register entry happened to be open would be the wrong kind of
    # number to carry here.)
    #
    # ** INTERIOR / PROTECTED USE ONLY, AND G90 ONLY. ** Simpson C-C-2021 p.252: "Products
    # shall be installed such that the Titen Turbo screws and Titen HD screw anchors are not
    # exposed to the exterior environment" — a roof or deck overhead does not make a joint
    # interior. No ZMAX/HDG/SS HGAM exists, and G90 against treated wood misses IRC R317.3.1.
    # catlin used sixteen at exterior column heads until 2026-09-21 and retyped them to the
    # cast-in HETA20Z below; the record stays for a protected joint and as a documented
    # backup (`houses/catlin/notes/column_head_connector_options.md`). Its last four (the
    # landing's stem ties) went to HL33HDG angles the same day (`hardware/ties.py`).
    allowable=AllowableLoads(
        uplift_lb=585.0,
        lateral_f1_lb=630.0,
        lateral_f2_lb=460.0,
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; the DF/SP column is 810 / 875 / 640 lbf",
        fasteners="(4) 1/4 in x 1-1/2 in SDS to the wood leg + (4) 1/4 in x 1-3/4 in "
                  "Titen 2 (or Titen Turbo) into concrete, 1-1/2 in min. edge distance, "
                  "min f'c 2,500 psi",
        citation=("Simpson Strong-Tie Florida product approval FL11473 (masonry products), "
                  "Table 1, HGAM10 row, sealed 2017-10-19, read 2026-08-30. SPF/HF column: "
                  "uplift 585, F1 630, F2 795 lbf INTO the connector / 460 lbf away "
                  "(footnote 5) — the 460 is recorded. Footnote 1: already increased 60 % "
                  "for wind. Footnote 4: a min. 2-1/2 in member thickness is required where "
                  "anchors are installed on each side. Footnote 8: min f'c 2,500 psi. "
                  "Same row in FL11473-R5 (sealed 2020-10-13); R0's 870/950 is superseded. "
                  "§9 item 4: combined directions by linear interaction <= 1.0. "
                  "https://www.floridabuilding.org/upload/PR_Tech_Docs/"
                  "FL11473_R4_AE_SIM201701%20Sealed%202017-10-19.pdf"),
    ),
)

HETA20Z_EMBEDDED_BEAM_ANCHOR = StructuralHardware(
    tag="simpson-heta20z-embedded-truss-anchor",
    name="HETA20Z embedded truss anchor (ZMAX), installed in pairs",
    role=ROLE_EMBEDDED_BEAM_ANCHOR,
    manufacturer=_SIMPSON,
    model="HETA20Z",
    source="Simpson Strong-Tie HETA heavy embedded truss anchor, 16 ga, ZMAX (G185) — the "
           "spoon cast 4\" into the pour, the 1-1/8\" strap nailed to the member's face. "
           "Cast in, so there is no post-installed concrete anchor and no anchor-exposure "
           "condition (contrast HGAM10); G185 meets IRC R317.3.1 against treated wood with "
           "HDG 16d nails",
    # ** THE ROW IS THE PAIR'S. ** FL11473 Table 3 rates two HETAs, one each face, as ONE
    # installation; a single HETA20 is Table 2's 1,810 / 340 / 770. `HeadConnector.set_rated`
    # carries that, so the grade credits the pair's value once and never per part.
    #
    # Table 3's "2- or 3-ply" row: 16d nails, 12 total (6 per strap), anchors >= 3" apart
    # (fn 6), spaced <= 1/8" wider than the member (fn 3). A 2-2x8 and a 3-2x12 are that row
    # as printed; a 3-1/2" glulam is it by WIDTH, not by ply count — a reading, flagged. Read
    # as 1-ply instead, the lateral is Table 2's single 340 lb (fn 6).
    #
    # F1 1,350 < F2 1,430: the lower is recorded, as for every tie here. ZMAX carries the
    # G90 part's published values (Simpson corrosion guide); the table prints SP only, which
    # is what every beam at catlin's column heads is.
    allowable=AllowableLoads(
        uplift_lb=2560.0,
        lateral_f1_lb=1350.0,
        lateral_f2_lb=1430.0,
        load_duration_factor=1.6,
        species="SP — Table 3 prints no other column; the PAIR's values (2- or 3-ply, "
                "concrete, 16d). A single HETA20 is 1,810 uplift / 340 F1 / 770 F2 "
                "(Table 2)",
        fasteners="(12) 16d HDG, 6 per strap, into a 2- or 3-ply member; spoons 4\" into "
                  "f'c >= 2,500 psi concrete, >= 6\" wide, 1-1/2\" min. edge distance; the "
                  "lowest four holes of each strap filled (Table 2 fn 2)",
        citation=("Simpson Strong-Tie Florida product approval FL11473 (masonry products), "
                  "Table 3, double HETA, concrete, 2- or 3-ply, sealed 2017-10-19, read "
                  "2026-09-21: uplift 2,560, F1 1,350, F2 1,430 lb. Note 1: already +60 % "
                  "for wind. Note 6: lateral applies only to 2- or 3-ply with anchors >= 3\" "
                  "apart. Note 7: F1 may add 1/16\" deflection when not wrapped over"),
    ),
)
