import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# Ghana Premier League 2026/27 — Matchweek 10 Scouting Dashboard
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