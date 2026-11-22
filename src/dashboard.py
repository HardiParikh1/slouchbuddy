import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import dashboard_data as data
import dashboard_theme as theme_mod

st.set_page_config(page_title="Posture Monitor", page_icon="🧍", layout="wide")


def stat_card(label, value, sub=None, status_key=None, theme=None):
    pill_html = ""
    if status_key:
        color = theme_mod.STATUS[status_key]
        icon = {"good": "●", "warning": "●", "critical": "●"}[status_key]
        label_text = {"good": "Good", "warning": "Fair", "critical": "Poor"}[status_key]
        pill_html = (
            f'<div class="pm-status-pill" style="background:{color}22; color:{color};">'
            f"{icon} {label_text}</div>"
        )
    sub_html = f'<div class="pm-card-sub">{sub}</div>' if sub else ""
    card_html = (
        '<div class="pm-card">'
        f'<div class="pm-card-label">{label}</div>'
        f'<div class="pm-card-value">{value}</div>'
        f"{sub_html}{pill_html}"
        "</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)


def meter_card(label, pct, theme):
    status_key, _ = theme_mod.score_status(pct)
    color = theme_mod.STATUS[status_key]
    card_html = (
        '<div class="pm-card">'
        f'<div class="pm-card-label">{label}</div>'
        f'<div class="pm-card-value">{pct:.0f}%</div>'
        '<div class="pm-meter-track">'
        f'<div class="pm-meter-fill" style="width:{min(pct, 100):.0f}%; background:{color};"></div>'
        "</div>"
        "</div>"
    )
    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )


TICK_FORMATS = {"Day": "%H:%M", "Week": "%a %d", "Month": "%b %d", "Year": "%b"}


def score_over_time_chart(agg, theme, view, start, end):
    """agg: output of dashboard_data.aggregate_scores (average score per time bucket)."""
    fig = go.Figure()
    fig.add_hline(y=80, line_dash="dot", line_color=theme["baseline"], line_width=1,
                   annotation_text="Good (80)", annotation_font_color=theme["ink_muted"],
                   annotation_font_size=11)
    fig.add_hline(y=50, line_dash="dot", line_color=theme["baseline"], line_width=1,
                   annotation_text="Fair (50)", annotation_font_color=theme["ink_muted"],
                   annotation_font_size=11)
    fig.add_trace(
        go.Scatter(
            x=agg["timestamp"],
            y=agg["avg_score"],
            mode="lines+markers",
            line=dict(color=theme["series_1"], width=2, shape="linear"),
            marker=dict(size=7, color=theme["series_1"]),
            customdata=agg["samples"],
            hovertemplate="%{y:.0f} / 100 avg (%{customdata} samples)<extra></extra>",
        )
    )
    layout = theme_mod.plotly_layout(theme, height=320)
    layout["yaxis"]["range"] = [0, 105]
    layout["xaxis"]["title"] = None
    layout["yaxis"]["title"] = None
    # Pin the axis to the selected period so a lone point can't zoom into microseconds.
    layout["xaxis"]["range"] = [start.isoformat(), end.isoformat()]
    layout["xaxis"]["tickformat"] = TICK_FORMATS[view]
    layout["margin"] = dict(l=10, r=90, t=10, b=10)
    fig.update_layout(**layout)
    return fig


def top_issues_chart(reason_counts, theme):
    if not reason_counts:
        return None
    items = reason_counts.most_common()
    labels = [k.title() for k, _ in items][::-1]
    values = [v for _, v in items][::-1]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=theme["series_1"]),
            text=values,
            textposition="outside",
            textfont=dict(color=theme["ink_secondary"]),
            hovertemplate="%{y}: %{x} samples<extra></extra>",
        )
    )
    layout = theme_mod.plotly_layout(theme, height=max(220, 60 * len(labels)))
    layout["xaxis"]["title"] = None
    layout["yaxis"]["title"] = None
    layout["xaxis"]["range"] = [0, max(values) * 1.18]
    layout["margin"] = dict(l=10, r=20, t=10, b=10)
    fig.update_layout(**layout)
    return fig


def session_trend_chart(session_df, theme):
    fig = go.Figure()
    fig.add_hline(y=80, line_dash="dot", line_color=theme["baseline"], line_width=1)
    fig.add_trace(
        go.Scatter(
            x=session_df["session_start"],
            y=session_df["avg_score"],
            mode="lines+markers",
            line=dict(color=theme["series_1"], width=2),
            marker=dict(size=8, color=theme["series_1"]),
            hovertemplate="%{y:.0f} / 100<extra></extra>",
        )
    )
    layout = theme_mod.plotly_layout(theme, height=280)
    layout["yaxis"]["range"] = [0, 105]
    layout["xaxis"]["title"] = None
    layout["yaxis"]["title"] = None
    fig.update_layout(**layout)
    return fig


def main():
    with st.sidebar:
        st.markdown("### Settings")
        mode = st.radio("Theme", ["Light", "Dark"], horizontal=True)
        st.markdown("---")

    theme = theme_mod.get_theme(mode)
    st.markdown(theme_mod.inject_css(theme), unsafe_allow_html=True)

    st.markdown('<div class="pm-title">Posture Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pm-subtitle">Session history and posture trends from your desk setup.</div>',
        unsafe_allow_html=True,
    )

    files = data.list_session_files()

    if not files:
        st.info(
            f"No session data yet. Run `python src/app.py` and calibrate to start "
            f"tracking — logs will appear in `{config.SESSIONS_DIR}/`."
        )
        return

    with st.sidebar:
        labels = [data._session_label(f) for f in files]
        options = ["All sessions"] + labels
        choice = st.selectbox("Session", options)

    if choice == "All sessions":
        selected_files = files
    else:
        selected_files = [files[labels.index(choice)]]

    df = data.load_all_sessions(selected_files)
    all_df = data.load_all_sessions(files)
    session_summary = data.session_level_summary(all_df)

    if df.empty:
        st.warning("Selected session has no data yet.")
        return

    avg_score = df["posture_score"].mean()
    good_pct = (df["status"] == "GOOD POSTURE").sum() / len(df) * 100
    longest_bad_streak = df["bad_duration"].max()
    status_key, _ = theme_mod.score_status(avg_score)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        stat_card("Average Score", f"{avg_score:.0f}/100", status_key=status_key, theme=theme)
    with col2:
        meter_card("Good Posture", good_pct, theme)
    with col3:
        stat_card("Longest Bad Streak", f"{longest_bad_streak:.0f}s", theme=theme)
    with col4:
        stat_card("Sessions Tracked", f"{len(files)}", sub=f"{len(all_df):,} samples total", theme=theme)

    st.markdown('<div class="pm-section-title">Posture score over time</div>', unsafe_allow_html=True)
    first_day = df["timestamp"].min().date()
    last_day = df["timestamp"].max().date()

    view_col, pick_col, _ = st.columns([3, 2, 3])
    with view_col:
        view = st.radio("View by", data.SCORE_VIEWS, horizontal=True, label_visibility="collapsed")
    with pick_col:
        if view in ("Day", "Week"):
            anchor = st.date_input(
                "Day" if view == "Day" else "Any day in the week",
                value=last_day, min_value=first_day, max_value=last_day,
                label_visibility="collapsed",
            )
        elif view == "Month":
            months = pd.period_range(first_day, last_day, freq="M")[::-1]
            anchor = st.selectbox(
                "Month", months, format_func=lambda m: m.strftime("%B %Y"), label_visibility="collapsed"
            ).start_time
        else:
            years = list(range(last_day.year, first_day.year - 1, -1))
            anchor = pd.Timestamp(
                year=st.selectbox("Year", years, label_visibility="collapsed"), month=1, day=1
            )

    agg, start, end = data.aggregate_scores(df, view, anchor)
    if agg.empty:
        st.info("No samples in this period. Pick another one.")
    else:
        st.plotly_chart(score_over_time_chart(agg, theme, view, start, end),
                        use_container_width=True, config={"displayModeBar": False})

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="pm-section-title">Most frequent issues</div>', unsafe_allow_html=True)
        reason_counts = data.extract_reason_counts(df["status"])
        fig = top_issues_chart(reason_counts, theme)
        if fig is None:
            st.markdown(
                f'<div class="pm-card" style="color:{theme["ink_secondary"]};">'
                "No posture issues logged in this selection. 🎉</div>",
                unsafe_allow_html=True,
            )
        else:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="pm-section-title">Session-level trend</div>', unsafe_allow_html=True)
        if len(session_summary) < 2:
            st.markdown(
                f'<div class="pm-card" style="color:{theme["ink_secondary"]};">'
                "Track a few more sessions to see your trend over time.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.plotly_chart(
                session_trend_chart(session_summary, theme), use_container_width=True,
                config={"displayModeBar": False},
            )

    with st.expander("Raw session data"):
        st.dataframe(
            df[["timestamp", "session_label", "posture_score", "status", "bad_duration"]],
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
