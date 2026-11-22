# "Eucalyptus grove": cream and leaf greens by day, a mossy night grove in dark mode.
LIGHT = {
    "surface": "#fffdf7",
    "page": "#f6f1e3",
    "page_glow": "#e4efdc",
    "sidebar": "#e9f0e1",
    "ink_primary": "#2b3a32",
    "ink_secondary": "#55685c",
    "ink_muted": "#8a9a8f",
    "gridline": "#e8e3d2",
    "baseline": "#d3cbb2",
    "border": "rgba(80,112,90,0.20)",
    "shadow": "rgba(70,100,80,0.14)",
    "series_1": "#5b9a76",
    "series_1_fill": "rgba(91,154,118,0.18)",
    "accent": "#f2a7b5",
    "honey": "#f3c969",
}

DARK = {
    "surface": "#26332c",
    "page": "#16201b",
    "page_glow": "#22332a",
    "sidebar": "#1c2a23",
    "ink_primary": "#f4f1e4",
    "ink_secondary": "#cbd6c9",
    "ink_muted": "#93a597",
    "gridline": "#31413a",
    "baseline": "#46584e",
    "border": "rgba(190,225,200,0.16)",
    "shadow": "rgba(0,0,0,0.35)",
    "series_1": "#8fd1a8",
    "series_1_fill": "rgba(143,209,168,0.18)",
    "accent": "#f2a7b5",
    "honey": "#f3c969",
}

# Fixed status palette - never themed, same hexes in both modes.
STATUS = {
    "good": "#4caf7a",
    "warning": "#efb94b",
    "critical": "#e0725f",
}


def get_theme(mode):
    return DARK if mode == "Dark" else LIGHT


def score_status(score):
    if score >= 80:
        return "good", "Good"
    elif score >= 50:
        return "warning", "Fair"
    else:
        return "critical", "Poor"


def plotly_layout(theme, height=320):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito, system-ui, -apple-system, 'Segoe UI', sans-serif", color=theme["ink_secondary"], size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        xaxis=dict(
            gridcolor=theme["gridline"],
            zerolinecolor=theme["baseline"],
            linecolor=theme["baseline"],
            tickfont=dict(color=theme["ink_muted"]),
        ),
        yaxis=dict(
            gridcolor=theme["gridline"],
            zerolinecolor=theme["baseline"],
            linecolor=theme["baseline"],
            tickfont=dict(color=theme["ink_muted"]),
        ),
        hoverlabel=dict(
            bgcolor=theme["surface"],
            bordercolor=theme["border"],
            font=dict(color=theme["ink_primary"]),
        ),
        showlegend=False,
    )


def inject_css(theme):
    t = theme
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:wght@400;600;700&display=swap');

    html, body, .stApp, [data-testid="stMarkdownContainer"], label, p, span, div {{
        font-family: 'Nunito', system-ui, sans-serif;
    }}
    .stApp {{
        background:
            radial-gradient(1100px 520px at 85% -8%, {t["page_glow"]} 0%, transparent 70%),
            radial-gradient(900px 480px at -5% 105%, {t["page_glow"]} 0%, transparent 70%),
            {t["page"]};
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{
        background: {t["sidebar"]};
        border-right: 1px solid {t["border"]};
    }}
    [data-testid="stSidebar"] h3 {{ font-family: 'Fredoka', sans-serif; color: {t["ink_primary"]}; }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; position: relative; z-index: 1; max-width: 1180px; }}

    /* Streamlit's widgets default to a dark theme; make them follow ours. */
    [data-testid="stWidgetLabel"] p, [data-testid="stSidebar"] label p,
    [data-testid="stRadio"] label, [data-testid="stRadio"] label p, [data-testid="stRadio"] label span {{
        color: {t["ink_primary"]} !important;
    }}
    [data-baseweb="select"] > div, [data-testid="stDateInput"] > div > div, [data-baseweb="input"] {{
        background: {t["surface"]} !important;
        border-color: {t["border"]} !important;
        border-radius: 14px !important;
        color: {t["ink_primary"]} !important;
    }}
    [data-baseweb="select"] *, [data-testid="stDateInput"] input {{ color: {t["ink_primary"]} !important; }}
    [data-testid="stSelectbox"] [role="group"], [data-testid="stDateInput"] [role="group"] {{
        background: {t["surface"]} !important; border: 1px solid {t["border"]} !important; border-radius: 14px !important;
    }}
    [data-testid="stSelectbox"] input, [data-testid="stDateInput"] input {{
        color: {t["ink_primary"]} !important; -webkit-text-fill-color: {t["ink_primary"]} !important;
    }}
    [data-testid="stSelectbox"] button, [data-testid="stDateInput"] button {{ color: {t["ink_secondary"]} !important; }}
    [role="listbox"] {{ background: {t["surface"]} !important; border-radius: 14px !important; }}
    [role="option"] {{ color: {t["ink_primary"]} !important; }}
    /* Streamlit's own promo nudge isn't part of the app */
    [data-testid="stSkillsNudge"], [data-testid="stSkillsNudgeAnchor"] {{ display: none !important; }}
    [data-testid="stExpander"] {{
        background: {t["surface"]}; border: 1px solid {t["border"]}; border-radius: 16px;
    }}
    [data-testid="stExpander"] summary p {{ color: {t["ink_primary"]} !important; }}

    /* Hero: koala + speech bubble */
    .sb-hero {{ display: flex; align-items: center; gap: 1.4rem; margin: 0.2rem 0 1.6rem 0; flex-wrap: wrap; }}
    .sb-koala {{
        width: 150px; height: 150px; flex: none; transform-origin: 50% 90%;
        animation: sb-bob 3.2s ease-in-out infinite, sb-wiggle 9s ease-in-out infinite;
        filter: drop-shadow(0 8px 10px {t["shadow"]});
    }}
    .sb-hero-text {{ flex: 1; min-width: 240px; }}
    .sb-title {{
        font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 2.6rem; line-height: 1.05;
        color: {t["ink_primary"]}; letter-spacing: 0.01em;
    }}
    .sb-title span {{ color: {t["series_1"]}; }}
    .sb-subtitle {{ color: {t["ink_secondary"]}; font-size: 1rem; margin: 0.2rem 0 0.8rem 0; }}
    .sb-bubble {{
        position: relative; display: inline-block; max-width: 520px; padding: 0.7rem 1.05rem;
        background: {t["surface"]}; color: {t["ink_primary"]}; font-weight: 600;
        border: 2px solid {t["border"]}; border-radius: 18px; box-shadow: 0 6px 18px {t["shadow"]};
    }}
    .sb-bubble::before {{
        content: ""; position: absolute; left: -9px; top: 50%; width: 14px; height: 14px;
        background: {t["surface"]}; border-left: 2px solid {t["border"]}; border-bottom: 2px solid {t["border"]};
        transform: translateY(-50%) rotate(45deg);
    }}
    @keyframes sb-bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-9px); }} }}
    @keyframes sb-wiggle {{
        0%, 86%, 100% {{ rotate: 0deg; }} 89% {{ rotate: -5deg; }} 92% {{ rotate: 5deg; }} 95% {{ rotate: -3deg; }}
    }}

    /* Falling leaves */
    .sb-leaves {{ position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }}
    .sb-leaf {{
        position: absolute; top: -8%; left: calc(var(--i) * 11% + 2%); font-size: calc(18px + var(--i) * 1.6px);
        opacity: 0.35; animation: sb-fall calc(16s + var(--i) * 2.3s) linear infinite;
        animation-delay: calc(var(--i) * -3.1s);
    }}
    @keyframes sb-fall {{
        0%   {{ transform: translate(0, 0) rotate(0deg); }}
        25%  {{ transform: translate(28px, 28vh) rotate(70deg); }}
        50%  {{ transform: translate(-22px, 56vh) rotate(150deg); }}
        75%  {{ transform: translate(30px, 84vh) rotate(230deg); }}
        100% {{ transform: translate(-10px, 112vh) rotate(300deg); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        .sb-koala, .sb-leaf {{ animation: none; }}
    }}

    /* Cards */
    .pm-card {{
        background-color: {t["surface"]}; border: 1px solid {t["border"]}; border-radius: 22px;
        padding: 1.1rem 1.3rem; height: 100%; min-height: 9.6rem; box-shadow: 0 8px 22px {t["shadow"]};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .pm-card:hover {{ transform: translateY(-4px) rotate(-0.4deg); box-shadow: 0 14px 28px {t["shadow"]}; }}
    .pm-card-label {{
        color: {t["ink_muted"]}; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.04em; margin-bottom: 0.4rem; white-space: nowrap;
    }}
    .pm-card-value {{
        color: {t["ink_primary"]}; font-family: 'Fredoka', sans-serif; font-size: 2.3rem; font-weight: 600; line-height: 1.1;
    }}
    .pm-card-sub {{ color: {t["ink_secondary"]}; font-size: 0.85rem; margin-top: 0.3rem; }}
    .pm-status-pill {{
        display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.8rem; font-weight: 700;
        margin-top: 0.4rem; padding: 0.15rem 0.65rem; border-radius: 999px;
    }}
    .pm-section-title {{
        color: {t["ink_primary"]}; font-family: 'Fredoka', sans-serif; font-size: 1.35rem; font-weight: 600;
        margin: 2rem 0 0.7rem 0;
    }}
    .pm-meter-track {{
        background-color: {t["gridline"]}; border-radius: 999px; height: 12px; width: 100%;
        margin-top: 0.6rem; overflow: hidden;
    }}
    .pm-meter-fill {{ height: 100%; border-radius: 999px; transition: width 0.8s ease; }}

    .sb-empty {{ text-align: center; padding: 2.2rem 1rem; }}
    .sb-empty img {{ width: 170px; animation: sb-bob 4s ease-in-out infinite; }}
    .sb-empty p {{ color: {t["ink_secondary"]}; font-size: 1.05rem; }}
    .sb-footer {{ text-align: center; margin-top: 3rem; color: {t["ink_muted"]}; font-size: 0.9rem; }}
    .sb-footer img {{ width: 64px; vertical-align: middle; margin-right: 0.5rem; }}
    </style>
    """
