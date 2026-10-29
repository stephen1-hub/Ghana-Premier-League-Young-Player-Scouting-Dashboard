# Ghana-Premier-League-Young-Player-Scouting-Dashboard

A Python and Streamlit scouting dashboard for exploring recorded player output in the Ghana Premier League 2026/27 season. The current analysis is a provisional snapshot after Matchweek 8, not a final-season ranking.
# Purpose
The dashboard is designed to help scouts and football analytics teams screen emerging players, compare recorded attacking output, and inspect data quality before making recruitment judgements.
# Dashboard features
- Filter players by age, minutes played, position group, and club.
- Review squad/scouting-pool summary metrics.
- Compare recorded goals-per-90 output.
- Explore player tables by position group.
- Inspect missing, constant, and zero-filled metrics.
- Flag goals recorded alongside zero expected goals (xG) for source verification.
- Export the filtered player table to CSV.
# Tools
- Python
- Pandas and NumPy
- Plotly
- Streamlit
# Important analytical limitations
- This is an early-season snapshot after Matchweek 8. Rankings may change as more matches are played.
- Goals per 90 measures recorded attacking output; it is not a complete player-quality score.
- Some source metrics may be missing, constant, or zero-filled. Such values should not automatically be interpreted as genuine performance values.
- Goals with zero recorded xG are flagged for review, not assumed to be invalid.
- Goalkeeper performance cannot be ranked meaningfully using goals per 90.
- Findings should be checked against the source provider and additional match/video evidence before recruitment decisions.
# Run locally
1. Install Python
Use a supported Python 3 version installed on your computer.
2. Get the code
Clone the repository or download the source files.
3. Install dependencies
python -m pip install -r requirements.txt
4. Add the dataset locally
Place the authorised player-statistics CSV beside app50.py using this filename:
ghana-ghana-premier-league-players-2026-to-2027-stats.csv
Dataset licensing: Do not commit or publish the raw CSV unless you have permission to redistribute it. The code can be shared separately from a restricted dataset. If you do not have redistribution rights, keep the CSV local and document the source and access conditions instead.
5. Launch the app
python -m streamlit run app50.py
Streamlit will print a local URL, commonly http://localhost:8501.
# Repository structure
ghana-pl-scouting/
├── app50.py
├── requirements.txt
├── README.md
├── .gitignore
└── screenshots/
    └── dashboard-overview.png
The screenshot is optional. Add it after capturing the dashboard with real data loaded.
# Next improvements
- Preserve dated matchweek snapshots to analyse player development over time.
- Add position-specific indicators once the source provides reliable coverage.
- Add minutes and sample-size context to player comparisons.
- Add a methodology note and validated scouting case studies.
- Deploy a public demo only after resolving dataset access and deployment requirements.
# Author
Stephen Yaw Ayamah
Football analytics portfolio — Ghana Premier League scouting
