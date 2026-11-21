from pathlib import Path
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="GPL 2026/27 | Player Scouting", page_icon="⚽", layout="wide")

DATA_FILE = Path(__file__).resolve().parent / "ghana-ghana-premier-league-players-2026-to-2027-stats.csv"

st.markdown("""
<style>
:root { --gpl-green:#1B7F4F; }
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
h1, h2, h3 {letter-spacing:-.025em;}
.dashboard-kicker {color:#1B7F4F; font-size:.78rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.35rem;}
.dashboard-sub {color: #66756D; font-size:1rem; margin-top:-.35rem; margin-bottom:1.4rem;}
.hero-card {border:1px solid rgba(128,145,135,.28); border-radius:16px; padding:1.35rem 1.5rem; margin:.6rem 0 1.2rem; background:linear-gradient(120deg, rgba(27,127,79,.10), rgba(27,127,79,.025));}
.hero-label {font-size:.8rem; font-weight:700; color:#66756D; text-transform:uppercase; letter-spacing:.08em;}
.hero-number {font-size:clamp(2.1rem,5vw,3.8rem); font-weight:850; line-height:1.1; color:#1B7F4F; margin:.25rem 0 .5rem;}
.insight-card {border:1px solid rgba(128,145,135,.25); border-left:4px solid #1B7F4F; border-radius:0 12px 12px 0; padding:.85rem 1rem; min-height:115px; margin-bottom:.6rem;}
.insight-card h4 {margin:0 0 .35rem; font-size:1rem;}
.insight-card p {margin:0; font-size:.9rem; color:#66756D;}
.section-note {color:#66756D; font-size:.88rem; margin-top:-.45rem;}
div[data-testid="stMetric"] {border:1px solid rgba(128,145,135,.25); border-radius:12px; padding:1rem 1.1rem; background:rgba(128,145,135,.045);}
div[data-testid="stMetric"] label {font-size:.8rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_bytes):
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
        ["Verify: missing xG", "Verify: zero xG"], default="No xG flag")
    pos = data.get("position", pd.Series("", index=data.index)).fillna("").astype(str).str.lower()
    data["scouting_group"] = np.select(
        [pos.str.contains(r"goalkeeper|goal keeper|\bgk\b", regex=True),
         pos.str.contains(r"defen|back|\bcb\b|\brb\b|\blb\b", regex=True),
         pos.str.contains(r"midfield|wing|\bam\b|\bdm\b|\bcm\b", regex=True),
         pos.str.contains(r"forward|striker|attack|\bst\b|\bcf\b", regex=True)],
        ["Goalkeeper", "Defender", "Midfielder", "Forward"], default="Other")
    return data

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE.name}. Keep the CSV beside app50.py in the repository.")
    st.stop()
try:
    df = load_data(DATA_FILE.read_bytes())
except Exception as exc:
    st.error(f"Could not load the player dataset: {exc}")
    st.stop()

st.markdown('<div class="dashboard-kicker">The Football Data Room · Scouting brief</div>', unsafe_allow_html=True)
st.title("Ghana Premier League 2026/27")
st.markdown('<div class="dashboard-sub">Young-player scouting dashboard · an early-season view of player output, minutes and age.</div>', unsafe_allow_html=True)
st.caption("Early-season snapshot · clubs have played 5–10 matches. Figures are provisional and depend on the supplied player data.")

with st.sidebar:
    st.header("Scouting filters")
    young_only = st.checkbox("Young-player focus (age ≤ 23)", value=True)
    ages = df["age"].dropna()
    min_age = int(ages.min()) if not ages.empty else 16
    max_age = int(ages.max()) if not ages.empty else 45
    age_range = st.slider("Age range", min_value=min_age, max_value=max_age,
                          value=(min_age, min(max_age, 23) if young_only else max_age))
    min_minutes = st.number_input("Minimum minutes", min_value=0, value=450, step=90)
    groups = ["All positions"] + sorted(df["scouting_group"].dropna().unique().tolist())
    chosen_group = st.selectbox("Position group", groups)
    clubs = sorted(df["Current Club"].dropna().astype(str).unique()) if "Current Club" in df else []
    chosen_clubs = st.multiselect("Club", clubs)

filtered = df[df["age"].between(age_range[0], age_range[1])].copy()
if young_only:
    filtered = filtered[filtered["age"].le(23)]
filtered = filtered[filtered["minutes_played_overall"].ge(min_minutes)]
if chosen_group != "All positions":
    filtered = filtered[filtered["scouting_group"].eq(chosen_group)]
if chosen_clubs and "Current Club" in filtered:
    filtered = filtered[filtered["Current Club"].astype(str).isin(chosen_clubs)]

scorers = df[df["goals_overall"].gt(0)].copy()
scorers = scorers.sort_values(["goals_overall", "goals_per90_calc"], ascending=False, na_position="last")
top = scorers.iloc[0] if not scorers.empty else None
total_goals = int(df["goals_overall"].sum())
club_count = df["Current Club"].nunique() if "Current Club" in df else 0
active = int(df["minutes_played_overall"].fillna(0).gt(0).sum())

if top is not None:
    top_club = str(top.get("Current Club", "Club not recorded"))
    top_rate = f"{top['goals_per90_calc']:.2f} goals/90" if pd.notna(top["goals_per90_calc"]) else "rate unavailable"
    st.markdown(f'<section class="hero-card"><div class="hero-label">Leading scorer in the current dataset</div><div class="hero-number">{int(top["goals_overall"])} goals · {top["full_name"]}</div><div>{top_club} &nbsp;·&nbsp; {top_rate}</div></section>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Named player records", f"{len(df):,}")
m2.metric("Players with minutes", f"{active:,}")
m3.metric("Recorded goals", f"{total_goals:,}")
m4.metric("Clubs represented", f"{club_count:,}")

st.subheader("What stands out")
insights = []
if not scorers.empty:
    one_goal = int(scorers["goals_overall"].eq(1).sum())
    insights.append(("Scoring is concentrated", f"{len(scorers)} players have scored; {one_goal} have exactly one goal."))
if "scouting_group" in df:
    pos_goals = df.groupby("scouting_group")["goals_overall"].sum().sort_values(ascending=False)
    if not pos_goals.empty:
        leader = pos_goals.index[0]
        insights.append(("Position-group output", f"{leader}s account for {int(pos_goals.iloc[0])} recorded goals in this dataset."))
if not filtered.empty and filtered["age"].notna().any():
    insights.append(("Filtered scouting pool", f"{len(filtered):,} players meet the current sidebar criteria; median age is {filtered['age'].median():.1f}."))
if not scorers.empty and scorers["goals_per90_calc"].notna().any():
    efficient = scorers.loc[scorers["goals_per90_calc"].idxmax()]
    insights.append(("Rate leader", f"{efficient['full_name']} has the highest calculated goals-per-90 among scorers with recorded minutes ({efficient['goals_per90_calc']:.2f})."))
cols = st.columns(2)
for i, (heading, body) in enumerate(insights[:4]):
    with cols[i % 2]:
        st.markdown(f'<div class="insight-card"><h4>{heading}</h4><p>{body}</p></div>', unsafe_allow_html=True)

st.subheader("Explore the numbers")
st.markdown('<div class="section-note">All charts and the player table below respond to the sidebar filters. Clear filters to return to the full dataset.</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    club_goals = df.groupby("Current Club", dropna=True)["goals_overall"].sum().sort_values(ascending=False).head(18).reset_index()
    if not club_goals.empty:
        fig = px.bar(club_goals.sort_values("goals_overall"), x="goals_overall", y="Current Club", orientation="h",
                     labels={"goals_overall":"Goals","Current Club":"Club"}, title="Goals by club · full dataset")
        fig.update_layout(height=430, margin=dict(l=8,r=8,t=55,b=8), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
with right:
    pos = filtered.groupby("scouting_group", dropna=True).agg(Goals=("goals_overall","sum"), Players=("full_name","nunique")).reset_index()
    if not pos.empty:
        fig = px.bar(pos, x="scouting_group", y="Goals", color="scouting_group",
                     labels={"scouting_group":"Position group"}, title="Goals by position group")
        fig.update_layout(height=430, margin=dict(l=8,r=8,t=55,b=8), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    age_df = filtered.dropna(subset=["age"]).copy()
    age_df["Age band"] = pd.cut(age_df["age"], bins=[0,18,21,24,28,100], labels=["≤18","19–21","22–24","25–28","29+"], right=True)
    age_summary = age_df.groupby("Age band", observed=False).agg(Players=("full_name","nunique"), Goals=("goals_overall","sum")).reset_index()
    if not age_summary.empty:
        fig = px.bar(age_summary, x="Age band", y=["Players","Goals"], barmode="group", title="Player count and goals by age band")
        fig.update_layout(height=360, margin=dict(l=8,r=8,t=55,b=8))
        st.plotly_chart(fig, use_container_width=True)
with right:
    if not filtered.empty:
        rate = filtered[filtered["goals_per90_calc"].notna()]
        if not rate.empty:
            fig = px.scatter(rate, x="age", y="goals_per90_calc", color="scouting_group",
                             hover_name="full_name", hover_data=[c for c in ["Current Club","goals_overall","minutes_played_overall"] if c in rate.columns],
                             labels={"age":"Age","goals_per90_calc":"Goals per 90"}, title="Filtered players · age vs goals/90")
            fig.update_layout(height=360, margin=dict(l=8,r=8,t=55,b=8))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No filtered players have positive minutes for a goals-per-90 comparison.")
    else:
        st.info("No records match the current filters.")

st.subheader("Scorer table")
st.caption("Full-dataset goalscorers, ranked by goals then goals per 90. This table is independent of sidebar age, minutes, position and club filters; use the search and club controls below to narrow it.")
search = st.text_input("Search player or club", placeholder="Type a name or club")
club_filter = st.selectbox("Scorer club", ["All clubs"] + clubs)
scorer_view = scorers.copy()
if search:
    mask = scorer_view["full_name"].str.contains(search, case=False, na=False)
    if "Current Club" in scorer_view:
        mask |= scorer_view["Current Club"].astype(str).str.contains(search, case=False, na=False)
    scorer_view = scorer_view[mask]
if club_filter != "All clubs" and "Current Club" in scorer_view:
    scorer_view = scorer_view[scorer_view["Current Club"].astype(str).eq(club_filter)]
show_cols = [c for c in ["full_name","Current Club","position","age","minutes_played_overall","goals_overall","assists_overall","goals_per90_calc","xg_total_overall","xG status"] if c in scorer_view.columns]
st.dataframe(scorer_view[show_cols], use_container_width=True, hide_index=True)
st.download_button("Download goalscorers (CSV)", scorer_view[show_cols].to_csv(index=False).encode("utf-8"),
                   file_name="ghana_pl_goalscorers.csv", mime="text/csv")

with st.expander("Data notes and limitations"):
    st.markdown("""
    - Goals per 90 is calculated only when minutes played are positive.
    - The early-season coverage is uneven across clubs; comparisons are descriptive, not final rankings.
    - Missing or zero xG is flagged for verification and is not used to exclude players.
    - Check source completeness and player identity before using the dashboard for recruitment decisions.
    """)
st.caption("Ghana Premier League 2026/27 · Player scouting snapshot")
