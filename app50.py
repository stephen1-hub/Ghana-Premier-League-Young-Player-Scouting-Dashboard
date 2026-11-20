from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="GPL 2026/27 | Scouting Dashboard", page_icon="⚽", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "ghana-ghana-premier-league-players-2026-to-2027-stats.csv"

st.title("⚽ Ghana Premier League 2026/27")
st.subheader("Young Player Scouting Dashboard")
st.caption("Provisional player-statistics snapshot. Check data quality before drawing scouting conclusions.")

@st.cache_data
def load_data(file_bytes):
    from io import BytesIO
    data = pd.read_csv(BytesIO(file_bytes))
    data.columns = data.columns.str.strip()
    if "full_name" not in data.columns:
        raise ValueError("CSV is missing the required 'full_name' column.")
    data["full_name"] = data["full_name"].astype("string").str.strip()
    data = data[data["full_name"].notna() & data["full_name"].ne("")].copy()

    numeric = ["age", "minutes_played_overall", "goals_overall", "assists_overall", "xg_total_overall"]
    for col in numeric:
        if col not in data.columns:
            data[col] = np.nan
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["goals_overall"] = data["goals_overall"].fillna(0)
    mins = data["minutes_played_overall"]
    data["goals_per90_calc"] = np.where(mins.gt(0), data["goals_overall"] / mins * 90, np.nan)
    data["xG status"] = np.select(
        [data["goals_overall"].gt(0) & data["xg_total_overall"].isna(),
         data["goals_overall"].gt(0) & data["xg_total_overall"].eq(0)],
        ["Verify: missing xG", "Verify: zero xG"],
        default="No xG flag"
    )
    pos = data.get("position", pd.Series("", index=data.index)).fillna("").astype(str).str.lower()
    data["scouting_group"] = np.select(
        [pos.str.contains("goalkeeper|goal keeper|\b gk \b", regex=True),
         pos.str.contains("defen|back|\b cb \b|\b rb \b|\b lb \b", regex=True),
         pos.str.contains("midfield|wing|\b am \b|\b dm \b|\b cm \b", regex=True),
         pos.str.contains("forward|striker|attack|\b st \b|\b cf \b", regex=True)],
        ["Goalkeeper", "Defender", "Midfielder", "Forward"],
        default="Other"
    )
    return data

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE.name}. Keep the CSV beside app50.py in the repository.")
    st.stop()

try:
    df = load_data(DATA_FILE.read_bytes())
except Exception as exc:
    st.error(f"Could not load the player dataset: {exc}")
    st.stop()

with st.sidebar:
    st.header("Scouting filters")
    young_only = st.checkbox("Young-player focus (age ≤ 23)", value=True)
    age_values = df["age"].dropna()
    min_age = int(age_values.min()) if not age_values.empty else 16
    max_age = int(age_values.max()) if not age_values.empty else 45
    age_range = st.slider("Age range", min_value=min_age, max_value=max_age,
                          value=(min_age, min(max_age, 23) if young_only else max_age))
    min_minutes = st.number_input("Minimum minutes (filtered views)", min_value=0, value=450, step=90)
    group_options = ["All positions"] + sorted(df["scouting_group"].unique().tolist())
    chosen_group = st.selectbox("Position group", group_options)
    clubs = sorted(df["Current Club"].dropna().astype(str).unique()) if "Current Club" in df else []
    chosen_clubs = st.multiselect("Club (optional)", clubs)

filtered = df.copy()
filtered = filtered[filtered["age"].between(age_range[0], age_range[1])]
if young_only:
    filtered = filtered[filtered["age"].le(23)]
filtered = filtered[filtered["minutes_played_overall"].ge(min_minutes)]
if chosen_group != "All positions":
    filtered = filtered[filtered["scouting_group"].eq(chosen_group)]
if chosen_clubs and "Current Club" in filtered:
    filtered = filtered[filtered["Current Club"].astype(str).isin(chosen_clubs)]

scorers_all = df[df["goals_overall"].gt(0)].copy()
scorers_all = scorers_all.sort_values(["goals_per90_calc", "goals_overall"], ascending=False, na_position="last")

c1, c2, c3 = st.columns(3)
c1.metric("Named player records", f"{len(df):,}")
c2.metric("Goalscorers in full dataset", f"{len(scorers_all):,}")
c3.metric("Recorded goals", f"{int(df['goals_overall'].sum()):,}")

overview, scorer_tab, data_tab = st.tabs(["Overview", "All goalscorers", "Player data"])
with overview:
    st.subheader("Filtered scouting pool")
    st.caption(f"{len(filtered):,} records match the sidebar filters.")
    if not filtered.empty:
        if "scouting_group" in filtered:
            counts = filtered["scouting_group"].value_counts().rename_axis("Position group").reset_index(name="Players")
            st.plotly_chart(px.bar(counts, x="Position group", y="Players", color="Position group"), use_container_width=True)
        rate_data = filtered[filtered["goals_per90_calc"].notna()]
        if not rate_data.empty:
            st.plotly_chart(px.scatter(rate_data, x="age", y="goals_per90_calc", color="scouting_group",
                                       hover_name="full_name", hover_data=["Current Club", "goals_overall", "minutes_played_overall"]),
                            use_container_width=True)
    else:
        st.info("No records match these filters.")

with scorer_tab:
    st.subheader("Every recorded goalscorer")
    st.caption("This table is intentionally independent of age, minutes, position, club, and xG filters. Every named player with at least one recorded goal is included. Missing or zero xG is flagged, not used to exclude a player.")
    show_cols = [c for c in ["full_name", "Current Club", "position", "age", "goals_overall",
                              "minutes_played_overall", "goals_per90_calc", "assists_overall",
                              "xg_total_overall", "xG status"] if c in scorers_all.columns]
    st.dataframe(scorers_all[show_cols], use_container_width=True, hide_index=True)
    st.download_button("Download all goalscorers (CSV)", scorers_all[show_cols].to_csv(index=False).encode("utf-8"),
                       file_name="ghana_pl_all_goalscorers.csv", mime="text/csv")

with data_tab:
    st.subheader("Filtered player records")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download filtered records (CSV)", filtered.to_csv(index=False).encode("utf-8"),
                       file_name="ghana_pl_filtered_players.csv", mime="text/csv")

st.divider()
st.caption("Goals per 90 is calculated only when minutes are positive. Rankings are descriptive, provisional, and depend on the accuracy of the supplied statistics.")
