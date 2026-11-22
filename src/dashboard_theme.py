LIGHT = {
    "surface": "#fcfcfb",
    "page": "#f9f9f7",
    "ink_primary": "#0b0b0b",
    "ink_secondary": "#52514e",
    "ink_muted": "#898781",
    "gridline": "#e1e0d9",
    "baseline": "#c3c2b7",
    "border": "rgba(11,11,11,0.10)",
    "series_1": "#2a78d6",
    "series_1_fill": "rgba(42,120,214,0.12)",
}

DARK = {
    "surface": "#1a1a19",
    "page": "#0d0d0d",
    "ink_primary": "#ffffff",
    "ink_secondary": "#c3c2b7",
    "ink_muted": "#898781",
    "gridline": "#2c2c2a",
    "baseline": "#383835",
    "border": "rgba(255,255,255,0.10)",
    "series_1": "#3987e5",
    "series_1_fill": "rgba(57,135,229,0.16)",
}

# Fixed status palette - never themed, same hexes in both modes.
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "critical": "#d03b3b",
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
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=theme["ink_secondary"], size=13),
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
    return f"""
    <style>
    .stApp {{
        background-color: {theme["page"]};
    }}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    .pm-title {{
        color: {theme["ink_primary"]};
        font-size: 1.9rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }}
    .pm-subtitle {{
        color: {theme["ink_secondary"]};
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }}
    .pm-card {{
        background-color: {theme["surface"]};
        border: 1px solid {theme["border"]};
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        height: 100%;
    }}
    .pm-card-label {{
        color: {theme["ink_muted"]};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.4rem;
    }}
    .pm-card-value {{
        color: {theme["ink_primary"]};
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.1;
    }}
    .pm-card-sub {{
        color: {theme["ink_secondary"]};
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }}
    .pm-status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.4rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
    }}
    .pm-section-title {{
        color: {theme["ink_primary"]};
        font-size: 1.1rem;
        font-weight: 700;
        margin: 1.8rem 0 0.6rem 0;
    }}
    /* Streamlit's base theme is dark, so widget text is white; force it to follow ours
       in the main area (otherwise the time-range radio labels are invisible on light). */
    [data-testid="stMain"] [data-testid="stRadio"] label,
    [data-testid="stMain"] [data-testid="stRadio"] label p,
    [data-testid="stMain"] [data-testid="stRadio"] label span {{
        color: {theme["ink_primary"]} !important;
    }}
    .pm-meter-track {{
        background-color: {theme["gridline"]};
        border-radius: 999px;
        height: 10px;
        width: 100%;
        margin-top: 0.6rem;
        overflow: hidden;
    }}
    .pm-meter-fill {{
        height: 100%;
        border-radius: 999px;
    }}
    </style>
    """
