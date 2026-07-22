#!/usr/bin/env python3
"""
Generates an animated terminal-style GitHub profile card (dark.svg + light.svg)
for Shivam Shukla (github.com/Shivam-Shukla0).

Edit CONFIG / INFO below and re-run:
    python generate_profile.py

The ASCII portrait on the left comes from portrait.txt, which is produced by
photo_to_ascii.py (run that only when you want to change the photo).

Repo/star/follower stats are fetched live from the GitHub API when this runs
inside GitHub Actions; if the API is unreachable it falls back to "-".
"""

import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
USERNAME = "Shivam-Shukla0"
FOOTER = "open to SDE / Full-Stack / AI Intern roles"
PORTRAIT_FILE = "portrait.txt"


def load_portrait():
    f = Path(__file__).parent / PORTRAIT_FILE
    if f.exists():
        return f.read_text(encoding="utf-8").rstrip("\n").split("\n")
    return ["[ portrait.txt missing — run photo_to_ascii.py ]"]


# (label, value, colour-key)   colour-key: val / accent / warn / muted
# special labels: __header__ / __rule__ / __blank__ / __section__ / __stats__
INFO = [
    ("__header__", "shivam shukla", ""),
    ("__rule__", "", ""),
    ("Role",     "Full Stack Developer · Cybersecurity Enthusiast", "val"),
    ("Edu",      "B.Tech CSE, Sitare Univ · BS DS, IIT Madras '29", "val"),
    ("Focus",    "Full-Stack (MERN) · GenAI Apps · AI/ML", "accent"),
    ("__blank__", "", ""),
    ("__section__", "~/stack", ""),
    ("Lang",     "Python · JavaScript · Java · SQL", "val"),
    ("Backend",  "FastAPI · Node.js · Express · REST APIs", "val"),
    ("AI",       "Claude API · Gemini · RAG · Vector DBs", "val"),
    ("Frontend", "React · React Native · Next.js · Zustand", "val"),
    ("Data",     "MongoDB · MySQL · SQLAlchemy", "val"),
    ("__blank__", "", ""),
    ("__section__", "~/projects", ""),
    ("PadhAI",   "AI learning platform · Class 6-12 · Hinglish", "warn"),
    ("",         "chapter explain · doubt chat · quiz gen", "muted"),
    ("LedgerLeaf", "AI doc organizer for CAs · GST + invoices", "warn"),
    ("SENTINEL", "ML intrusion detection · CICIDS2017", "warn"),
    ("AI-OS",    "personal AI OS · FastAPI + Claude RAG", "warn"),
    ("__blank__", "", ""),
    ("__section__", "~/highlights", ""),
    ("Startup",  "Sitare Startup Program '26-27 · B2B cohort", "val"),
    ("__stats__", "", ""),
    ("__blank__", "", ""),
    ("__section__", "~/reach", ""),
    ("Web",      "shivam-portfolio-next.vercel.app", "accent"),
    ("In",       "linkedin.com/in/shivam-shukla-", "accent"),
    ("Mail",     "lucifer84670@gmail.com", "accent"),
]

THEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "border": "#30363d",
        "text": "#c9d1d9", "muted": "#8b949e", "key": "#3fb950",
        "accent": "#58a6ff", "warn": "#d29922", "art": "#bc8cff",
        "prompt": "#3fb950", "dot1": "#ff5f56", "dot2": "#ffbd2e", "dot3": "#27c93f",
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de",
        "text": "#1f2328", "muted": "#59636e", "key": "#1a7f37",
        "accent": "#0969da", "warn": "#9a6700", "art": "#8250df",
        "prompt": "#1a7f37", "dot1": "#ff5f56", "dot2": "#ffbd2e", "dot3": "#27c93f",
    },
}

W, H = 980, 620
ART_X, ART_Y = 30, 86
ART_MAX_CW = 5.2             # cap on auto-fitted char width
INFO_X, INFO_Y, INFO_LH = 448, 92, 17.5
VAL_X = INFO_X + 92


# ----------------------------------------------------------------------------
# STATS
# ----------------------------------------------------------------------------
def fetch_stats():
    stats = {"repos": "-", "stars": "-", "followers": "-"}
    try:
        headers = {"User-Agent": "profile-readme"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            f"https://api.github.com/users/{USERNAME}", headers=headers)
        user = json.load(urllib.request.urlopen(req, timeout=15))
        stats["repos"] = str(user.get("public_repos", 0))
        stats["followers"] = str(user.get("followers", 0))

        stars, page = 0, 1
        while page <= 5:
            req = urllib.request.Request(
                f"https://api.github.com/users/{USERNAME}/repos"
                f"?per_page=100&page={page}", headers=headers)
            repos = json.load(urllib.request.urlopen(req, timeout=15))
            if not repos:
                break
            stars += sum(r.get("stargazers_count", 0) for r in repos)
            page += 1
        stats["stars"] = str(stars)
    except Exception as e:                      # offline / rate-limited
        print(f"[warn] stats fetch failed: {e}")
    return stats


# ----------------------------------------------------------------------------
# RENDER
# ----------------------------------------------------------------------------
def render(colors, stats, stamp):
    art_lines = load_portrait()
    cols = max((len(l) for l in art_lines), default=1)
    rows = max(len(art_lines), 1)
    max_w = INFO_X - ART_X - 14
    max_h = H - ART_Y - 46
    cw = min(max_w / max(cols, 1), max_h / (rows * 1.72), ART_MAX_CW)
    lh = cw * 1.72
    art_fs = cw * 1.59
    art_y0 = ART_Y + max(0, (max_h - rows * lh) / 2)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, '
        f"'JetBrains Mono', 'Cascadia Code', Menlo, Consolas, monospace\">"
    ]

    parts.append(f"""<style>
    .art  {{ fill:{colors['art']}; font-size:{art_fs:.2f}px; white-space:pre; }}
    .key  {{ fill:{colors['key']}; font-size:13px; font-weight:700; }}
    .val  {{ fill:{colors['text']}; font-size:13px; }}
    .acc  {{ fill:{colors['accent']}; font-size:13px; }}
    .wrn  {{ fill:{colors['warn']}; font-size:13px; }}
    .mut  {{ fill:{colors['muted']}; font-size:12px; }}
    .hdr  {{ fill:{colors['accent']}; font-size:15px; font-weight:700; }}
    .sec  {{ fill:{colors['muted']}; font-size:12px; letter-spacing:1px; }}
    .ttl  {{ fill:{colors['muted']}; font-size:12px; }}
    .row  {{ opacity:1; animation: fade .35s ease backwards; }}
    @keyframes fade {{ from {{ opacity:0; transform:translateY(3px); }}
                       to   {{ opacity:1; transform:translateY(0); }} }}
    .cur  {{ fill:{colors['prompt']}; animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    .artline {{ opacity:1; animation: fade .3s ease backwards; }}
    </style>""")

    # window chrome
    parts.append(
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<path d="M1 13 a12 12 0 0 1 12 -12 h{W-26} a12 12 0 0 1 12 12 v25 h{-(W-2)} z" '
        f'fill="{colors["panel"]}"/>'
    )
    parts.append(f'<line x1="1" y1="38" x2="{W-1}" y2="38" stroke="{colors["border"]}"/>')
    for i, c in enumerate(["dot1", "dot2", "dot3"]):
        parts.append(f'<circle cx="{24 + i*20}" cy="20" r="6" fill="{colors[c]}"/>')
    parts.append(
        f'<text x="{W/2}" y="24" class="ttl" text-anchor="middle">'
        f'{escape(USERNAME)} — zsh — 90×26</text>'
    )

    # command line
    parts.append(
        f'<text x="{ART_X}" y="66" class="row" style="animation-delay:.05s">'
        f'<tspan class="key">➜</tspan>'
        f'<tspan class="acc" dx="8">~</tspan>'
        f'<tspan class="val" dx="8">neofetch --profile</tspan></text>'
    )

    # ascii portrait — auto-fitted to the left panel
    for i, line in enumerate(art_lines):
        if not line.strip():
            continue
        y = art_y0 + i * lh
        tl = len(line) * cw
        parts.append(
            f'<text x="{ART_X}" y="{y:.1f}" class="art artline" xml:space="preserve" '
            f'textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'style="animation-delay:{0.15 + i*0.012:.2f}s">{escape(line)}</text>'
        )

    # info block
    y, delay = INFO_Y, 0.35
    cls_map = {"val": "val", "accent": "acc", "warn": "wrn", "muted": "mut"}

    for label, value, ckey in INFO:
        d = f'style="animation-delay:{delay:.2f}s"'
        if label == "__header__":
            parts.append(f'<text x="{INFO_X}" y="{y:.1f}" class="hdr row" {d}>{escape(value)}</text>')
            y += INFO_LH
        elif label == "__rule__":
            parts.append(
                f'<line x1="{INFO_X}" y1="{y-8:.1f}" x2="{W-40}" y2="{y-8:.1f}" '
                f'stroke="{colors["border"]}" class="row" {d}/>'
            )
            y += 8
        elif label == "__blank__":
            y += 10
            continue
        elif label == "__section__":
            parts.append(f'<text x="{INFO_X}" y="{y:.1f}" class="sec row" {d}>{escape(value)}</text>')
            y += INFO_LH
        elif label == "__stats__":
            stat_txt = (f'repos {stats["repos"]}   ·   stars {stats["stars"]}'
                        f'   ·   followers {stats["followers"]}')
            parts.append(
                f'<text x="{INFO_X}" y="{y:.1f}" class="row" {d}>'
                f'<tspan class="key">⚡</tspan>'
                f'<tspan class="val" dx="8">{escape(stat_txt)}</tspan></text>'
            )
            y += INFO_LH
        else:
            cls = cls_map.get(ckey, "val")
            if label:
                parts.append(
                    f'<text x="{INFO_X}" y="{y:.1f}" class="key row" {d}>{escape(label)}</text>'
                )
            parts.append(
                f'<text x="{VAL_X}" y="{y:.1f}" class="{cls} row" {d}>{escape(value)}</text>'
            )
            y += INFO_LH
        delay += 0.07

    # footer prompt + blinking cursor
    fy = H - 24
    parts.append(
        f'<text x="{ART_X}" y="{fy}" class="row" style="animation-delay:{delay+0.1:.2f}s">'
        f'<tspan class="key">➜</tspan>'
        f'<tspan class="acc" dx="8">~</tspan>'
        f'<tspan class="val" dx="8">{escape(FOOTER)}</tspan>'
        f'<tspan class="cur" dx="8">█</tspan></text>'
    )
    parts.append(
        f'<text x="{W-34}" y="{fy}" class="mut" text-anchor="end">'
        f'last updated {stamp}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    stats = fetch_stats()
    ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    stamp = ist.strftime("%d %b %Y, %H:%M IST")
    out = Path(__file__).parent
    for name, colors in THEMES.items():
        (out / f"{name}.svg").write_text(render(colors, stats, stamp), encoding="utf-8")
        print(f"wrote {name}.svg")


if __name__ == "__main__":
    main()
