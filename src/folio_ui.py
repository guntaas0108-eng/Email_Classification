"""
Folio Archival Editorial UI & Motion System for CampusMail.
Strictly preserves Folio's design tokens, Instrument Serif / DM Sans / IBM Plex Mono
typography, 8-segment radial logo, dimensional orb, and GPU-composited animations
while keeping CampusMail's dual-head ML classification domain and backend intact.
"""

from __future__ import annotations

import html
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ───────────────────────────── FOLIO DESIGN TOKENS ─────────────────────────────
FOLIO_THEMES = {
    "Folio Parchment (Light)": dict(
        bg="#F6F2E9",
        bg2="#0E0F0C",
        rail="#0E0F0C",
        rail2="#1D1E1A",
        rail_line="#2A2B26",
        rail_ink="#F0EEE5",
        rail_muted="#92978C",
        panel="#FFFCF5",
        panel2="#EFE9DD",
        elevated="#FFFFFF",
        line="#DED9CD",
        line_subtle="#EFE9DD",
        ink="#151613",
        ink2="#525349",
        muted="#77776C",
        accent="#BE4A1D",
        accent2="#B85D45",
        accent_soft="#FDF4F2",
        accent_border="#E8A591",
        olive="#5A623F",
        olive_soft="#F4F6F0",
        olive_border="#D7DBC8",
        amber="#C4933F",
        amber_soft="#FAF3E5",
        gold="#C98A2C",
        gold2="#E4A23E",
        gold_soft="#FDF6E4",
        gold_border="#E5C078",
        verdigris="#2F7A6D",
        verdigris_soft="#ECF6F3",
        verdigris_border="#A7D4CA",
        ember="#D94E28",
        ember_glow="rgba(217, 78, 40, 0.28)",
        danger="#A64833",
        danger_soft="#FCE7E2",
        input="#FFFCF5",
        sel="#F4ECE2",
        hover="#EFE9DD",
        h1="#EFE9DD",
        h2="#FDF4F2",
        h3="#F4F6F0",
        h4="#FAF3E5",
        shadow="0 1px 3px rgba(38, 39, 32, 0.05), 0 1px 2px rgba(38, 39, 32, 0.03)",
        shadow_elevated="0 8px 24px -4px rgba(38, 39, 32, 0.08), 0 4px 8px -2px rgba(38, 39, 32, 0.03)",
        grain_opacity="0.025",
        is_dark=False,
    ),
    "Folio Obsidian (Dark)": dict(
        bg="#171916",
        bg2="#0E0F0C",
        rail="#0E0F0C",
        rail2="#1D1E1A",
        rail_line="#2A2B26",
        rail_ink="#F0EEE5",
        rail_muted="#92978C",
        panel="#20231F",
        panel2="#272B26",
        elevated="#2E332D",
        line="#3A4038",
        line_subtle="#30362F",
        ink="#F0EEE5",
        ink2="#C1C2B8",
        muted="#92978C",
        accent="#D46A43",
        accent2="#E1825F",
        accent_soft="#3A2922",
        accent_border="#7B3525",
        olive="#9CA878",
        olive_soft="#252B1E",
        olive_border="#414D36",
        amber="#E99A53",
        amber_soft="#332B1E",
        gold="#E4A23E",
        gold2="#F2CE86",
        gold_soft="#332919",
        gold_border="#7D5D2B",
        verdigris="#5AB8A6",
        verdigris_soft="#1B2E2B",
        verdigris_border="#346158",
        ember="#E85E3B",
        ember_glow="rgba(232, 94, 59, 0.34)",
        danger="#E1825F",
        danger_soft="#3A2922",
        input="#20231F",
        sel="#2E332D",
        hover="#343A33",
        h1="#272B26",
        h2="#3A2922",
        h3="#252B1E",
        h4="#2E2A20",
        shadow="0 2px 6px rgba(0, 0, 0, 0.34), 0 8px 24px -6px rgba(0, 0, 0, 0.45)",
        shadow_elevated="0 12px 32px -6px rgba(0, 0, 0, 0.55)",
        grain_opacity="0.015",
        is_dark=True,
    ),
}

# Earthy Archival Palette from Folio's categoryColors.ts (harmonized across 10 campus categories)
FOLIO_CAT_COLORS = {
    "exams": "#BE4A1D",                  # Terracotta Crimson
    "placements": "#B85D45",             # Warm Terracotta
    "assignments": "#C4933F",            # Ochre / Warm Amber
    "scholarships": "#9B4532",           # Muted Rust / Burnt Sienna
    "hackathons": "#7A5230",             # Deep Umber / Sepia
    "seminars": "#5A623F",               # Botanical Olive
    "events": "#4A6B53",                 # Sage Forest
    "sports": "#8C8542",                 # Antique Brass / Golden Olive
    "hostel_notices": "#6B705C",         # Sage Stone Olive
    "general_announcements": "#77776C",  # Warm Graphite
}

# Exact 8-Segment Radial Geometry from Folio/frontend/src/components/FolioLogo.tsx
FOLIO_LOGO_SEGMENTS = [
    {"index": 0, "dx": 5.36, "dy": -12.93, "d": "M 53.64 34.93 A 15.5 15.5 0 0 1 58.08 36.77 Q 60.32 38.44 62.19 36.35 L 78.5 18.07 Q 81.3 14.94 78.04 12.28 C 74.57 9.37 61.36 3.9 56.84 3.5 Q 52.66 3.08 52.43 7.27 L 51.04 31.73 Q 50.88 34.52 53.64 34.93 Z"},
    {"index": 1, "dx": 12.93, "dy": -5.36, "d": "M 63.68 41.7 A 16 16 0 0 1 65.54 46.2 Q 65.98 49.16 68.97 49.01 L 92.94 47.75 Q 97.43 47.51 96.99 43.04 C 96.77 38.58 91.14 25.01 88.15 21.7 Q 85.3 18.22 81.96 21.23 L 64.12 37.29 Q 61.89 39.29 63.68 41.7 Z"},
    {"index": 2, "dx": 12.93, "dy": 5.36, "d": "M 64.79 53.5 A 15.2 15.2 0 0 1 62.93 57.99 Q 61.38 60.07 63.33 61.79 L 82.06 78.36 Q 85.05 81.01 87.57 77.91 C 90.44 74.35 95.81 61.38 96.3 56.83 Q 96.71 52.86 92.72 52.61 L 67.77 51.09 Q 65.17 50.93 64.79 53.5 Z"},
    {"index": 3, "dx": 5.36, "dy": 12.93, "d": "M 58.33 63.9 A 16.2 16.2 0 0 1 53.94 65.71 Q 50.88 66.18 51.04 69.27 L 52.34 93.14 Q 52.57 97.53 56.95 97.09 C 61.46 96.78 74.97 91.18 78.38 88.21 Q 81.79 85.43 78.85 82.15 L 62.89 64.37 Q 60.82 62.06 58.33 63.9 Z"},
    {"index": 4, "dx": -5.36, "dy": 12.93, "d": "M 46.27 65.15 A 15.6 15.6 0 0 1 41.93 63.35 Q 39.6 61.63 37.67 63.79 L 21.34 82.06 Q 18.54 85.19 21.79 87.84 C 25.31 90.79 38.61 96.3 43.19 96.71 Q 47.37 97.13 47.6 92.93 L 48.97 68.47 Q 49.13 65.58 46.27 65.15 Z"},
    {"index": 5, "dx": -12.93, "dy": 5.36, "d": "M 36.95 57.99 A 15.3 15.3 0 0 1 35.12 53.57 Q 34.73 50.91 32.03 51.07 L 7.28 52.54 Q 3.18 52.78 3.6 56.86 C 4.09 61.37 9.5 74.43 12.34 77.96 Q 14.93 81.14 17.99 78.42 L 36.54 61.95 Q 38.56 60.16 36.95 57.99 Z"},
    {"index": 6, "dx": -12.93, "dy": -5.36, "d": "M 34.36 46.18 A 16.1 16.1 0 0 1 36.24 41.64 Q 38.03 39.24 35.79 37.23 L 17.95 21.19 Q 14.75 18.31 12.02 21.64 C 8.93 25.08 3.34 38.58 3.09 43.2 Q 2.67 47.48 6.96 47.71 L 30.93 48.98 Q 33.92 49.14 34.36 46.18 Z"},
    {"index": 7, "dx": -5.36, "dy": -12.93, "d": "M 42 36.84 A 15.4 15.4 0 0 1 46.35 35.04 Q 49.11 34.63 48.95 31.83 L 47.53 7.17 Q 47.29 2.98 43.11 3.41 C 38.6 3.81 25.39 9.28 21.92 12.18 Q 18.67 14.83 21.46 17.97 L 37.89 36.41 Q 39.76 38.5 42 36.84 Z"},
]

FOLIO_OAUTH_SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Authentication Complete — CampusMail</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&family=Instrument+Serif&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
            background: #F6F2E9;
            color: #151613;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .box {
            position: relative;
            background: #FFFCF5;
            border: 1px solid #DED9CD;
            padding: 40px 34px;
            border-radius: 2px;
            text-align: center;
            max-width: 440px;
            box-shadow: 0 8px 24px -4px rgba(38,39,32,0.08);
        }
        .tick { position: absolute; width: 10px; height: 10px; border-color: #77776C; border-style: solid; }
        .t-tl { top: 8px; left: 8px; border-width: 1.5px 0 0 1.5px; }
        .t-tr { top: 8px; right: 8px; border-width: 1.5px 1.5px 0 0; }
        .t-bl { bottom: 8px; left: 8px; border-width: 0 0 1.5px 1.5px; }
        .t-br { bottom: 8px; right: 8px; border-width: 0 1.5px 1.5px 0; }
        .stamp {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #5A623F;
            border: 1px solid #5A623F;
            padding: 3px 9px;
            display: inline-block;
            margin-bottom: 14px;
        }
        h2 {
            font-family: 'Instrument Serif', Georgia, serif;
            font-size: 32px;
            font-weight: 400;
            color: #151613;
            margin: 0 0 10px;
        }
        p { color: #525349; font-size: 14px; line-height: 1.55; margin: 0 0 24px; }
        .btn {
            display: inline-block;
            background: #151613;
            color: #FFFCF5;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 600;
            padding: 12px 24px;
            border-radius: 2px;
            text-decoration: none;
            transition: background 0.2s ease, transform 0.15s ease;
        }
        .btn:hover { background: #BE4A1D; transform: translateY(-1px); }
    </style>
</head>
<body>
    <div class="box">
        <span class="tick t-tl"></span><span class="tick t-tr"></span>
        <span class="tick t-bl"></span><span class="tick t-br"></span>
        <div class="stamp">Cryptographic Seal Verified</div>
        <h2>Authentication Complete</h2>
        <p>Your institutional Google account has been verified. Returning directly to your CampusMail observatory...</p>
        <a class="btn" href="http://localhost:8501">Return to CampusMail &rarr;</a>
    </div>
    <script>
        setTimeout(function() { window.location.href = "http://localhost:8501"; }, 650);
        setTimeout(function() { window.close(); }, 3000);
    </script>
</body>
</html>"""


def _esc(x) -> str:
    return html.escape(str(x))


def get_motion_prefs() -> dict:
    defaults = {
        "micro_interactions": True,
        "animated_typography": True,
        "highlights": True,
        "loading_animations": True,
        "section_entrances": True,
        "sound_enabled": False,
    }
    if "folio_motion_prefs" not in st.session_state:
        st.session_state.folio_motion_prefs = dict(defaults)
    return st.session_state.folio_motion_prefs


def normalize_theme_name(raw_name: str | None) -> str:
    name = (raw_name or "").strip()
    if name in FOLIO_THEMES:
        return name
    if "Dark" in name or "Obsidian" in name:
        return "Folio Obsidian (Dark)"
    return "Folio Parchment (Light)"


def folio_logo_svg(size: int = 34, state: str = "idle", context: str = "dark") -> str:
    dark_idle = ["#E8D6BF", "#B85D45", "#C4933F", "#D8C4AA", "#A44B34", "#D0B89C", "#C26346", "#B8833C"]
    light_idle = ["#B85D45", "#C8785A", "#C4933F", "#A64833", "#BF6E52", "#D0876C", "#B6793B", "#9C402B"]
    paths = []
    for seg in FOLIO_LOGO_SEGMENTS:
        i = seg["index"]
        if state == "urgent":
            fill = ("#E85E3B" if i in (0, 1) else "#784639") if context == "dark" else ("#C74426" if i in (0, 1) else "#DC9987")
        elif state == "review-needed":
            fill = ("#E59866" if i % 2 == 0 else "#6B5448") if context == "dark" else ("#C46243" if i % 2 == 0 else "#DDB8A8")
        else:
            fill = (dark_idle if context == "dark" else light_idle)[i % 8]
        sdx = seg["dx"] * 0.22
        sdy = seg["dy"] * 0.22
        paths.append(
            f'<path class="folio-logo-slice" d="{seg["d"]}" fill="{fill}" '
            f'style="--sdx:{sdx:.2f}px;--sdy:{sdy:.2f}px;transition:fill 300ms ease,transform 320ms cubic-bezier(0.22,1,0.36,1)" />'
        )

    pulse_ring = ""
    if state == "urgent":
        ring_rgba = "rgba(232, 94, 59, 0.16)" if context == "dark" else "rgba(184, 93, 69, 0.16)"
        ring_bdr = "rgba(232, 94, 59, 0.42)" if context == "dark" else "rgba(190, 74, 29, 0.36)"
        pulse_ring = (
            f'<span class="folio-highlight-pulse" '
            f'style="position:absolute;inset:-4px;border-radius:50%;background:{ring_rgba};border:1px solid {ring_bdr};z-index:0;pointer-events:none"></span>'
        )

    dot = ""
    if state in ("urgent", "review-needed"):
        dot_bg = "#BE4A1D" if state == "urgent" else "#C4933F"
        bdr = "#0E0F0C" if context == "dark" else "#F6F2E9"
        dot = f'<span class="folio-highlight-pulse" style="position:absolute;top:-1px;right:-1px;z-index:4;width:8px;height:8px;border-radius:50%;background:{dot_bg};border:1.5px solid {bdr}"></span>'

    return (
        f'<div class="folio-logo-wrap" style="position:relative;width:{size}px;height:{size}px;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center">'
        f'{pulse_ring}'
        f'<svg viewBox="0 0 100 100" width="{size}" height="{size}" style="position:relative;z-index:2;overflow:visible;display:block;transition:transform 300ms ease" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(paths)}'
        f'</svg>{dot}</div>'
    )


def folio_orb_html(state: str = "idle", review_count: int = 0, label: str = "Neural Core Active") -> str:
    """Renders Folio's Dimensional Orb + IntelligenceLoader polygon mask organism cleanly inside CSS."""
    uid = uuid.uuid4().hex[:8]
    mask_id = f"folio-clip-{uid}"
    state_cls = "state-review-needed" if state in ("urgent", "review-needed") else ""
    badge_html = ""
    if review_count > 0:
        badge_html = (
            f'<div class="folio-highlight-pulse" style="position:absolute;top:-4px;right:-10px;z-index:20;'
            f'display:inline-flex;align-items:center;gap:4px;background:var(--accent);color:#FFFCF5;'
            f'border:1px solid var(--bg);padding:2px 7px;font-family:\'IBM Plex Mono\',monospace;font-size:10px;font-weight:600;'
            f'letter-spacing:0.06em;text-transform:uppercase;box-shadow:0 4px 12px rgba(190,74,29,0.3)">'
            f'<span>!</span><span>{review_count} Threat{"s" if review_count != 1 else ""}</span></div>'
        )
    return (
        f'<div class="folio-orb-container folio-orb-tilt {state_cls}" '
        f'style="position:relative;display:inline-flex;flex-direction:column;align-items:center;justify-content:center;user-select:none;padding:6px 10px" '
        f'title="{_esc(label)}">'
        f'{badge_html}'
        f'<div class="folio-orb-sphere folio-loader-organism {state_cls}">'
        f'  <svg width="96" height="96" viewBox="0 0 100 100" style="position:absolute;inset:0">'
        f'    <defs>'
        f'      <mask id="{mask_id}">'
        f'        <polygon points="0,0 100,0 100,100 0,100" fill="black" />'
        f'        <polygon class="poly-1" points="25,25 75,25 50,75" fill="white" />'
        f'        <polygon class="poly-2" points="50,25 75,75 25,75" fill="white" />'
        f'        <polygon class="poly-3" points="35,35 65,35 50,65" fill="white" />'
        f'        <polygon class="poly-4" points="35,35 65,35 50,65" fill="white" />'
        f'        <polygon class="poly-5" points="35,35 65,35 50,65" fill="white" />'
        f'        <polygon class="poly-6" points="35,35 65,35 50,65" fill="white" />'
        f'      </mask>'
        f'    </defs>'
        f'  </svg>'
        f'  <div class="folio-loader-box" style="mask:url(#{mask_id});-webkit-mask:url(#{mask_id});"></div>'
        f'</div>'
        f'<div style="margin-top:8px;font-family:\'IBM Plex Mono\',monospace;font-size:9px;text-transform:uppercase;letter-spacing:0.16em;color:var(--muted);background:var(--panel);border:1px solid var(--line);padding:2px 8px">'
        f'{_esc(label)}</div>'
        f'</div>'
    )


def inject_folio_css(t: dict, motion: dict | None = None):
    m = motion or get_motion_prefs()
    m_micro = "true" if m.get("micro_interactions", True) else "false"
    m_typo = "true" if m.get("animated_typography", True) else "false"
    m_high = "true" if m.get("highlights", True) else "false"
    m_load = "true" if m.get("loading_animations", True) else "false"
    m_sec = "true" if m.get("section_entrances", True) else "false"

    grain_op = t.get("grain_opacity", "0.025")
    paper_grain = (
        f'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E'
        f'%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.8\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E'
        f'%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'{grain_op}\'/%3E%3C/svg%3E")'
    )

    scheme = "dark" if t.get("is_dark") else "light"
    vars_css = (
        ":root{"
        + ";".join(f"--{k}:{v}" for k, v in t.items() if isinstance(v, str))
        + f";--paper-grain:{paper_grain};"
        + f"--text-color:{t['ink']};--background-color:{t['bg']};--secondary-background-color:{t['panel2']};--primary-color:{t['accent']};"
        + f"color-scheme:{scheme};"
        + "}"
    )

    # Dynamic keyframe gating based on user's Motion toggles
    micro_css = ""
    if m_micro == "true":
        micro_css = """
.folio-btn-tactile, div.stButton button, div.stDownloadButton button, div.stFormSubmitButton button {
    transition: transform 160ms cubic-bezier(0.22, 1, 0.36, 1), background-color 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease !important;
}
/* Brass Foil Shimmer Sweep on Primary CTAs */
div.stButton button[kind="primary"],
div.stButton button[data-testid="stBaseButton-primary"],
div.stFormSubmitButton button {
    position: relative !important;
    overflow: hidden !important;
}
div.stButton button[kind="primary"]::after,
div.stButton button[data-testid="stBaseButton-primary"]::after,
div.stFormSubmitButton button::after {
    content: '';
    position: absolute;
    top: -10%;
    left: -120%;
    width: 65%;
    height: 120%;
    background: linear-gradient(115deg, transparent 22%, rgba(242, 206, 134, 0.36) 50%, transparent 78%);
    pointer-events: none;
    transform: skewX(-18deg);
    transition: left 620ms cubic-bezier(0.22, 1, 0.36, 1);
}
@media (hover: hover) {
    div.stButton button[kind="primary"]:hover::after,
    div.stButton button[data-testid="stBaseButton-primary"]:hover::after,
    div.stFormSubmitButton button:hover::after {
        left: 145%;
    }
    .folio-btn-tactile:hover:not(:disabled), div.stButton button:hover:not(:disabled), div.stDownloadButton button:hover:not(:disabled) {
        transform: translateY(-1px) !important;
    }
    .folio-card-interactive:hover, .folio-plate-card:hover {
        transform: translateY(-2px) !important;
        border-color: var(--gold_border) !important;
        box-shadow: var(--shadow_elevated) !important;
    }
    .folio-logo-wrap:hover svg {
        transform: rotate(9deg) scale(1.03);
    }
    .folio-logo-wrap:hover .folio-logo-slice {
        transform: translate(var(--sdx, 0px), var(--sdy, 0px));
    }
}
/* Cursor-Tracking Gold-Leaf Spotlight on Archival Plates & KPIs */
.folio-spotlight, .kpi-modern, .dept-pill-card, .reader, .folio-plate {
    position: relative;
    overflow: hidden;
}
.folio-spotlight::after, .kpi-modern::after, .dept-pill-card::after, .reader::after, .folio-plate::after {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0;
    background: radial-gradient(260px circle at var(--mx, 50%) var(--my, 50%), rgba(228, 162, 62, 0.14), transparent 72%);
    transition: opacity 240ms ease;
    z-index: 1;
}
.folio-spotlight:hover::after, .kpi-modern:hover::after, .dept-pill-card:hover::after, .reader:hover::after, .folio-plate:hover::after {
    opacity: 1;
}
.folio-btn-tactile:active:not(:disabled), div.stButton button:active:not(:disabled) {
    transform: translateY(0.5px) scale(0.985) !important;
    transition-duration: 90ms !important;
}
.folio-nav-btn:hover { transform: translateX(2px) !important; }
"""

    typo_css = ""
    if m_typo == "true":
        typo_css = """
.folio-typo-kicker { animation: folio-typo-reveal 260ms cubic-bezier(0.22, 1, 0.36, 1) both; }
.folio-typo-heading { animation: folio-typo-reveal 320ms cubic-bezier(0.22, 1, 0.36, 1) 45ms both; }
.folio-typo-subtitle { animation: folio-typo-reveal 300ms cubic-bezier(0.22, 1, 0.36, 1) 90ms both; }
.folio-hero-rule, .rule-double { transform-origin: left center; animation: folio-hero-rule-x 620ms cubic-bezier(0.22, 1, 0.36, 1) 40ms both; }
.folio-divider-draw { transform-origin: left center; animation: folio-divider-reveal 440ms cubic-bezier(0.16, 1, 0.3, 1) both; }
"""

    sec_css = ""
    if m_sec == "true":
        sec_css = """
.folio-card-entrance { animation: folio-card-reveal 340ms cubic-bezier(0.16, 1, 0.3, 1) var(--enter-delay, 0ms) both; }
.folio-workbench-panel { animation: folio-panel-fade 280ms cubic-bezier(0.22, 1, 0.36, 1) both; }
.folio-reader-enter { animation: folio-slide-in-right 280ms cubic-bezier(0.22, 1, 0.36, 1) both; }
.dept-progress-fill { transform-origin: left center; animation: folio-bar-fill 720ms cubic-bezier(0.22, 1, 0.36, 1) var(--enter-delay, 60ms) both; }
.folio-chip-pop { animation: folio-chip-reveal 280ms cubic-bezier(0.22, 1, 0.36, 1) calc(var(--chip-i, 0) * 50ms) both; }
"""

    high_css = ""
    if m_high == "true":
        high_css = """
.folio-highlight-pulse { animation: folio-highlight-pulse-anim 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.folio-orb-aura-threat .folio-orb-sphere.state-review-needed {
    animation: folio-ember-pulse 2.4s ease-in-out infinite;
}
.folio-edge-light-wrap { position: relative; overflow: hidden; }
.folio-edge-light-ring {
    position: absolute; inset: 0; padding: 2px; box-sizing: border-box;
    border-radius: inherit; pointer-events: none; overflow: hidden; z-index: 20;
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
}
.folio-edge-light-ring::before {
    content: ''; position: absolute; left: 50%; top: 50%; width: max(220%, 260px); aspect-ratio: 1 / 1;
    background: conic-gradient(from 0deg, transparent 0deg, transparent 226deg, rgba(190, 74, 29, 0.50) 266deg, rgba(228, 162, 62, 0.96) 312deg, rgba(242, 206, 134, 1) 340deg, rgba(185, 87, 42, 0.68) 354deg, transparent 360deg);
    animation: folio-edge-light-sweep 3.4s cubic-bezier(0.35, 0.05, 0.25, 1) forwards;
}
.folio-edge-light-ring.threat-ember::before {
    background: conic-gradient(from 0deg, transparent 0deg, transparent 225deg, rgba(166, 72, 51, 0.55) 265deg, rgba(232, 94, 59, 0.98) 315deg, rgba(242, 206, 134, 0.95) 342deg, rgba(217, 78, 40, 0.65) 354deg, transparent 360deg);
}
.folio-edge-light-glow {
    position: absolute; inset: 0; border-radius: inherit; pointer-events: none; z-index: 19;
    border: 1.5px solid rgba(228, 162, 62, 0.45);
    background: rgba(242, 206, 134, 0.07);
    box-shadow: inset 0 0 10px rgba(228, 162, 62, 0.26);
    animation: folio-edge-light-ambient 3.4s ease-out forwards;
}
.folio-edge-light-glow.threat-ember {
    border-color: rgba(232, 94, 59, 0.52);
    background: rgba(232, 94, 59, 0.08);
    box-shadow: inset 0 0 12px rgba(232, 94, 59, 0.26);
}
"""

    load_css = ""
    if m_load == "true":
        load_css = """
.folio-loader-ping { animation: folio-ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; }
.folio-loader-pulse { animation: folio-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.folio-orb-sphere { animation: orb-drift 18s ease-in-out infinite alternate; }
.folio-orb-sphere::before { animation: orb-halo 10s ease-in-out infinite alternate; }
.folio-loader-organism { animation: colorize 6s ease-in-out infinite; }
.folio-loader-organism mask { filter: contrast(15); animation: roundness 1s linear infinite; }
.folio-loader-organism .poly-2 { animation: orb-rotation 2s linear infinite reverse; }
.folio-loader-organism .poly-3 { animation: orb-rotation 2s linear infinite -0.66s; }
.folio-loader-organism .poly-4 { animation: orb-rotation 2s linear infinite reverse; }
.folio-loader-organism .poly-5 { animation: orb-rotation 2s linear infinite reverse -1s; }
.folio-loader-organism .poly-6 { animation: orb-rotation 2s linear infinite -1.33s; }
"""

    css = f"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Instrument+Serif:ital@0;1&display=swap');

/* ══════════ BASE FOLIO CANVAS & PAPER GRAIN TEXTURE ══════════ */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif !important;
    background-color: var(--bg) !important;
    background-image: var(--paper-grain) !important;
    color: var(--ink) !important;
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    transition: background-color 220ms ease, color 220ms ease;
}}

/* Preserve Material Symbols icons inside Streamlit internal buttons/expanders */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"], [class*="StyledIcon"] {{
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    font-style: normal !important;
    letter-spacing: normal !important;
}}

/* Subtle unobtrusive top Streamlit bar */
[data-testid="stHeader"] {{
    background: transparent !important;
    height: 2.5rem !important;
}}
[data-testid="stToolbar"] {{
    opacity: 0.45;
    transition: opacity 180ms ease;
}}
[data-testid="stToolbar"]:hover {{
    opacity: 1.0;
}}
[data-testid="stDecoration"] {{
    display: none !important;
}}

.stApp [data-testid="stMain"] .block-container,
.main .block-container {{
    max-width: 1320px !important;
    margin: 0 auto !important;
    padding-top: 2.35rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2.4rem !important;
    padding-right: 2.4rem !important;
}}

/* Typography Hierarchy */
.stMarkdown, .stMarkdown p, label, [data-testid="stWidgetLabel"] *, h1, h2, h3, h4 {{
    color: var(--ink);
}}
h1, h2, h3, .folio-serif {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-weight: 400 !important;
    letter-spacing: -0.02em !important;
}}
.folio-mono, code {{
    font-family: 'IBM Plex Mono', Menlo, monospace !important;
}}
[data-testid="stCaptionContainer"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--muted) !important;
    font-size: 0.76rem !important;
}}

/* Archival Utilities */
.archival-stamp {{
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    font-size: 0.68rem;
    font-weight: 600;
    border: 1px solid currentColor;
    padding: 2px 8px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border-radius: 1px;
    white-space: nowrap;
}}
.rule-double {{
    border-bottom: 3px double var(--line);
}}
.rule-double-t {{
    border-top: 3px double var(--line);
}}
.folio-urgency-hatched {{
    background-color: var(--accent_soft);
    background-image: repeating-linear-gradient(
        -45deg,
        rgba(190, 74, 29, 0.14),
        rgba(190, 74, 29, 0.14) 4px,
        transparent 4px,
        transparent 8px
    );
}}

/* Corner Registration Ticks Container */
.folio-plate {{
    position: relative;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    box-shadow: var(--shadow);
}}
.folio-tick {{
    position: absolute;
    width: 9px;
    height: 9px;
    border-color: var(--muted);
    border-style: solid;
    pointer-events: none;
    opacity: 0.65;
}}
.folio-tick.tl {{ top: 7px; left: 7px; border-width: 1.5px 0 0 1.5px; }}
.folio-tick.tr {{ top: 7px; right: 7px; border-width: 1.5px 1.5px 0 0; }}
.folio-tick.bl {{ bottom: 7px; left: 7px; border-width: 0 0 1.5px 1.5px; }}
.folio-tick.br {{ bottom: 7px; right: 7px; border-width: 0 1.5px 1.5px 0; }}

/* ══════════ OBSERVATORY COORDINATE STRIP & EDITORIAL MASTHEAD ══════════ */
.folio-coord-strip {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 6px 0 8px;
    border-bottom: 1px solid var(--line);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.69rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 14px;
}}
.folio-coord-left, .folio-coord-right {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}}
.folio-ping-wrap {{
    position: relative;
    display: inline-flex;
    width: 8px;
    height: 8px;
}}
.folio-ping-halo {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: var(--verdigris);
    opacity: 0.75;
}}
.folio-ping-core {{
    position: relative;
    display: inline-flex;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--verdigris);
}}
.folio-masthead {{
    padding-bottom: 16px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--line);
}}
.folio-page-title {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-size: clamp(2.1rem, 3.6vw, 3.05rem);
    font-weight: 400;
    color: var(--ink);
    line-height: 1.03;
    letter-spacing: -0.02em;
    margin: 4px 0 6px;
}}
.folio-page-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    color: var(--ink2);
    line-height: 1.5;
    border-left: 2px solid var(--accent);
    padding-left: 12px;
    max-width: 68ch;
}}

/* ══════════ NEAR-BLACK FOLIO SIDEBAR RAIL (#0E0F0C) ══════════ */
[data-testid="stSidebar"], section[data-testid="stSidebar"] {{
    background: var(--rail) !important;
    border-right: 1px solid var(--rail_line) !important;
    box-shadow: 4px 0 28px rgba(0, 0, 0, 0.25) !important;
}}
[data-testid="stSidebar"] * {{
    color: var(--rail_ink);
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    gap: 0.25rem !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
    margin-bottom: 1px !important;
}}

/* Sidebar Collapse / Reopen Buttons */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 999999 !important;
    background: var(--rail) !important;
    color: #F0EEE5 !important;
    border: 1px solid var(--accent) !important;
    border-radius: 2px !important;
    padding: 6px 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28) !important;
}}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {{
    background: var(--accent) !important;
    color: #FFFCF5 !important;
}}
[data-testid="stSidebarCollapseButton"] button, button[data-testid="stSidebarCollapseButton"] {{
    background: var(--rail2) !important;
    border: 1px solid var(--rail_line) !important;
    border-radius: 2px !important;
    color: var(--rail_ink) !important;
}}
[data-testid="stSidebarCollapseButton"] button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent2) !important;
}}

.side-title {{
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--rail_muted) !important;
    font-size: 0.67rem !important;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin: 14px 4px 6px;
    font-weight: 600;
}}

/* Sidebar Tree / Navigation Buttons (supports help-wrapped stTooltipHoverTarget too) */
[data-testid="stSidebar"] div.stButton button,
[data-testid="stSidebar"] div.stButton button[data-testid="stBaseButton-secondary"] {{
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    padding: 7px 12px !important;
    min-height: 2.3rem !important;
    border-radius: 2px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    color: #B4B6AC !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    margin: 1px 0 !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] div.stButton button > div,
[data-testid="stSidebar"] div.stButton button span,
[data-testid="stSidebar"] div.stButton button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] div.stButton button [data-testid="stMarkdownContainer"] p {{
    display: flex !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    gap: 8px !important;
    color: inherit !important;
}}
[data-testid="stSidebar"] div.stButton button[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stSidebar"] div.stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {{
    background: var(--rail2) !important;
    background-color: var(--rail2) !important;
    border-color: var(--rail_line) !important;
    color: #F0EEE5 !important;
    transform: translateX(2px) !important;
}}
[data-testid="stSidebar"] div.stButton button[kind="primary"],
[data-testid="stSidebar"] div.stButton button[data-testid="stBaseButton-primary"] {{
    background: var(--rail2) !important;
    background-color: var(--rail2) !important;
    border: 1px solid var(--rail_line) !important;
    border-left: 3px solid #D46A43 !important;
    color: #FFFCF5 !important;
    font-weight: 600 !important;
    box-shadow: inset 0 0 18px rgba(190, 74, 29, 0.14) !important;
}}

/* Sidebar 2-Column Compact Controls (Theme Toggle, Demo/SignIn, SignOut/Sync) */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {{
    gap: 8px !important;
    margin: 4px 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button,
[data-testid="stSidebar"] [data-testid="stColumn"] div.stButton button {{
    justify-content: center !important;
    text-align: center !important;
    padding: 6px 10px !important;
    min-height: 2.15rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.74rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    border-radius: 2px !important;
    transform: none !important;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button p,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button span {{
    justify-content: center !important;
    text-align: center !important;
    margin: 0 auto !important;
    color: inherit !important;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {{
    background: #1D1E1A !important;
    background-color: #1D1E1A !important;
    border: 1px solid #32342D !important;
    color: #E2E1D8 !important;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {{
    background: #272923 !important;
    background-color: #272923 !important;
    border-color: #D46A43 !important;
    color: #FFFCF5 !important;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div.stButton button[data-testid="stBaseButton-primary"] {{
    background: #BE4A1D !important;
    background-color: #BE4A1D !important;
    border: 1px solid #D46A43 !important;
    border-left: 1px solid #D46A43 !important;
    color: #FFFCF5 !important;
}}

/* ══════════ REAL WRAPPED ARCHIVAL CONTAINERS (st.container(key=...)) ══════════ */
[class*="st-key-folio_card"],
[class*="st-key-folio_plate"],
[class*="st-key-folio_login_box"],
[class*="st-key-card_"] {{
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    padding: 18px 20px !important;
    box-shadow: var(--shadow) !important;
    margin-bottom: 14px !important;
    transition: border-color 180ms ease, box-shadow 200ms ease, transform 200ms cubic-bezier(0.22, 1, 0.36, 1) !important;
}}
[class*="st-key-folio_login_box"] {{
    padding: 28px 30px !important;
    box-shadow: var(--shadow_elevated) !important;
}}
@media (hover: hover) {{
    [class*="st-key-folio_card"]:hover,
    [class*="st-key-card_"]:hover {{
        border-color: rgba(184, 93, 69, 0.52) !important;
    }}
}}

/* Standard HTML Cards */
.card {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    box-shadow: var(--shadow);
    overflow: hidden;
    margin-bottom: 14px;
}}
.card-head {{
    padding: 12px 18px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    background: var(--panel2);
    color: var(--ink);
}}
.card-head-left {{
    display: inline-flex;
    align-items: center;
    gap: 9px;
}}
.card-body {{ padding: 18px 20px; }}
.h1 {{ background: var(--h1); }} .h2 {{ background: var(--h2); }} .h3 {{ background: var(--h3); }} .h4 {{ background: var(--h4); }}

/* KPI Archival Tiles */
/* Equal-Height KPI Grid Alignment */
[data-testid="stHorizontalBlock"]:has(.kpi-modern) {{
    align-items: stretch !important;
}}
[data-testid="stHorizontalBlock"]:has(.kpi-modern) > [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.kpi-modern) [data-testid="stMarkdown"] {{
    height: 100% !important;
}}
.kpi-modern {{
    position: relative;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 16px 18px;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 152px;
    height: 100%;
    box-sizing: border-box;
}}
.kpi-modern-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 10px;
}}
.kpi-modern-icon {{
    width: 30px;
    height: 30px;
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--line);
    background: var(--panel2);
    color: var(--accent);
}}
.kpi-modern-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
}}
.kpi-modern-val {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-size: 2.15rem;
    font-weight: 400;
    line-height: 1.05;
    color: var(--ink);
    font-variant-numeric: tabular-nums;
    margin-bottom: 6px;
}}
.kpi-modern-foot {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.70rem;
    color: var(--muted);
    line-height: 1.35;
    border-top: 1px solid var(--line_subtle);
    padding-top: 6px;
}}

/* Department Matrix Cards */
.dept-pill-card {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 13px 14px;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 108px;
    height: 100%;
    box-sizing: border-box;
}}
.dept-title {{
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.80rem;
    color: var(--ink);
    line-height: 1.25;
}}
.dept-val {{
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.75rem;
    font-weight: 400;
    color: var(--ink);
    line-height: 1.1;
    margin: 4px 0;
    font-variant-numeric: tabular-nums;
}}
.dept-progress-bg {{
    width: 100%;
    height: 4px;
    background: var(--panel2);
    border-radius: 1px;
    overflow: hidden;
    margin-top: 6px;
}}
.dept-progress-fill {{
    height: 100%;
    border-radius: 1px;
    transition: width 420ms cubic-bezier(0.22, 1, 0.36, 1);
}}

/* Impending Deadlines / Action Rows */
.deadline-item {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: 2px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
}}
.deadline-item:hover {{
    background: var(--panel2);
}}

/* Tags, Pills & Badges */
.tag {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 9px;
    border-radius: 2px;
    border: 1px solid;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.70rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
}}
.hud-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 1px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
}}
.muted {{ color: var(--ink2); font-size: 0.88rem; line-height: 1.55; }}

/* ══════════ MAIN CONTENT BUTTONS, INPUTS, RADIOS, TABS & TABLES ══════════ */
div.stButton button,
div.stButton button[data-testid="stBaseButton-secondary"],
div.stDownloadButton button,
div.stDownloadButton button[data-testid="stBaseButton-secondary"] {{
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    min-height: 2.35rem !important;
    border: 1px solid var(--line) !important;
    background: var(--panel) !important;
    background-color: var(--panel) !important;
    color: var(--ink) !important;
    box-shadow: var(--shadow) !important;
}}
div.stButton button p,
div.stButton button span,
div.stDownloadButton button p,
div.stDownloadButton button span {{
    color: inherit !important;
}}
div.stButton button:hover,
div.stButton button[data-testid="stBaseButton-secondary"]:hover,
div.stDownloadButton button:hover {{
    background: var(--panel2) !important;
    background-color: var(--panel2) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}}
div.stButton button[kind="primary"],
div.stButton button[data-testid="stBaseButton-primary"],
div.stFormSubmitButton button[kind="primary"],
div.stFormSubmitButton button[data-testid="stBaseButton-primaryFormSubmit"],
div.stFormSubmitButton button {{
    background: var(--accent) !important;
    background-color: var(--accent) !important;
    color: #FFFCF5 !important;
    border: 1px solid var(--accent) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    font-weight: 600 !important;
    border-radius: 2px !important;
}}
div.stButton button[kind="primary"]:hover,
div.stButton button[data-testid="stBaseButton-primary"]:hover,
div.stFormSubmitButton button:hover {{
    background: var(--accent2) !important;
    background-color: var(--accent2) !important;
    border-color: var(--accent2) !important;
    color: #FFFCF5 !important;
}}

/* Tight Specimen Row Fitting at 1280px */
[class*="st-key-folio_specimens"] div.stButton button {{
    padding: 6px 6px !important;
    font-size: 0.71rem !important;
    letter-spacing: 0.02em !important;
}}

/* Inputs, Textarea, Selectbox, DatePicker, Code Chips (Light + Obsidian Dark consistent) */
html body .stApp [data-testid="stTextInputRootElement"],
html body .stApp [data-testid="stTextInputRootElement"] > div,
html body .stApp [data-testid="stTextArea"] [data-baseweb="textarea"],
html body .stApp [data-testid="stTextArea"] [data-baseweb="textarea"] > div,
html body .stApp [data-testid="stTextArea"] [data-baseweb="base-input"],
html body .stApp [data-testid="stTextArea"] [data-baseweb="base-input"] > div,
html body .stApp [data-testid="stDateInput"] > div > div,
html body .stApp [data-testid="stDateInput"] [data-baseweb="input"],
html body .stApp [data-testid="stDateInput"] [data-baseweb="input"] div,
html body .stApp [data-testid="stDateInput"] [data-baseweb="base-input"],
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] div,
html body .stApp [data-testid="stSelectbox"] .react-aria-ComboBox > div[role="group"],
html body .stApp [data-testid="stSelectbox"] div[role="group"],
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="base-input"] > div,
[data-baseweb="textarea"],
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div,
[data-baseweb="select"] div {{
    background: var(--input) !important;
    background-color: var(--input) !important;
    color: var(--ink) !important;
    border-color: var(--line) !important;
    border-radius: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within,
html body .stApp [data-testid="stSelectbox"] div[role="group"]:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}}
html body .stApp [data-testid="stTextInput"] input,
html body .stApp [data-testid="stDateInput"] input,
html body .stApp [data-testid="stDateInput"] *,
html body .stApp [data-testid="stTextArea"] textarea,
[data-baseweb="input"] input,
[data-baseweb="base-input"] input,
[data-baseweb="textarea"] textarea,
input, textarea {{
    color: var(--ink) !important;
    background: var(--input) !important;
    background-color: var(--input) !important;
    caret-color: var(--accent) !important;
    -webkit-text-fill-color: var(--ink) !important;
    opacity: 1 !important;
}}
html body .stApp [data-testid="stSelectbox"] .react-aria-ComboBox,
html body .stApp [data-testid="stSelectbox"] div[role="group"] > input,
html body .stApp [data-testid="stSelectbox"] div[role="group"] > button,
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"],
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"]:hover,
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"]:focus,
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"]:active,
html body .stApp [data-testid="stSelectbox"] [data-rac] button {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--ink) !important;
}}
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"] svg,
html body .stApp [data-testid="stSelectbox"] svg {{
    color: var(--ink2) !important;
    fill: var(--ink2) !important;
    opacity: 1 !important;
}}
html body .stApp [data-testid="stSelectbox"] button[aria-label="Open"]:hover svg {{
    color: var(--accent) !important;
    fill: var(--accent) !important;
}}
html body .stApp [data-testid="stSelectbox"] svg path:not([fill="none"]) {{
    fill: currentColor !important;
}}
html body .stApp [data-testid="stSelectbox"] svg path[fill="none"],
html body .stApp [data-testid="stSelectbox"] svg rect {{
    fill: none !important;
}}
input::placeholder, textarea::placeholder {{
    color: var(--muted) !important;
    opacity: 0.85 !important;
    -webkit-text-fill-color: var(--muted) !important;
}}
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] *,
html body .stApp [data-testid="stSelectbox"] .react-aria-ComboBox input,
[data-baseweb="select"] span,
div[data-baseweb="calendar"] * {{
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}}
[data-baseweb="input"] svg, [data-baseweb="select"] svg, [data-testid="stDateInput"] svg {{
    fill: var(--muted) !important;
    color: var(--muted) !important;
}}
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"],
div[role="listbox"],
div.react-aria-Popover,
div.react-aria-ListBox,
div[data-baseweb="calendar"] {{
    background-color: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    box-shadow: var(--shadow_elevated) !important;
}}
li[role="option"],
[role="option"] {{
    background-color: var(--panel) !important;
    color: var(--ink) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}}
li[role="option"]:hover,
li[role="option"][aria-selected="true"],
[role="option"]:hover,
[role="option"][aria-selected="true"],
[role="option"][data-hovered="true"],
[role="option"][data-focused="true"],
[role="option"][data-selected="true"] {{
    background-color: var(--sel) !important;
    color: var(--accent) !important;
}}
code {{
    background: var(--panel2) !important;
    color: var(--accent) !important;
    border: 1px solid var(--line) !important;
    padding: 1px 6px !important;
    border-radius: 2px !important;
}}
details.vega-actions summary {{
    background: var(--panel2) !important;
    border: 1px solid var(--line) !important;
    color: var(--muted) !important;
    border-radius: 2px !important;
}}
.vega-actions {{
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
}}
.vega-actions a {{
    color: var(--ink) !important;
}}

/* Segmented Radios */
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    gap: 6px !important;
}}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label {{
    padding: 6px 14px !important;
    border-radius: 2px !important;
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    cursor: pointer !important;
    transition: all 150ms ease !important;
}}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label > div:first-child:not([data-testid="stMarkdownContainer"]),
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label input[type="radio"] {{
    display: none !important;
}}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label p {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--ink2) !important;
    margin: 0 !important;
}}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label:has(input:checked) {{
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}}
div[data-testid="stRadio"]:not([data-testid="stSidebar"] div[data-testid="stRadio"]) [role="radiogroup"] label:has(input:checked) p {{
    color: #FFFCF5 !important;
    font-weight: 600 !important;
}}

/* Archival Editorial Tabs (ultra-high specificity against dynamic Emotion rules) */
html body .stApp [role="tablist"],
[data-testid="stTabs"] [data-baseweb="tab-list"],
.stTabs [data-baseweb="tab-list"] {{
    border-bottom: 1px solid var(--line) !important;
    gap: 18px !important;
    background: transparent !important;
}}
html body .stApp [role="tablist"] button[role="tab"],
html body .stApp [role="tablist"] button[role="tab"] *,
[data-testid="stTabs"] button[data-baseweb="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"] *,
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] * {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--ink2) !important;
    -webkit-text-fill-color: var(--ink2) !important;
    opacity: 1 !important;
    background: transparent !important;
    border-radius: 0 !important;
}}
html body .stApp [role="tablist"] button[role="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"],
.stTabs [data-baseweb="tab"] {{
    padding: 10px 4px !important;
    border-bottom: 2px solid transparent !important;
}}
html body .stApp [role="tablist"] button[role="tab"]:hover,
html body .stApp [role="tablist"] button[role="tab"]:hover *,
[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
[data-testid="stTabs"] button[data-baseweb="tab"]:hover * {{
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}}
html body .stApp [role="tablist"] button[role="tab"][aria-selected="true"],
html body .stApp [role="tablist"] button[role="tab"][aria-selected="true"] *,
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] * {{
    color: var(--accent) !important;
    -webkit-text-fill-color: var(--accent) !important;
    font-weight: 600 !important;
}}
html body .stApp [role="tablist"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: var(--accent) !important;
    height: 2px !important;
}}

/* Folio HTML Ledger Tables */
.folio-table-wrap {{
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--line);
    border-radius: 2px;
    background: var(--panel);
}}
table.folio-table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.80rem;
    color: var(--ink);
}}
table.folio-table thead th {{
    background: var(--panel2);
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 8px 7px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    white-space: normal;
    line-height: 1.25;
}}
table.folio-table tbody td {{
    padding: 7px 7px;
    border-bottom: 1px solid var(--line_subtle);
    color: var(--ink);
    font-variant-numeric: tabular-nums;
}}
table.folio-table.folio-table-compact thead th {{
    font-size: 0.61rem;
    padding: 7px 5px;
    letter-spacing: 0.04em;
}}
table.folio-table.folio-table-compact tbody td {{
    font-size: 0.74rem;
    padding: 6px 5px;
}}
table.folio-table tbody tr:last-child td {{
    border-bottom: none;
}}
table.folio-table tbody tr:hover td {{
    background: var(--panel2);
}}
table.folio-table tbody tr.folio-row-champion td {{
    background: linear-gradient(90deg, var(--gold_soft), var(--accent_soft));
    font-weight: 600;
    border-bottom-color: var(--gold_border);
}}
table.folio-table tbody tr.folio-row-champion td:first-child {{
    border-left: 3px solid var(--gold2);
}}
.folio-spark-chip {{
    border-color: var(--gold_border) !important;
    background: var(--gold_soft) !important;
    color: var(--gold) !important;
    box-shadow: 0 2px 8px rgba(228, 162, 62, 0.16);
}}
table.folio-table th.num, table.folio-table td.num {{
    text-align: right;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
}}

/* Slider in Sync panel */
div[data-baseweb="slider"] div[role="slider"] {{
    background-color: var(--accent) !important;
    border: 2px solid var(--panel) !important;
}}
div[data-baseweb="slider"] div[data-testid="stThumbValue"] {{
    color: var(--accent) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}}

/* Expanders & DataFrames */
[data-testid="stExpander"] {{
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    background: var(--panel) !important;
    box-shadow: var(--shadow) !important;
    margin-bottom: 14px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.80rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    padding: 10px 16px !important;
}}
[data-testid="stDataFrame"] {{
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    overflow: hidden;
    background: var(--panel) !important;
    {"filter: invert(0.89) hue-rotate(180deg) contrast(0.95);" if t.get("is_dark") else ""}
}}

/* Mail List & Editorial Reader */
[class*="st-key-mail"] button {{
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 2px !important;
    padding: 12px 14px !important;
    height: auto !important;
    margin-bottom: 5px !important;
    box-shadow: var(--shadow) !important;
}}
[class*="st-key-mail"] button > div,
[class*="st-key-mail"] button [data-testid="stMarkdownContainer"] {{
    width: 100% !important;
    text-align: left !important;
}}
[class*="st-key-mail"] button p {{
    text-align: left !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    color: var(--muted) !important;
    line-height: 1.42 !important;
    margin: 0 !important;
}}
[class*="st-key-mail"] button p strong {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    color: var(--ink) !important;
    font-size: 1.04rem !important;
    font-weight: 400 !important;
}}
[class*="st-key-mail"] button:hover {{
    border-color: var(--accent) !important;
    background: var(--panel2) !important;
    transform: translateX(2px) !important;
}}
[class*="st-key-mailsel"] button {{
    background: var(--sel) !important;
    border-color: var(--accent) !important;
    border-left: 3px solid var(--accent) !important;
}}

.reader {{
    position: relative;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 26px 28px;
    box-shadow: var(--shadow);
}}
.reader h2 {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    margin: 0 0 14px;
    font-size: 1.9rem;
    font-weight: 400;
    line-height: 1.15;
    color: var(--ink);
}}
.sender-row {{ display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }}
.avatar {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--olive);
    color: #F6F2E9;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
    font-size: 0.92rem;
    flex-shrink: 0;
}}
.sender-name {{ font-weight: 600; font-size: 0.96rem; color: var(--ink); }}
.sender-mail {{ font-family: 'IBM Plex Mono', monospace; color: var(--muted); font-size: 0.76rem; }}
.reader-body {{
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.72;
    font-size: 0.96rem;
    max-height: 540px;
    overflow-y: auto;
    border-top: 1px solid var(--line);
    padding-top: 20px;
    color: var(--ink);
}}

/* ══════════ DIMENSIONAL FOLIO ORB + MASKED POLYGON LOADER ══════════ */
.folio-orb-sphere {{
    position: relative;
    width: 96px;
    height: 96px;
    border-radius: 50%;
    --c1: #e4a23e;
    --c2: #be4a1d;
    --c3: #e8b86b78;
    --c4: #a9441e78;
    --c5: #e8b86b3d;
    box-shadow: 0 0 24px 0 var(--c3), 0 16px 40px 0 var(--c4);
    transition: transform 0.35s cubic-bezier(0.15, 0.85, 0.2, 1);
}}
.folio-orb-sphere::before {{
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border-top: solid 1px var(--c1);
    border-bottom: solid 1px var(--c2);
    background: linear-gradient(180deg, var(--c5), var(--c4));
    box-shadow: inset 0 8px 10px 0 var(--c3), inset 0 -8px 10px 0 var(--c4);
    z-index: 2;
    pointer-events: none;
}}
.folio-orb-sphere.state-review-needed {{
    box-shadow: 0 0 32px 4px rgba(190, 74, 29, 0.42), 0 16px 40px 0 rgba(169, 68, 30, 0.35);
}}
.folio-loader-box {{
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background: linear-gradient(180deg, var(--c1) 28%, var(--c2) 72%);
}}
.folio-loader-organism polygon {{ filter: blur(6.5px); }}
.folio-loader-organism .poly-1 {{ transform-origin: 75% 25%; transform: rotate(90deg); }}
.folio-loader-organism .poly-2 {{ transform-origin: 50% 50%; }}
.folio-loader-organism .poly-3 {{ transform-origin: 50% 60%; }}
.folio-loader-organism .poly-4 {{ transform-origin: 40% 40%; }}
.folio-loader-organism .poly-5 {{ transform-origin: 40% 40%; }}
.folio-loader-organism .poly-6 {{ transform-origin: 60% 40%; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--panel2); }}
::-webkit-scrollbar-thumb {{ background: var(--line); border-radius: 2px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--muted); }}
hr {{ border-color: var(--line); margin: 18px 0; }}

/* ══════════ KEYFRAME DEFINITIONS ══════════ */
@keyframes folio-typo-reveal {{
    from {{ opacity: 0; transform: translateY(7px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes folio-hero-rule-x {{
    from {{ opacity: 0; transform: scaleX(0); }}
    to {{ opacity: 1; transform: scaleX(1); }}
}}
@keyframes folio-divider-reveal {{
    from {{ transform: scaleX(0); opacity: 0.3; }}
    to {{ transform: scaleX(1); opacity: 1; }}
}}
@keyframes folio-card-reveal {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes folio-panel-fade {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes folio-slide-in-right {{
    from {{ opacity: 0; transform: translateX(10px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes folio-bar-fill {{
    from {{ transform: scaleX(0); opacity: 0.45; }}
    to {{ transform: scaleX(1); opacity: 1; }}
}}
@keyframes folio-chip-reveal {{
    from {{ opacity: 0; transform: translateY(5px) scale(0.95); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes folio-ember-pulse {{
    0%, 100% {{ box-shadow: 0 0 26px 2px var(--ember_glow), 0 16px 40px 0 rgba(169, 68, 30, 0.35); }}
    50% {{ box-shadow: 0 0 38px 8px var(--ember_glow), 0 16px 44px 0 rgba(232, 94, 59, 0.45); }}
}}
@keyframes folio-highlight-pulse-anim {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.38; }}
}}
@keyframes folio-ping {{
    75%, 100% {{ transform: scale(1.9); opacity: 0; }}
}}
@keyframes folio-pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.45; }}
}}
@keyframes folio-edge-light-sweep {{
    0% {{ transform: translate(-50%, -50%) rotate(-35deg); opacity: 0.95; }}
    12% {{ opacity: 1; }}
    58% {{ transform: translate(-50%, -50%) rotate(325deg); opacity: 0.95; }}
    80% {{ transform: translate(-50%, -50%) rotate(355deg); opacity: 0.35; }}
    100% {{ transform: translate(-50%, -50%) rotate(360deg); opacity: 0; }}
}}
@keyframes folio-edge-light-ambient {{
    0% {{ opacity: 0; }}
    14% {{ opacity: 1; }}
    65% {{ opacity: 0.78; }}
    100% {{ opacity: 0; }}
}}
@keyframes orb-drift {{
    0% {{ transform: translateY(0px) rotate(0deg) scale(1); }}
    50% {{ transform: translateY(-5px) rotate(3deg) scale(1.015); }}
    100% {{ transform: translateY(2px) rotate(-2deg) scale(0.99); }}
}}
@keyframes orb-halo {{
    0% {{ opacity: 0.65; transform: scale(0.97); }}
    100% {{ opacity: 0.9; transform: scale(1.03); }}
}}
@keyframes orb-rotation {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}
@keyframes roundness {{
    0%, 60%, 100% {{ filter: contrast(15); }}
    20%, 40% {{ filter: contrast(3); }}
}}
@keyframes colorize {{
    0%, 100% {{ filter: hue-rotate(0deg) saturate(1) brightness(1); }}
    45% {{ filter: hue-rotate(-3deg) saturate(1.05) brightness(0.99); }}
    70% {{ filter: hue-rotate(-5deg) saturate(1.08) brightness(0.97); }}
}}

/* Opening Splash Sequence CSS */
@keyframes folio-splash-core-life {{
    0% {{ opacity: 0; transform: scale(0.7); }}
    22% {{ opacity: 1; transform: scale(1); }}
    72% {{ opacity: 0.9; transform: scale(1.04); }}
    100% {{ opacity: 0; transform: scale(0.45); }}
}}
@keyframes folio-slice-assemble {{
    0% {{ opacity: 0; transform: translate(var(--ax, 0px), var(--ay, 0px)) scale(0.72); }}
    100% {{ opacity: 1; transform: translate(0px, 0px) scale(1); }}
}}
@keyframes folio-slice-depart {{
    0% {{ opacity: 1; transform: translate(0px, 0px) rotate(0deg) scale(1); }}
    18% {{ opacity: 1; transform: translate(var(--px, 0px), var(--py, 0px)) rotate(var(--prot, 0deg)) scale(1.06); }}
    100% {{ opacity: 0; transform: translate(var(--tx, 0px), var(--ty, 0px)) rotate(var(--rot, 0deg)) scale(2.8); }}
}}
@keyframes folio-wordmark-seq {{
    0% {{ opacity: 0; transform: translateY(10px); }}
    28%, 72% {{ opacity: 1; transform: translateY(0px); }}
    100% {{ opacity: 0; transform: translateY(-6px); }}
}}
@keyframes folio-backdrop-reveal {{
    0% {{ opacity: 1; visibility: visible; }}
    99% {{ opacity: 0; visibility: visible; }}
    100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
}}

{micro_css}
{typo_css}
{sec_css}
{high_css}
{load_css}

@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
}}
"""
    st.markdown(f"<style>{vars_css}{css}</style>", unsafe_allow_html=True)


def render_folio_splash_once(theme_dict: dict, enabled: bool = True):
    """Plays Folio's 8-segment splash choreography once on login/demo/replay without blocking Streamlit."""
    if not st.session_state.pop("play_folio_splash", False):
        return
    if not enabled:
        return
    splash_colors = ["#B85D45", "#C8785A", "#C4933F", "#A64833", "#BF6E52", "#D0876C", "#B6793B", "#9C402B"]
    bg_hex = theme_dict["bg"]
    ink_hex = theme_dict["ink"]
    muted_hex = theme_dict["muted"]

    segs_markup = []
    for seg in FOLIO_LOGO_SEGMENTS:
        i = seg["index"]
        mag = max(1.0, (seg["dx"] ** 2 + seg["dy"] ** 2) ** 0.5)
        ux, uy = seg["dx"] / mag, seg["dy"] / mag
        ax, ay = -seg["dx"] * 0.75, -seg["dy"] * 0.75
        px, py = ux * 8.0, uy * 8.0
        tx, ty = ux * 420.0, uy * 420.0
        rot = -9 if i % 2 == 0 else 10
        prot = -2 if i % 2 == 0 else 2
        segs_markup.append(
            f'<g style="transform-box:view-box;transform-origin:50px 50px;animation:folio-slice-assemble 520ms cubic-bezier(0.22,1,0.36,1) {i*38}ms both">'
            f'<path d="{seg["d"]}" fill="{splash_colors[i % 8]}" '
            f'style="transform-box:view-box;transform-origin:{50+ux*33:.1f}px {50+uy*33:.1f}px;--ax:{ax:.1f}px;--ay:{ay:.1f}px;--px:{px:.1f}px;--py:{py:.1f}px;--prot:{prot}deg;--tx:{tx:.1f}px;--ty:{ty:.1f}px;--rot:{rot}deg;'
            f'animation:folio-slice-depart 780ms cubic-bezier(0.32,0.04,0.22,1) {1320 + i*65}ms forwards" />'
            f'</g>'
        )

    st.markdown(
        f'<div id="folio-splash-overlay" style="position:fixed;inset:0;z-index:9999999;display:flex;flex-direction:column;align-items:center;justify-content:center;background:{bg_hex};background-image:var(--paper-grain);pointer-events:none;animation:folio-backdrop-reveal 580ms cubic-bezier(0.4,0,0.2,1) 1820ms forwards">'
        f'  <div style="position:relative;width:168px;height:168px;display:flex;align-items:center;justify-content:center">'
        f'    <div style="position:absolute;width:18px;height:18px;border-radius:50%;background:#BE4A1D;animation:folio-splash-core-life 760ms ease both"></div>'
        f'    <svg viewBox="0 0 100 100" style="width:100%;height:100%;overflow:visible" xmlns="http://www.w3.org/2000/svg">'
        f'      {"".join(segs_markup)}'
        f'    </svg>'
        f'  </div>'
        f'  <div style="text-align:center;margin-top:18px;animation:folio-wordmark-seq 1050ms cubic-bezier(0.22,1,0.36,1) 660ms both">'
        f'    <div style="font-family:\'Instrument Serif\',Georgia,serif;font-size:2.4rem;color:{ink_hex};letter-spacing:0.06em">CAMPUSMAIL</div>'
        f'    <div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.2em;color:{muted_hex};margin-top:4px">Dual-Head Observatory &middot; Thapar Archive</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def inject_folio_runtime(motion: dict, theme_dict: dict | None = None):
    """Lightweight progressive enhancer running against parent DOM (3D orb tilt, count-up numbers, splash cleanup, late Emotion theme overrides, optional Web Audio)."""
    sound_on = "true" if motion.get("sound_enabled", False) else "false"
    micro_on = "true" if motion.get("micro_interactions", True) else "false"
    typo_on = "true" if motion.get("animated_typography", True) else "false"
    t_obj = theme_dict or FOLIO_THEMES["Folio Parchment (Light)"]
    t_ink = json.dumps(t_obj.get("ink", "#151613"))
    t_ink2 = json.dumps(t_obj.get("ink2", "#525349"))
    t_muted = json.dumps(t_obj.get("muted", "#77776C"))
    t_accent = json.dumps(t_obj.get("accent", "#BE4A1D"))
    t_input = json.dumps(t_obj.get("input", "#FFFCF5"))
    t_line = json.dumps("#4A5247" if t_obj.get("is_dark") else t_obj.get("line", "#DED9CD"))
    t_panel = json.dumps(t_obj.get("panel", "#FFFCF5"))

    js = f"""
    <script>
    (function() {{
        try {{
            var pdoc = window.parent.document;
            var pwin = window.parent;

            // 0. Late <head> override sheet (wins Emotion dynamic style order) + direct tab/select patch
            var lateCss = [
                'div[data-testid="stTabs"] button, div[data-testid="stTabs"] button *, [data-baseweb="tab-list"] button, [data-baseweb="tab-list"] button *, [role="tablist"] [role="tab"], [role="tablist"] [role="tab"] * {{ color: ' + {t_ink2} + ' !important; -webkit-text-fill-color: ' + {t_ink2} + ' !important; opacity: 1 !important; }}',
                'div[data-testid="stTabs"] button[aria-selected="true"], div[data-testid="stTabs"] button[aria-selected="true"] *, [data-baseweb="tab-list"] button[aria-selected="true"], [data-baseweb="tab-list"] button[aria-selected="true"] *, [role="tablist"] [role="tab"][aria-selected="true"], [role="tablist"] [role="tab"][aria-selected="true"] * {{ color: ' + {t_accent} + ' !important; -webkit-text-fill-color: ' + {t_accent} + ' !important; }}',
                'div[data-testid="stSelectbox"] div[role="group"], div[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-baseweb="select"] > div {{ background-color: ' + {t_input} + ' !important; background: ' + {t_input} + ' !important; border: 1px solid ' + {t_line} + ' !important; border-radius: 2px !important; color: ' + {t_ink} + ' !important; }}',
                'div[data-testid="stSelectbox"] div[role="group"] > input, div[data-testid="stSelectbox"] div[role="group"] > button, div[data-testid="stSelectbox"] button[aria-label="Open"], div[data-testid="stSelectbox"] button[aria-label="Open"]:hover, div[data-testid="stSelectbox"] [data-rac] button, div[data-testid="stSelectbox"] [data-baseweb="select"] div, div[data-testid="stSelectbox"] [data-baseweb="select"] span, div[data-testid="stSelectbox"] [data-baseweb="select"] button {{ background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important; color: ' + {t_ink} + ' !important; -webkit-text-fill-color: ' + {t_ink} + ' !important; }}',
                'div[data-testid="stSelectbox"] svg {{ color: ' + {t_ink2} + ' !important; fill: ' + {t_ink2} + ' !important; opacity: 1 !important; }}',
                'div[data-testid="stSelectbox"] button[aria-label="Open"]:hover svg {{ color: ' + {t_accent} + ' !important; fill: ' + {t_accent} + ' !important; }}',
                'div[data-testid="stSelectbox"] svg path:not([fill="none"]) {{ fill: currentColor !important; }}',
                'div[data-testid="stSelectbox"] svg path[fill="none"], div[data-testid="stSelectbox"] svg rect {{ fill: none !important; }}',
                'div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], div[role="listbox"], div.react-aria-Popover, div.react-aria-ListBox {{ background-color: ' + {t_panel} + ' !important; border-color: ' + {t_line} + ' !important; }}',
                'li[role="option"], [role="option"] {{ background-color: ' + {t_panel} + ' !important; color: ' + {t_ink} + ' !important; }}'
            ].join('\\n');

            var styleEl = pdoc.getElementById('folio-late-head-overrides');
            if (!styleEl) {{
                styleEl = pdoc.createElement('style');
                styleEl.id = 'folio-late-head-overrides';
            }}
            styleEl.textContent = lateCss;
            if (pdoc.head) pdoc.head.appendChild(styleEl);

            pwin.__folioThemeCfg = {{
                ink: {t_ink}, ink2: {t_ink2}, muted: {t_muted},
                accent: {t_accent}, input: {t_input}, line: {t_line}
            }};
            pwin.__applyFolioLateFixes = function() {{
                var cfg = pwin.__folioThemeCfg;
                if (!cfg) return;
                pdoc.querySelectorAll('[role="tab"], [data-baseweb="tab"], [data-testid="stTabs"] button').forEach(function(btn) {{
                    var sel = btn.getAttribute('aria-selected') === 'true';
                    var col = sel ? cfg.accent : cfg.ink2;
                    btn.style.setProperty('color', col, 'important');
                    btn.style.setProperty('opacity', '1', 'important');
                    btn.querySelectorAll('*').forEach(function(ch) {{
                        ch.style.setProperty('color', col, 'important');
                        ch.style.setProperty('-webkit-text-fill-color', col, 'important');
                        ch.style.setProperty('opacity', '1', 'important');
                    }});
                }});
                pdoc.querySelectorAll('[data-testid="stSelectbox"], [data-baseweb="select"]').forEach(function(root) {{
                    var box = root.querySelector('[role="group"], [data-baseweb="select"] > div');
                    if (box) {{
                        box.style.setProperty('background', cfg.input, 'important');
                        box.style.setProperty('background-color', cfg.input, 'important');
                        box.style.setProperty('border', '1px solid ' + cfg.line, 'important');
                        box.style.setProperty('border-radius', '2px', 'important');
                    }}
                    root.querySelectorAll('.react-aria-ComboBox, [role="group"] > *, [role="group"] input, [role="group"] button, button[aria-label="Open"], div, span, button').forEach(function(nd) {{
                        if (nd !== box && nd !== root && !nd.matches('[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] *')) {{
                            if (nd.closest('.react-aria-ComboBox, [data-baseweb="select"]')) {{
                                nd.style.setProperty('background', 'transparent', 'important');
                                nd.style.setProperty('background-color', 'transparent', 'important');
                                nd.style.setProperty('opacity', '1', 'important');
                                if (nd.tagName === 'BUTTON') {{
                                    nd.style.setProperty('border', 'none', 'important');
                                    nd.style.setProperty('box-shadow', 'none', 'important');
                                }}
                                if (nd.tagName === 'INPUT') {{
                                    nd.style.setProperty('color', cfg.ink, 'important');
                                    nd.style.setProperty('-webkit-text-fill-color', cfg.ink, 'important');
                                }}
                            }}
                        }}
                    }});
                    root.querySelectorAll('svg').forEach(function(sv) {{
                        sv.style.setProperty('color', cfg.ink2, 'important');
                        sv.style.setProperty('fill', cfg.ink2, 'important');
                        sv.style.setProperty('opacity', '1', 'important');
                        sv.querySelectorAll('path').forEach(function(pt) {{
                            if (pt.getAttribute('fill') === 'none') {{
                                pt.style.setProperty('fill', 'none', 'important');
                            }} else {{
                                pt.style.setProperty('fill', cfg.ink2, 'important');
                            }}
                        }});
                    }});
                }});
            }};
            pwin.__applyFolioLateFixes();
            setTimeout(pwin.__applyFolioLateFixes, 80);
            setTimeout(pwin.__applyFolioLateFixes, 250);

            // Cursor-tracking warm gold spotlight across archival surfaces
            if ({micro_on} && !pwin.__folioSpotlightBound) {{
                pwin.__folioSpotlightBound = true;
                pdoc.addEventListener('mousemove', function(ev) {{
                    var card = ev.target && ev.target.closest ? ev.target.closest('.folio-spotlight, .kpi-modern, .dept-pill-card, .reader, .folio-plate') : null;
                    if (!card) return;
                    var rect = card.getBoundingClientRect();
                    card.style.setProperty('--mx', (ev.clientX - rect.left).toFixed(1) + 'px');
                    card.style.setProperty('--my', (ev.clientY - rect.top).toFixed(1) + 'px');
                }}, {{ passive: true }});
            }}
            if (!pwin.__folioLateObsBound && pdoc.body) {{
                pwin.__folioLateObsBound = true;
                var obs = new MutationObserver(function() {{
                    if (pwin.__folioLateTimer) cancelAnimationFrame(pwin.__folioLateTimer);
                    pwin.__folioLateTimer = requestAnimationFrame(function() {{
                        if (pwin.__applyFolioLateFixes) pwin.__applyFolioLateFixes();
                    }});
                }});
                obs.observe(pdoc.body, {{ childList: true, subtree: true, attributes: true, attributeFilter: ['aria-selected'] }});
            }}

            // 1. Clean up splash overlay after playback finishes
            var sp = pdoc.getElementById('folio-splash-overlay');
            if (sp) {{
                setTimeout(function() {{ if (sp && sp.parentNode) sp.parentNode.removeChild(sp); }}, 2600);
            }}

            // 2. Animated Numeric Count-up on KPI Metrics
            if ({typo_on}) {{
                var counters = pdoc.querySelectorAll('[data-folio-count]');
                counters.forEach(function(el) {{
                    if (el.dataset.counted === '1') return;
                    el.dataset.counted = '1';
                    var target = parseFloat(el.dataset.folioCount || '0');
                    var suffix = el.dataset.folioSuffix || '';
                    var decimals = parseInt(el.dataset.folioDecimals || '0', 10);
                    if (isNaN(target) || target === 0) return;
                    var start = performance.now();
                    var dur = 340;
                    function step(now) {{
                        var t = Math.min(1, (now - start) / dur);
                        var ease = 1 - Math.pow(1 - t, 3);
                        var val = target * ease;
                        var formatted = decimals > 0 ? val.toFixed(decimals) : Math.round(val).toLocaleString();
                        el.textContent = formatted + suffix;
                        if (t < 1) requestAnimationFrame(step);
                        else el.textContent = (decimals > 0 ? target.toFixed(decimals) : Math.round(target).toLocaleString()) + suffix;
                    }}
                    requestAnimationFrame(step);
                }});
            }}

            // 3. 3D Perspective Pointer Tilt on Signature Folio Orb
            if ({micro_on}) {{
                pdoc.querySelectorAll('.folio-orb-tilt').forEach(function(orb) {{
                    if (orb.dataset.tiltBound === '1') return;
                    orb.dataset.tiltBound = '1';
                    orb.addEventListener('mousemove', function(e) {{
                        var rect = orb.getBoundingClientRect();
                        var nx = (e.clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
                        var ny = (e.clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
                        var sphere = orb.querySelector('.folio-orb-sphere');
                        if (sphere) {{
                            sphere.style.transform = 'perspective(600px) rotateX(' + (-ny * 7).toFixed(1) + 'deg) rotateY(' + (nx * 7).toFixed(1) + 'deg)';
                        }}
                    }});
                    orb.addEventListener('mouseleave', function() {{
                        var sphere = orb.querySelector('.folio-orb-sphere');
                        if (sphere) sphere.style.transform = '';
                    }});
                }});
            }}

            // 4. Web Audio Tactile Brass Tick (only active when user enables Tactile Audio)
            pwin.__folioSoundEnabled = {sound_on};
            if (!pwin.__folioAudioBound) {{
                pwin.__folioAudioBound = true;
                pwin.__playBrassTick = function() {{
                    if (!pwin.__folioSoundEnabled) return;
                    try {{
                        var Ctx = pwin.AudioContext || pwin.webkitAudioContext;
                        if (!Ctx) return;
                        pwin.__folioAudioCtx = pwin.__folioAudioCtx || new Ctx();
                        var ctx = pwin.__folioAudioCtx;
                        if (ctx.state === 'suspended') ctx.resume();
                        var osc = ctx.createOscillator();
                        var gain = ctx.createGain();
                        osc.type = 'triangle';
                        osc.frequency.setValueAtTime(2400, ctx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(420, ctx.currentTime + 0.03);
                        gain.gain.setValueAtTime(0.05, ctx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.035);
                        osc.connect(gain); gain.connect(ctx.destination);
                        osc.start(); osc.stop(ctx.currentTime + 0.04);
                    }} catch(e) {{}}
                }};
                pdoc.addEventListener('click', function(ev) {{
                    if (!pwin.__folioSoundEnabled) return;
                    if (ev.target && ev.target.closest('button')) pwin.__playBrassTick();
                }}, true);
            }}
            }} catch(e) {{}}
        }})();
        </script>
    """
    components.html(js, height=0, width=0)


def render_folio_table(df, highlight_first: bool = False):
    """Renders a crisp theme-native Folio archival HTML ledger table with zero dark-mode canvas flash or clipping."""
    import pandas as pd

    if df is None or df.empty:
        return
    headers = []
    is_num_col = []
    for col in df.columns:
        s_vals = df[col].dropna().astype(str).tolist()
        numeric_like = False
        if s_vals and all(
            v.replace(".", "", 1).replace("-", "", 1).replace("%", "", 1).replace(",", "").strip().isdigit()
            for v in s_vals[:8]
        ):
            numeric_like = True
        is_num_col.append(numeric_like)
        cls_attr = " class='num'" if numeric_like else ""
        headers.append(f"<th{cls_attr}>{_esc(col)}</th>")

    rows_html = []
    for r_i, (_, row) in enumerate(df.iterrows()):
        tr_cls = " class='folio-row-champion'" if (highlight_first and r_i == 0) else ""
        tds = []
        for c_i, col in enumerate(df.columns):
            val = row[col]
            cell_txt = "" if pd.isna(val) else str(val)
            cls_attr = " class='num'" if is_num_col[c_i] else ""
            tds.append(f"<td{cls_attr}>{_esc(cell_txt)}</td>")
        rows_html.append(f"<tr{tr_cls}>{''.join(tds)}</tr>")

    tbl_cls = "folio-table folio-table-compact" if len(df.columns) >= 6 else "folio-table"
    st.markdown(
        f"<div class='folio-table-wrap'>"
        f"  <table class='{tbl_cls}'>"
        f"    <thead><tr>{''.join(headers)}</tr></thead>"
        f"    <tbody>{''.join(rows_html)}</tbody>"
        f"  </table>"
        f"</div>",
        unsafe_allow_html=True,
    )
