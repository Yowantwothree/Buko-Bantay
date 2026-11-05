"""Texts (English / Filipino / Bikol) and HTML builders for Buko Bantay.

No gradio or model imports here, so it is easy to test and edit.
Filipino/Bikol advice is a shortened version of the English advice and keeps the
same reference numbers. Have a native speaker review the Bikol text.
"""
import html
import re

from recommendations import DISCLAIMER, RECOMMENDATIONS, SOURCES

LANGS = [("English", "en"), ("Filipino", "fil"), ("Bikol", "bik")]

T = {
    "en": {
        "tagline": "Coconut leaf health checker",
        "home_title": "Check a coconut leaf",
        "home_hint": "Take a clear photo of one leaf in good daylight, or upload one from your gallery.",
        "photo": "Leaf photo", "analyze": "Analyze photo",
        "no_photo": "Please take or upload a photo first.",
        "nav_home": "Home", "nav_settings": "Settings",
        "confidence": "Confidence", "unclear": "Unclear photo",
        "low_title": "We can't give a reliable result",
        "low_body": "The photo may be too blurry, or no coconut leaf was detected. Retake the photo: one leaf, in daylight, in focus, filling the frame. No recommendation is shown for unclear results.",
        "advice": "What you can do", "refs": "References", "again": "Check another leaf",
        "disc_title": "Disclosure",
        "disclosure": DISCLAIMER + " The model was tested on 132 leaf photos: 97.7% accurate overall, but it missed 3 of 9 healthy leaves. If it reports a disease on a leaf that looks healthy, double-check before treating.",
        "settings": "Settings", "language": "Language", "strict": "Warning strictness",
        "strict_opts": ["Strict (90%)", "Normal (80%)", "Relaxed (65%)"],
        "strict_help": "Stricter settings show the unclear-photo warning more often.",
        "about_title": "About",
        "about": "Buko Bantay checks coconut leaf photos for caterpillar damage, gray leaf spot and leaf rot.",
    },
    "fil": {
        "tagline": "Tagasuri ng kalusugan ng dahon ng niyog",
        "home_title": "Suriin ang dahon ng niyog",
        "home_hint": "Kumuha ng malinaw na litrato ng isang dahon sa liwanag ng araw, o mag-upload mula sa gallery.",
        "photo": "Litrato ng dahon", "analyze": "Suriin ang litrato",
        "no_photo": "Kumuha o mag-upload muna ng litrato.",
        "nav_home": "Home", "nav_settings": "Mga Setting",
        "confidence": "Kumpiyansa", "unclear": "Hindi malinaw ang litrato",
        "low_title": "Hindi namin masabi nang tiyak ang resulta",
        "low_body": "Maaaring malabo ang litrato o walang nakitang dahon ng niyog. Muling kumuha: isang dahon, sa liwanag ng araw, malinaw, at sakop ang buong frame. Walang rekomendasyong ipapakita sa hindi malinaw na resulta.",
        "advice": "Ano ang maaari mong gawin", "refs": "Mga sanggunian", "again": "Suriin ang ibang dahon",
        "disc_title": "Paunawa",
        "disclosure": "Ang gabay na ito ay pantulong sa pagpapasya, hindi diyagnosis. Magkakaiba ang mga pestisidyo at fungicide, ang dosis at legalidad ng mga ito sa bawat bansa, at karamihan sa mga sanggunian ay mula sa India. Kumonsulta sa lokal na agricultural technician bago gumamit ng kemikal at sundin ang label. Sinubok ang modelo sa 132 litrato: 97.7% ang tama, ngunit hindi nito nakilala ang 3 sa 9 na malulusog na dahon. Kung may sakit na iniulat sa dahong mukhang malusog, doblehin ang pagsusuri bago gamutin.",
        "settings": "Mga Setting", "language": "Wika", "strict": "Higpit ng babala",
        "strict_opts": ["Mahigpit (90%)", "Karaniwan (80%)", "Maluwag (65%)"],
        "strict_help": "Mas madalas lumalabas ang babalang hindi malinaw ang litrato kapag mas mahigpit.",
        "about_title": "Tungkol dito",
        "about": "Sinusuri ng Buko Bantay ang mga litrato ng dahon ng niyog para sa pinsala ng higad, abuhing batik sa dahon, at pagkabulok ng dahon.",
    },
    "bik": {
        "tagline": "Tagasuri kan kamarhayan kan dahon nin niyog",
        "home_title": "Surion an dahon nin niyog",
        "home_hint": "Magkua nin malinaw na litrato kan sarong dahon sa liwanag nin aldaw, o mag-upload hali sa gallery.",
        "photo": "Litrato kan dahon", "analyze": "Susiyaton an litrato",
        "no_photo": "Magkua o mag-upload nin litrato primero.",
        "nav_home": "Harong", "nav_settings": "Mga Setting",
        "confidence": "Kumpiyansa", "unclear": "Dai malinaw an litrato",
        "low_title": "Dai kami makakapagsabi nin tunay na resulta",
        "low_body": "Mahilas pa an litrato o dai nin nahiling na dahon nin niyog. Magkua giraray: sarong dahon, sa liwanag nin aldaw, malinaw, asin punô an frame. Dai nin irerekomendar sa dai malinaw na resulta.",
        "advice": "Ano an puwede mong gibohon", "refs": "Mga sanggunian", "again": "Surion an iba pang dahon",
        "disc_title": "Paunawa",
        "disclosure": "An gabay na ini tabang sa pagpapasya, dai diyagnosis. Magkakaiba an mga pestisidyo asin fungicide, an dosis asin pagkalehitimo kaiyan sa kada nasyon, asin an kadaklan sa mga sanggunian hali sa India. Kumonsulta sa lokal na agricultural technician bago gumamit nin kemikal asin sundon an label. Sinubukan an modelo sa 132 litrato: 97.7% an tama, pero dai nakilala kan modelo an 3 sa 9 na marahay na dahon. Kun may sakit na iniulat sa dahon na garo marahay, doblehon an pagsusuri bago gamuton.",
        "settings": "Mga Setting", "language": "Tataramon", "strict": "Higpit kan babala",
        "strict_opts": ["Mahigpit (90%)", "Normal (80%)", "Maluwag (65%)"],
        "strict_help": "Mas madalas an babala na dai malinaw an litrato kun mas mahigpit.",
        "about_title": "Manungod digdi",
        "about": "Sinusuri kan Buko Bantay an mga litrato nin dahon nin niyog para sa pinsala kan higad, abuhon na batik sa dahon, asin pagkaburok kan dahon.",
    },
}
THRESHOLDS = [0.90, 0.80, 0.65]

NAMES = {
    "en": {"caterpillar": "Caterpillar damage", "grayleafspot": "Gray leaf spot", "healthy": "Healthy leaf", "leafrot": "Leaf rot"},
    "fil": {"caterpillar": "Pinsala ng higad", "grayleafspot": "Abuhing batik sa dahon", "healthy": "Malusog na dahon", "leafrot": "Pagkabulok ng dahon"},
    "bik": {"caterpillar": "Pinsala kan higad", "grayleafspot": "Abuhon na batik sa dahon", "healthy": "Marahay na dahon", "leafrot": "Pagkaburok kan dahon"},
}

# (text, source ids) - same reference numbers as recommendations.py
ADVICE = {
    "fil": {
        "caterpillar": [
            ("Putulin at sunugin ang mga pinakamalubhang apektadong dahon sa labas.", [1, 2]),
            ("Gamitin ang biyolohikal na kontrol: maglabas ng parasitoid (Goniozus nephantidis at Bracon brevicornis) kapag nasa 2nd o 3rd instar ang higad.", [1, 2, 3]),
            ("Huling opsyon lang ang pag-spray ng pamatay-insekto, para sa napakalubhang pinsala sa batang puno. Maghintay ng tatlong linggo bago maglabas ng parasitoid.", [1, 2]),
            ("Alagaan ang puno: sapat na abono at patubig, at panatilihing malinis ang taniman.", [2, 3]),
        ],
        "grayleafspot": [
            ("Pagbutihin ang nutrisyon at luwag ng pagitan ng mga puno; mas kaunti ang sakit kapag sapat ang abono at maluwag ang tanim.", [4, 5]),
            ("Alisin at sunugin ang mga matatandang dahong malubha ang tama.", [7]),
            ("Sa nursery, bawasan ang lilim; nakatulong ang biofungicide na Trichoderma harzianum sa mga punla.", [4, 6]),
            ("Karaniwang hindi inirerekomendang mag-spray sa malalaking puno dahil malamang na hindi sulit ang gastos.", [4]),
        ],
        "leafrot": [
            ("Alisin ang bulok na bahagi ng usbong at ng dalawang katabing dahon.", [8]),
            ("Para sa banayad na kaso, ibuhos sa puno ng usbong ang solusyon ng fungicide (hexaconazole o mancozeb), 2-3 beses. Gamitin lang ang produktong rehistrado sa inyo at sundin ang label.", [8]),
            ("Maaaring subukan ang biyolohikal na paraan, tulad ng talc-based na Pseudomonas fluorescens.", [10]),
            ("Panatilihin ang mahigpit na kalinisan ng taniman at tingnan din kung may sintomas ng root wilt, na kaugnay ng leaf rot.", [9]),
        ],
        "healthy": [
            ("Patuloy na magbantay: tingnan sa ilalim ng mga dahon ang sapot at dumi ng higad, at ang basang kayumangging sugat sa usbong.", [1, 8]),
            ("Panatilihin ang maayos na pag-aalaga: sapat na abono, patubig, at maluwag na pagitan ng mga puno.", [3, 5]),
        ],
    },
    "bik": {
        "caterpillar": [
            ("Putulon asin sunogon an mga pinakagrabeng apektadong dahon sa luwas.", [1, 2]),
            ("Gamiton an biyolohikal na kontrol: magpakawala nin parasitoid (Goniozus nephantidis asin Bracon brevicornis) kun nasa 2nd o 3rd instar an higad.", [1, 2, 3]),
            ("Huring opsyon sana an pag-spray nin pamatay-insekto, para sa grabeng pinsala sa bata pang kahoy. Maghalat nin tulong semana bago magpakawala nin parasitoid.", [1, 2]),
            ("Alagahan an kahoy: sapat na abono asin patubig, asin pagdalisayon an tanoman.", [2, 3]),
        ],
        "grayleafspot": [
            ("Pagayunon an nutrisyon asin an luwag kan pagitan kan mga kahoy; mas guti an sakit kun sapat an abono asin maluwag an tanom.", [4, 5]),
            ("Kuahon asin sunogon an mga gurang na dahon na grabe an tama.", [7]),
            ("Sa nursery, bawasan an lilim; nakatabang an biofungicide na Trichoderma harzianum sa mga punla.", [4, 6]),
            ("Sa kadaklan dai nirerekomendar an pag-spray sa dakulang kahoy ta mayo man sulit an gastos.", [4]),
        ],
        "leafrot": [
            ("Kuahon an buruk na parte kan usbong asin kan duwang katabing dahon.", [8]),
            ("Para sa banayad na kaso, ibubo sa puno kan usbong an solusyon nin fungicide (hexaconazole o mancozeb), 2-3 beses. Gamiton sana an produktong rehistrado digdi asin sundon an label.", [8]),
            ("Puwedeng sinubahan an biyolohikal na paagi, arog kan talc-based na Pseudomonas fluorescens.", [10]),
            ("Padagos na pagdalisayon an tanoman asin hilingon man kun may sintomas nin root wilt, na kaugnay kan leaf rot.", [9]),
        ],
        "healthy": [
            ("Padagos na magbantay: hilingon sa ilalom kan mga dahon an sapot asin tai kan higad, asin an basâ na kayumangging sugat sa usbong.", [1, 8]),
            ("Ipadagos an marhay na pag-alaga: sapat na abono, patubig, asin maluwag na pagitan kan mga kahoy.", [3, 5]),
        ],
    },
}


def class_key(name):
    return re.sub(r"[^a-z]", "", name.lower())


def _advice(lang, key):
    """Return (summary, [(text, ids), ...]) for a class in a language."""
    if lang == "en":
        entry = RECOMMENDATIONS.get(key)
        if entry:
            return entry["summary"], entry["actions"]
        return ("", []), []
    return ("", []), ADVICE[lang].get(key, [])


def _refs(ids):
    return f' <sup class="ref">[{", ".join(map(str, ids))}]</sup>' if ids else ""


def _link(text):
    return re.sub(r"(https?://\S+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', html.escape(text))


def header_html(lang):
    return (f'<div class="appbar"><div class="logo">B</div><div><div class="brand">Buko Bantay</div>'
            f'<div class="tag">{T[lang]["tagline"]}</div></div></div>')


def home_html(lang):
    t = T[lang]
    return f'<div class="hero"><h2>{t["home_title"]}</h2><p>{t["home_hint"]}</p></div>'


def settings_html(lang):
    t = T[lang]
    return (f'<h2 class="page-title">{t["settings"]}</h2>'
            f'<div class="card"><h3>{t["about_title"]}</h3><p>{t["about"]}</p></div>')


def result_html(lang, thr, probs, class_names):
    t = T[lang]
    top = max(range(len(probs)), key=lambda i: probs[i])
    conf = float(probs[top])
    pct = round(conf * 100)
    key = class_key(class_names[top])
    low = conf < thr

    if low:
        chip = f'<span class="chip unsure">{t["unclear"]}</span>'
    else:
        name = NAMES[lang].get(key, class_names[top])
        chip = f'<span class="chip {"ok" if key == "healthy" else "bad"}">{html.escape(name)}</span>'

    out = [f'<div class="card">{chip}<div class="muted">{t["confidence"]}</div>'
           f'<div class="pct">{pct}%</div><div class="bar"><span style="width:{pct}%"></span></div></div>']

    if low:
        out.append(f'<div class="warn"><b>&#9888; {t["low_title"]}</b><p>{t["low_body"]}</p></div>')
    else:
        (summary, sum_ids), actions = _advice(lang, key)
        used = set(sum_ids) | {i for _, ids in actions for i in ids}
        body = f"<p>{html.escape(summary)}{_refs(sum_ids)}</p>" if summary else ""
        body += "<ol>" + "".join(f"<li>{html.escape(a)}{_refs(ids)}</li>" for a, ids in actions) + "</ol>"
        out.append(f'<div class="card"><h3>{t["advice"]}</h3>{body}</div>')
        if used:
            refs = "".join(f"<li>[{i}] {_link(SOURCES[i])}</li>" for i in sorted(used))
            out.append(f'<details class="card"><summary>{t["refs"]}</summary><ul class="refs">{refs}</ul></details>')

    out.append(f'<div class="disc"><b>{t["disc_title"]}</b><p>{html.escape(t["disclosure"])}</p></div>')
    return "".join(out)
