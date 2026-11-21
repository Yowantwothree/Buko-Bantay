"""Dashboard page for Buko Bantay (English / Filipino / Bikol).

Kept in its own file so it does not conflict with the Account and Local Storage
parts. It only needs a list of scan records, so whoever builds local storage can
load the saved list and pass it to dashboard_html().

A record looks like this:
    {"time": "2026-11-18T14:30", "label": "leafrot", "confidence": 0.93, "unclear": False}

Have a native speaker review the Bikol text.
"""
import html
from collections import Counter
from datetime import datetime

from i18n import NAMES, class_key

KEYS = ["caterpillar", "grayleafspot", "leafrot", "healthy"]
MAX_RECORDS = 200   # keep only the latest scans
RECENT_SHOWN = 5

DASH_T = {
    "en": {
        "nav": "Dashboard", "title": "Dashboard",
        "total": "Total scans", "healthy": "Healthy", "issues": "Issues found", "unclear": "Unclear",
        "common": "Most common issue", "none": "None",
        "breakdown": "Leaf health breakdown", "recent": "Recent scans",
        "empty_title": "No scans yet",
        "empty_body": "Check a leaf and your results will show up here.",
    },
    "fil": {
        "nav": "Dashboard", "title": "Dashboard",
        "total": "Kabuuang pagsusuri", "healthy": "Malusog", "issues": "May problema", "unclear": "Hindi malinaw",
        "common": "Pinakakaraniwang problema", "none": "Wala",
        "breakdown": "Kalagayan ng mga dahon", "recent": "Mga huling pagsusuri",
        "empty_title": "Wala pang pagsusuri",
        "empty_body": "Suriin ang isang dahon at lalabas dito ang resulta.",
    },
    "bik": {
        "nav": "Dashboard", "title": "Dashboard",
        "total": "Kabuuan nin pagsusuri", "healthy": "Marahay", "issues": "May problema", "unclear": "Dai malinaw",
        "common": "Pinakadakol na problema", "none": "Mayo",
        "breakdown": "Kamugtakan kan mga dahon", "recent": "Mga hurihing pagsusuri",
        "empty_title": "Mayo pang pagsusuri",
        "empty_body": "Surion an sarong dahon asin makikita digdi an resulta.",
    },
}

# Add this to the CSS string in app.py (CSS = """...""" + DASH_CSS).
DASH_CSS = """
.stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:12px 0; }
.stat { background:#fff; border:1px solid #eadfc8; border-radius:18px; padding:12px 14px; }
.stat .num { font-size:30px; font-weight:800; color:var(--palm-dark); line-height:1.1; }
.stat .lbl { font-size:13px; color:#7a6a58; }
.stat.bad .num { color:#9a4a00; } .stat.unsure .num { color:#a11d1d; }
.stat.wide { grid-column:1 / -1; } .stat.wide .num { font-size:20px; }
.bar-row { margin:10px 0; } .bar-top { display:flex; justify-content:space-between; font-size:14px; margin-bottom:4px; }
.bar.issue span { background:#c9772b; }
.scan { display:flex; justify-content:space-between; align-items:center; gap:8px;
  padding:8px 0; border-bottom:1px solid #f1e8d4; }
.scan:last-child { border-bottom:0; }
.scan .chip { margin-bottom:0; font-size:13px; padding:4px 10px; }
.scan .when { font-size:12px; color:#7a6a58; text-align:right; }
"""

# Fake data for testing the layout before local storage exists.
SAMPLE_HISTORY = [
    {"time": "2026-11-15T09:10", "label": "healthy", "confidence": 0.96, "unclear": False},
    {"time": "2026-11-16T10:42", "label": "caterpillar", "confidence": 0.91, "unclear": False},
    {"time": "2026-11-16T10:50", "label": "leafrot", "confidence": 0.88, "unclear": False},
    {"time": "2026-11-17T15:05", "label": "healthy", "confidence": 0.55, "unclear": True},
    {"time": "2026-11-18T08:30", "label": "grayleafspot", "confidence": 0.93, "unclear": False},
]


def add_record(history, probs, class_names, thr):
    """Return a new history list with the latest scan added."""
    top = max(range(len(probs)), key=lambda i: probs[i])
    record = {
        "time": datetime.now().isoformat(timespec="minutes"),
        "label": class_key(class_names[top]),
        "confidence": float(probs[top]),
        "unclear": float(probs[top]) < thr,
    }
    return [*(history or []), record][-MAX_RECORDS:]


def _when(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %I:%M %p")
    except (TypeError, ValueError):
        return ""


def _stat(value, label, kind=""):
    return f'<div class="stat {kind}"><div class="num">{value}</div><div class="lbl">{label}</div></div>'


def dashboard_html(lang, history):
    t = DASH_T[lang]
    names = NAMES[lang]
    head = f'<h2 class="page-title">{t["title"]}</h2>'

    if not history:
        return head + f'<div class="card"><h3>{t["empty_title"]}</h3><p class="muted">{t["empty_body"]}</p></div>'

    reliable = [r for r in history if not r.get("unclear")]
    counts = Counter(r["label"] for r in reliable)
    healthy = counts["healthy"]
    issues = sum(n for k, n in counts.items() if k != "healthy")
    unclear = len(history) - len(reliable)

    problems = Counter({k: n for k, n in counts.items() if k != "healthy"})
    common = names.get(problems.most_common(1)[0][0], "") if problems else t["none"]

    out = [head, '<div class="stats">',
           _stat(len(history), t["total"]),
           _stat(healthy, t["healthy"]),
           _stat(issues, t["issues"], "bad"),
           _stat(unclear, t["unclear"], "unsure"),
           _stat(html.escape(common), t["common"], "wide"),
           "</div>"]

    bars = ""
    for key in KEYS:
        n = counts[key]
        width = round(n / len(reliable) * 100) if reliable else 0
        kind = "" if key == "healthy" else "issue"
        bars += (f'<div class="bar-row"><div class="bar-top"><span>{html.escape(names[key])}</span>'
                 f'<b>{n}</b></div><div class="bar {kind}"><span style="width:{width}%"></span></div></div>')
    out.append(f'<div class="card"><h3>{t["breakdown"]}</h3>{bars}</div>')

    rows = ""
    for r in reversed(history[-RECENT_SHOWN:]):
        if r.get("unclear"):
            chip = f'<span class="chip unsure">{t["unclear"]}</span>'
        else:
            kind = "ok" if r["label"] == "healthy" else "bad"
            chip = f'<span class="chip {kind}">{html.escape(names.get(r["label"], r["label"]))}</span>'
        rows += (f'<div class="scan">{chip}<div class="when">{round(r["confidence"] * 100)}%'
                 f'<br>{_when(r.get("time"))}</div></div>')
    out.append(f'<div class="card"><h3>{t["recent"]}</h3>{rows}</div>')

    return "".join(out)
