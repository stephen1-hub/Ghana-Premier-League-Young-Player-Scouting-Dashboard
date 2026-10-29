import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# Ghana Premier League 2026/27 — Matchweek 8 Scouting Dashboard
# ============================================================

st.set_page_config(
    page_title="GPL 2026/27 | Scouting Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.hero {
    padding: 1.5rem 1.7rem;
    border-radius: 16px;
    background: linear-gradient(115deg, #102b46 0%, #176b55 100%);
    color: white;
    margin-bottom: 1.1rem;
}
.hero h1 {margin: 0; font-size: 2rem;}
.hero p {margin: .45rem 0 0 0; opacity: .92;}
.kpi {
    border: 1px solid rgba(128,128,128,.30);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    min-height: 100px;
}
.kpi-label {font-size: .88rem; opacity: .75;}
.kpi-value {font-size: 1.8rem; font-weight: 700; margin-top: .25rem;}
.note {
    border-left: 4px solid #e0a126;
    padding: .8rem 1rem;
    border-radius: 5px;
    background: rgba(224,161,38,.09);
}
</style>
""", unsafe_allow_html=True)

POSITION_GROUPS = {
    "Forward": [
        "Forward", "Centre Forward", "Secondary Striker",
        "Left Wing", "Right Wing"
    ],
    "Midfielder": [
        "Midfielder", "Central Midfield", "Attacking Midfield",
        "Defensive Midfield", "Left Midfield"
    ],
    "Defender": [
        "Defender", "Centre Back", "Left Back", "Right Back"
    ],
    "Goalkeeper": ["Goalkeeper"],
}

POSITION_LOOKUP = {
    position: group
    for group, positions in POSITION_GROUPS.items()
    for position in positions
}

NUMERIC_COLUMNS = [
    "age", "minutes_played_overall", "goals_overall",
    "assists_overall", "xg_total_overall", "xg_per_90_overall",
    "xa_total_overall", "xa_per_90_overall",
    "shots_total_overall", "shots_per_90_overall",
    "shot_conversion_rate_overall",
    "shot_accuraccy_percentage_overall",
    "tackles_total_overall", "interceptions_total_overall",
    "clearances_total_overall", "duels_won_total_overall",
    "average_rating_overall", "market_value",
]

REQUIRED_COLUMNS = [
    "full_name", "Current Club", "position", "age",
    "minutes_played_overall", "goals_overall",
]

def clean_data(raw):
    df = raw.copy()
    # Handle common alternate header spelling/capitalisation.
    df.columns = [str(c).strip() for c in df.columns]
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(
                f"Required column '{col}' is missing. "
                "Please upload the Ghana Premier League player stats CSV."
            )
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["full_name"] = df["full_name"].astype("string").str.strip()
    df["Current Club"] = df["Current Club"].astype("string").str.strip()
    df["position"] = df["position"].astype("string").str.strip()

    df = df[df["full_name"].notna() & df["full_name"].ne("")].copy()
    df["scouting_group"] = df["position"].map(POSITION_LOOKUP).fillna("Other")

    minutes = df["minutes_played_overall"]
    goals = df["goals_overall"]
    assists = (
        df["assists_overall"]
        if "assists_overall" in df.columns
        else pd.Series(np.nan, index=df.index)
    )

    df["goals_per90_calc"] = np.where(
        minutes.gt(0) & goals.notna(),
        goals / minutes * 90,
        np.nan
    )
    df["goal_contributions"] = goals.fillna(0) + assists.fillna(0)
    df["contributions_per90_calc"] = np.where(
        minutes.gt(0),
        df["goal_contributions"] / minutes * 90,
        np.nan
    )

    if "xg_total_overall" in df.columns:
        df["xg_review_flag"] = (
            goals.gt(0) & df["xg_total_overall"].eq(0)
        )
        df["xg_missing_flag"] = goals.gt(0) & df["xg_total_overall"].isna()
    else:
        df["xg_review_flag"] = False
        df["xg_missing_flag"] = goals.gt(0)

    return df

def metric_status(df, col):
    if col not in df.columns:
        return "Column unavailable"
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        return "All missing"
    if s.fillna(0).ne(0).sum() == 0:
        return "All zero / no variation"
    if s.nunique(dropna=True) <= 1:
        return "Constant"
    return "Has variation"

def kpi(col, label, value):
    with col:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True
        )

# Header
st.markdown("""
<div class="hero">
  <h1>⚽ Ghana Premier League 2026/27</h1>
  <h2 style="margin:.25rem 0 0 0;font-weight:500;">Young Player Scouting Dashboard</h2>
  <p>Reporting period: After Matchweek 8 · Provisional early-season analysis</p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Use this dashboard to screen emerging players and compare recorded attacking output. "
    "It is not a final-season ranking or a complete player-quality model."
)

# Data input
# By default, load the CSV stored beside this app. You can still upload
# another CSV from the sidebar when you need to.
from pathlib import Path

DATA_FILENAME = "ghana-ghana-premier-league-players-2026-to-2027-stats.csv"
APP_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = APP_DIR / DATA_FILENAME

with st.sidebar:
    st.header("📂 Data")
    use_upload = st.checkbox(
        "Upload a different CSV instead",
        value=False,
        help="Leave this unchecked to load the CSV saved beside app50.py."
    )
    uploaded = None
    if use_upload:
        uploaded = st.file_uploader(
            "Upload player statistics CSV",
            type=["csv"],
            help="Upload an alternative Ghana Premier League player-stats CSV."
        )
    st.caption(
        "Source: uploaded file" if use_upload
        else f"Source: {DATA_FILENAME}"
    )
    st.divider()
    st.header("🎛️ Scouting filters")

try:
    if use_upload:
        if uploaded is None:
            st.info("Upload a CSV in the sidebar, or uncheck the upload option to use the local CSV.")
            st.stop()
        raw = pd.read_csv(uploaded)
        data_source_label = uploaded.name
    else:
        if not DEFAULT_CSV_PATH.exists():
            st.error(
                f"Could not find the default CSV file: {DEFAULT_CSV_PATH}. "
                "Place the CSV in the same folder as app50.py, or enable the upload option."
            )
            st.stop()
        raw = pd.read_csv(DEFAULT_CSV_PATH)
        data_source_label = DATA_FILENAME

    df = clean_data(raw)
    st.caption(f"Loaded data from: `{data_source_label}` · {len(df):,} named player records")
except Exception as exc:
    st.error(f"Could not load the file: {exc}")
    st.stop()

# Sidebar controls
with st.sidebar:
    young_only = st.checkbox("Young-player focus (age ≤ 23)", value=True)

    valid_ages = df["age"].dropna()
    if valid_ages.empty:
        age_min, age_max = 16, 44
    else:
        age_min = int(max(0, np.floor(valid_ages.min())))
        age_max = int(np.ceil(valid_ages.max()))
    age_range = st.slider(
        "Age range",
        min_value=age_min,
        max_value=max(age_min, age_max),
        value=(age_min, min(23, age_max)) if age_min <= min(23, age_max) else (age_min, age_max)
    )

    max_minutes = int(df["minutes_played_overall"].fillna(0).max())
    min_minutes = st.slider(
        "Minimum minutes played",
        min_value=0,
        max_value=max(0, max_minutes),
        value=min(450, max_minutes),
        step=30 if max_minutes >= 30 else 1
    )

    available_groups = ["All positions"] + sorted(df["scouting_group"].dropna().unique().tolist())
    position_choice = st.selectbox("Position group", available_groups, index=0)

    clubs = sorted(df["Current Club"].dropna().astype(str).unique().tolist())
    club_choices = st.multiselect("Clubs (optional)", clubs, default=[])

    top_n = st.select_slider("Players to show", options=[5, 10, 15, 20, 30], value=10)

# Apply filters
filtered = df.copy()
if young_only:
    filtered = filtered[filtered["age"].le(23)]
else:
    filtered = filtered[filtered["age"].between(age_range[0], age_range[1])]

# When young-only is on, still allow a chosen upper age range to limit further.
if young_only:
    filtered = filtered[filtered["age"].between(age_range[0], min(23, age_range[1]))]

filtered = filtered[filtered["minutes_played_overall"].ge(min_minutes)]

if position_choice != "All positions":
    filtered = filtered[filtered["scouting_group"].eq(position_choice)]

if club_choices:
    filtered = filtered[filtered["Current Club"].astype(str).isin(club_choices)]

# Exclude xG anomaly only from primary ranking, not from data tables/audit.
rankable = filtered[~filtered["xg_review_flag"]].copy()

# KPIs
total_players = len(filtered)
scorers = int(filtered["goals_overall"].gt(0).sum())
total_goals = int(filtered["goals_overall"].fillna(0).sum())
review_count = int(filtered["xg_review_flag"].sum())

st.subheader("Scouting snapshot")
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Players matching filters", f"{total_players:,}")
kpi(c2, "Players with ≥1 goal", f"{scorers:,}")
kpi(c3, "Recorded goals", f"{total_goals:,}")
kpi(c4, "Goals/xG records flagged", f"{review_count:,}")

st.write("")
tab_overview, tab_positions, tab_quality, tab_data = st.tabs([
    "📊 Overview", "🧭 Position comparison", "🧪 Data quality", "📋 Player data"
])

with tab_overview:
    left, right = st.columns((1, 1))

    with left:
        st.subheader("Eligible players by position")
        position_counts = (
            filtered["scouting_group"]
            .value_counts()
            .rename_axis("Position group")
            .reset_index(name="Players")
        )
        if not position_counts.empty:
            fig = px.bar(
                position_counts, x="Position group", y="Players",
                color="Position group", text="Players",
                title="Scouting pool distribution"
            )
            fig.update_layout(showlegend=False, height=390)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No players match the current filters.")

    with right:
        st.subheader("Age vs scoring rate")
        scatter = rankable[
            rankable["goals_per90_calc"].notna()
            & rankable["age"].notna()
        ].copy()
        if not scatter.empty:
            fig = px.scatter(
                scatter,
                x="age",
                y="goals_per90_calc",
                size="minutes_played_overall",
                color="scouting_group",
                hover_name="full_name",
                hover_data={
                    "Current Club": True,
                    "position": True,
                    "goals_overall": True,
                    "minutes_played_overall": True,
                    "goals_per90_calc": ":.3f",
                },
                labels={
                    "age": "Age",
                    "goals_per90_calc": "Goals per 90",
                    "scouting_group": "Position group",
                    "minutes_played_overall": "Minutes"
                },
                title="Age, minutes and scoring output"
            )
            fig.update_layout(height=390)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usable scoring-rate records for this view.")

    st.subheader("Top scoring rates")
    st.caption(
        "Primary leaderboard excludes players with goals but zero recorded xG "
        "until those records are verified. This is a data-quality precaution, "
        "not a claim that their goals are invalid."
    )
    leaders = rankable[
        rankable["scouting_group"].isin(["Forward", "Midfielder", "Defender"])
        & rankable["goals_per90_calc"].notna()
    ].sort_values(
        ["goals_per90_calc", "goals_overall"],
        ascending=False
    ).head(top_n).copy()

    if not leaders.empty:
        leaders["player_club"] = (
            leaders["full_name"] + " — " + leaders["Current Club"].astype(str)
        )
        fig = px.bar(
            leaders.sort_values("goals_per90_calc"),
            x="goals_per90_calc",
            y="player_club",
            orientation="h",
            color="scouting_group",
            hover_data=[
                "position", "age", "minutes_played_overall",
                "goals_overall", "assists_overall"
            ],
            labels={
                "goals_per90_calc": "Goals per 90",
                "player_club": "",
                "scouting_group": "Position group"
            }
        )
        fig.update_layout(height=max(430, 32 * len(leaders)))
        fig.update_traces(texttemplate="%{x:.3f}", textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No eligible outfield players to rank.")

with tab_positions:
    st.subheader("Compare players within their role")
    st.caption(
        "Goals per 90 is only an attacking-output measure. It does not measure "
        "defensive quality or overall player ability."
    )

    groups = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
    group_tabs = st.tabs(groups)

    for group_tab, group in zip(group_tabs, groups):
        with group_tab:
            subset = filtered[filtered["scouting_group"].eq(group)].copy()

            if group == "Goalkeeper":
                st.info(
                    "Goalkeeper performance cannot be ranked with goals per 90. "
                    "This dataset's save and rating fields were zero-filled in the "
                    "initial audit. Obtain verified saves, goals conceded, save "
                    "percentage and distribution metrics."
                )
                keeper_cols = [
                    c for c in [
                        "full_name", "Current Club", "age",
                        "minutes_played_overall"
                    ] if c in subset.columns
                ]
                st.dataframe(
                    subset[keeper_cols].sort_values(
                        "minutes_played_overall", ascending=False
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                subset = subset.sort_values(
                    ["goals_per90_calc", "goals_overall"],
                    ascending=False
                )
                show_cols = [
                    c for c in [
                        "full_name", "Current Club", "position", "age",
                        "minutes_played_overall", "goals_overall",
                        "assists_overall", "goals_per90_calc",
                        "contributions_per90_calc", "xg_total_overall",
                        "xg_review_flag"
                    ] if c in subset.columns
                ]
                st.dataframe(
                    subset[show_cols].head(top_n).round(3),
                    use_container_width=True,
                    hide_index=True
                )
                if group == "Defender":
                    st.warning(
                        "Defender rankings here reflect recorded attacking output only. "
                        "Do not infer defensive quality from this table."
                    )

with tab_quality:
    st.subheader("Data quality audit")
    audit_rows = []
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            non_missing = int(s.notna().sum())
            nonzero = int(s.ne(0).fillna(False).sum())
            unique = int(s.nunique(dropna=True))
            if non_missing == 0:
                status = "All missing"
            elif nonzero == 0:
                status = "All zero / no variation"
            elif unique <= 1:
                status = "Constant"
            else:
                status = "Has variation"
            audit_rows.append({
                "Metric": col,
                "Non-missing": non_missing,
                "Non-zero": nonzero,
                "Unique values": unique,
                "Missing %": round(s.isna().mean() * 100, 1),
                "Status": status
            })

    audit = pd.DataFrame(audit_rows)
    if not audit.empty:
        st.dataframe(audit, use_container_width=True, hide_index=True)

    st.subheader("Goals with zero recorded xG")
    flagged = filtered[filtered["xg_review_flag"]].copy()
    if not flagged.empty:
        cols = [
            c for c in [
                "full_name", "Current Club", "position", "age",
                "minutes_played_overall", "goals_overall",
                "xg_total_overall", "goals_per90_calc"
            ] if c in flagged.columns
        ]
        st.dataframe(flagged[cols], use_container_width=True, hide_index=True)
        st.warning(
            "Verify these records against the source provider before drawing "
            "finishing or recruitment conclusions."
        )
    else:
        st.success("No goals-with-zero-xG records in the current filtered view.")

    st.markdown("""
    <div class="note">
    <b>Known limitations from the initial audit</b><br>
    Several shooting, defensive, rating, market-value and salary columns were
    all-zero in the supplied data. Zero-filled values are treated as unavailable
    evidence, not genuine performance or valuation. Assist and xA coverage is
    also sparse. Rankings are provisional after Matchweek 8.
    </div>
    """, unsafe_allow_html=True)

with tab_data:
    st.subheader("Filtered player records")
    st.caption("Use the sidebar filters, then download the resulting table.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered player data (CSV)",
        data=csv,
        file_name="ghana_pl_2026_27_matchweek8_scouting.csv",
        mime="text/csv"
    )

st.divider()
st.caption(
    "Reporting snapshot: after Matchweek 8. Rates are calculated from recorded "
    "totals and minutes. Rankings are provisional and should be revisited as the "
    "season progresses and data quality improves."
)
