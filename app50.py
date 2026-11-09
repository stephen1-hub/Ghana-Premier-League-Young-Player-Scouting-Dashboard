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
        scatter = filtered[
            filtered["goals_per90_calc"].notna()
            & filtered["age"].notna()
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
        "Players with recorded goals and minutes remain eligible, including those "
        "whose xG is zero or missing. xG concerns are flagged separately in the "
        "Data quality tab and in the leaderboard status column."
    )
    leaders = filtered[
        filtered["scouting_group"].isin(["Forward", "Midfielder", "Defender"])
        & filtered["goals_per90_calc"].notna()
        & filtered["goals_overall"].gt(0)
    ].sort_values(
        ["goals_per90_calc", "goals_overall"],
        ascending=False
    ).head(top_n).copy()

    if not leaders.empty:
        leaders["player_club"] = (
            leaders["full_name"] + " — " + leaders["Current Club"].astype(str)
        )
        leaders["xG status"] = np.select(
            [
                leaders["xg_review_flag"].fillna(False).to_numpy(dtype=bool),
                leaders["xg_missing_flag"].fillna(False).to_numpy(dtype=bool),
            ],
            ["Verify: zero xG", "Verify: missing xG"],
            default="No xG flag"
        )
        fig = px.bar(
            leaders.sort_values("goals_per90_calc"),
            x="goals_per90_calc",
            y="player_club",
            orientation="h",
            color="scouting_group",
            hover_data=[
                "position", "age", "minutes_played_overall",
                "goals_overall", "assists_overall", "xg_total_overall", "xG status"
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
