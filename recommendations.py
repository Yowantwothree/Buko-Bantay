"""Recommendations and references shown by the prototype app.

Every statement is tied to the numbered sources in SOURCES. Edit the text here
(not in app.py) and keep the source numbers in step with what each source says.
"""
import re

DISCLAIMER = (
    "This tool is decision support, not a diagnosis. Pesticide and fungicide "
    "products, rates and legal status differ between countries, and several "
    "sources below are from India. Confirm any chemical treatment with your "
    "local agricultural technician or extension office and follow the product label."
)

SOURCES = {
    1: "Tamil Nadu Agricultural University (TNAU) Agritech Portal. Black Headed "
       "Caterpillar Management in Coconut. "
       "https://agritech.tnau.ac.in/crop_protection/coconut/crop_prot_crop_insect_oil_coconut_4.html",
    2: "ICAR-Central Plantation Crops Research Institute (CPCRI). Bio-management of "
       "coconut black headed caterpillar in Arsikere, Karnataka. "
       "https://cpcri.gov.in/page/article/Bio_management",
    3: "Lu, H., Lyu, B., Tang, J., Wu, Q., Wyckhuys, K.A.G., Le, K.H., Chongchitmate, P., "
       "Qiu, H., & Zhang, Q. (2023). Ecology, invasion history and biodiversity-driven "
       "management of the coconut black-headed caterpillar Opisina arenosella in Asia. "
       "Frontiers in Plant Science, 14, 1116221. https://doi.org/10.3389/fpls.2023.1116221",
    4: "Tsatsia, H., & Jackson, G. Coconut leaf spots (090). Pacific Pests, Pathogens, "
       "Weeds & Pesticides (SPC/ACIAR). "
       "https://apps.lucidcentral.org/pppw_v13/text/web_mini/entities/coconut_leaf_spots_090.htm",
    5: "Anupama, N. (1997). Effect of management practices on the incidence and intensity "
       "of grey blight disease of coconut [M.Sc. thesis]. College of Agriculture, Vellayani, "
       "Kerala Agricultural University. "
       "https://krishikosh.egranth.ac.in/items/5cf9d94a-e181-42c8-aa54-1e9d2979395f",
    6: "Khan, M.A.H., & Hossain, I. (2014). Leaf spot disease of coconut seedling and its "
       "eco-friendly management. Journal of the Bangladesh Agricultural University, 11(2), "
       "199-208. https://doi.org/10.3329/jbau.v11i2.19894",
    7: "Centre for e-Learning, Kerala Agricultural University. Coconut: Grey blight "
       "(Pestalotia palmarum). https://celkau.in/crops/plantation/coconut/grey.php",
    8: "Tamil Nadu Agricultural University (TNAU) Agritech Portal. Coconut: Leaf rot "
       "disease. https://agritech.tnau.ac.in/crop_protection/coconut_diseases_6.html",
    9: "Srinivasan, N., & Gunasekaran, M. (1999). Coconut leaf rot disease complex: a "
       "review. CORD, 15(1). https://doi.org/10.37833/cord.v15i01.323",
    10: "Asian and Pacific Coconut Community (APCC) Library. Evaluation of fungicides and "
        "antagonistic organism against major pathogens of leaf rot disease of coconut and "
        "their eco-friendly management (abstract). "
        "https://apccsec.org/library-sub/media.php/page-reviewer-id-191",
}

# Keys are class names reduced to lowercase letters only (see _key), so
# "Gray Leaf Spot" and "gray_leaf_spot" both map to "grayleafspot".
RECOMMENDATIONS = {
    "caterpillar": {
        "title": "Coconut black-headed caterpillar (Opisina arenosella)",
        "summary": (
            "The larvae live in silk-and-frass galleries on the underside of leaflets "
            "and eat the leaf tissue. This leaves dried patches on the lower leaves, and "
            "severe infestations give the plantation a scorched look.",
            [1, 3],
        ),
        "actions": [
            ("Cut and burn the heavily infested outer fronds. TNAU advises doing this "
             "with the first affected leaves at the start of the summer season, and the "
             "ICAR-CPCRI field demonstration removed and burned 2-3 heavily infested "
             "outer fronds.", [1, 2]),
            ("Make biological control the core of the response. Release stage-specific "
             "parasitoids (Goniozus nephantidis and Bracon brevicornis in the ICAR-CPCRI "
             "demonstration) when the larvae are in the 2nd or 3rd instar. A literature "
             "review reports that scheduled releases of lab-reared parasitoids lowered "
             "infestation by up to 95%, and that resident ants killed 75-98% of egg "
             "masses in the canopy.", [1, 2, 3]),
            ("Treat chemical spraying as a last resort, only for very severe infestations "
             "on young palms where biological control is unlikely to work (TNAU says to "
             "spray the underside of the fronds). The ICAR-CPCRI demonstration used a "
             "single spray of chlorantriniliprole. Wait three weeks after any spray "
             "before releasing parasitoids.", [1, 2]),
            ("Support palm health with proper fertilization, irrigation and sanitation; "
             "the review found biological control works best when combined with these "
             "measures.", [2, 3]),
        ],
    },
    "grayleafspot": {
        "title": "Grey leaf spot / grey blight (Pestalotiopsis palmarum)",
        "summary": (
            "Grey spots up to about 15 mm long with a thin dark-brown border and tiny "
            "black dots (fruiting bodies), mostly on older leaves. Spores spread by rain "
            "and wind, so it is more common in wet weather. It is generally considered a "
            "disease of low importance, but severe blight on older leaves points to "
            "unfavourable growing conditions.",
            [4],
        ),
        "actions": [
            ("Improve nutrition and spacing. In a Kerala study, grey blight intensity was "
             "highest in closely spaced palms that received no fertilizer and lowest in "
             "widely spaced palms with higher fertilizer levels.", [4, 5]),
            ("Remove severely affected older leaves and burn them.", [7]),
            ("In nurseries, reduce shade. A Trichoderma harzianum-based biofungicide, "
             "alone or combined with the fungicide Bavistin, controlled leaf spot on "
             "coconut seedlings.", [4, 6]),
            ("Spraying mature palms is generally not recommended because treatment "
             "would likely be uneconomic.", [4]),
        ],
    },
    "leafrot": {
        "title": "Leaf rot (disease complex)",
        "summary": (
            "Leaf rot is caused by a complex of fungi (Colletotrichum gloeosporioides, "
            "Exserohilum rostratum and Fusarium spp.). It starts as water-soaked brown "
            "lesions on the spear leaf, and in severe cases the spear fails to unfurl. "
            "It is closely linked to root (wilt) disease, so check the palm for root "
            "(wilt) symptoms too.",
            [8, 9],
        ),
        "actions": [
            ("Remove the rotten portions of the spear and of the two adjacent leaves.",
             [8]),
            ("For mild infections, TNAU recommends pouring a fungicide solution "
             "(hexaconazole or mancozeb) at the base of the spindle leaf, with 2-3 rounds "
             "being sufficient. Use only products registered locally and follow the label.",
             [8]),
            ("Consider biological options: a talc-based Pseudomonas fluorescens "
             "preparation consistently improved leaf-rot-affected palms in field trials, "
             "and bio-agents can be combined with fungicides at minimal concentrations.",
             [10]),
            ("Practise strict phytosanitation and an integrated, multi-measure approach; "
             "the review stresses both for sound management.", [9]),
        ],
    },
    "healthy": {
        "title": "No disease detected",
        "summary": ("The model classifies this leaf as healthy.", []),
        "actions": [
            ("Keep monitoring. Look for silk-and-frass galleries and dried patches on "
             "the underside of lower leaflets (black-headed caterpillar) and for "
             "water-soaked brown lesions on the spear leaf (leaf rot).", [1, 8]),
            ("Maintain good agronomy. Proper fertilization, irrigation and adequate "
             "spacing were linked to lower pest and disease pressure in the cited "
             "studies.", [3, 5]),
            ("Treat severe spotting on older leaves as a sign of poor growing "
             "conditions and check palm nutrition.", [4]),
        ],
    },
}


def _key(name):
    return re.sub(r"[^a-z]", "", name.lower())


def _refs(ids):
    return f" [{', '.join(str(i) for i in ids)}]" if ids else ""


def format_recommendation(class_name, confidence, min_confidence):
    """Return Markdown with the advice for a predicted class and its references."""
    entry = RECOMMENDATIONS.get(_key(class_name))
    parts = []

    if confidence < min_confidence:
        parts.append(
            f"> **Low confidence ({confidence:.0%}).** Retake the photo (one leaf, "
            "daylight, in focus) and have the palm checked before acting on this result.\n"
        )
    if entry is None:
        parts.append(f"No recommendation is stored for **{class_name}** yet.")
        return "\n".join(parts)

    text, ids = entry["summary"]
    used = set(ids)
    parts.append(f"## {entry['title']}\n")
    parts.append(text + _refs(ids) + "\n")
    parts.append("### Recommended actions")
    for number, (action, action_ids) in enumerate(entry["actions"], start=1):
        parts.append(f"{number}. {action}{_refs(action_ids)}")
        used.update(action_ids)

    parts.append("\n### References")
    for i in sorted(used):
        parts.append(f"[{i}] {SOURCES[i]}\n")
    parts.append(f"*{DISCLAIMER}*")
    return "\n".join(parts)
