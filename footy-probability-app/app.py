import streamlit as st
import os
from src.providers.football_data import FootballDataProvider
from src.providers.api_football import APIFootballProvider
from src.models.probability import predict_probabilities

# --- Page setup ---
st.set_page_config(page_title="⚽ Football Match Analyzer", layout="wide")
st.title("⚽ Football Match Analyzer with Probabilities")

# --- Load API Keys ---
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")

fd = FootballDataProvider(FD_API_KEY) if FD_API_KEY else None
api = APIFootballProvider(API_FOOTBALL_KEY) if API_FOOTBALL_KEY else None

# --- Sidebar ---
st.sidebar.header("🔍 Match Selector")
competition = st.sidebar.text_input("Competition ID (e.g. PL for Premier League):", "PL")
matchday = st.sidebar.number_input("Matchday", min_value=1, max_value=50, value=1)

if fd:
    fixtures = fd.get_fixtures(competition, matchday)
else:
    fixtures = [
        {"homeTeam": {"id": 1, "name": "Team A"},
         "awayTeam": {"id": 2, "name": "Team B"},
         "id": 100, "utcDate": "2025-08-20T19:00:00Z"}
    ]

fixture = st.sidebar.selectbox("Select Match", fixtures, format_func=lambda x: f"{x['homeTeam']['name']} vs {x['awayTeam']['name']}")

if fixture:
    home_team = fixture["homeTeam"]["name"]
    away_team = fixture["awayTeam"]["name"]

    st.markdown(
        f"### 🏟️ {home_team} vs {away_team}  \n"
        f"**Kickoff (UTC):** {fixture.get('utcDate','?')}"
    )

    # --- Fetch team data ---
    if api:
        home_stats = api.get_team_stats(fixture["homeTeam"]["id"], competition)
        away_stats = api.get_team_stats(fixture["awayTeam"]["id"], competition)
        h2h = api.get_head_to_head(fixture["homeTeam"]["id"], fixture["awayTeam"]["id"])
        injuries = api.get_injuries(fixture["homeTeam"]["id"], fixture["awayTeam"]["id"])
        cards = api.get_cards(fixture["homeTeam"]["id"], fixture["awayTeam"]["id"])
        top_scorers = api.get_top_scorers(competition)
    else:
        # Mock fallback
        home_stats = {"avg_goals_scored": 1.8, "avg_goals_conceded": 1.0, "home_form": "WDLWW"}
        away_stats = {"avg_goals_scored": 1.2, "avg_goals_conceded": 1.6, "away_form": "DLLWL"}
        h2h = {"home_wins": 3, "away_wins": 2, "draws": 1}
        injuries = [{"team": home_team, "player": "Player A", "type": "Hamstring"}]
        cards = [{"team": away_team, "player": "Player B", "cards": 5}]
        top_scorers = [{"player": "Star Striker", "team": home_team, "goals": 10}]

    # --- Show Analysis Panels ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Team Stats")
        st.write(f"**{home_team}**: {home_stats}")
        st.write(f"**{away_team}**: {away_stats}")

        st.subheader("🤝 Head-to-Head")
        st.write(h2h)

        st.subheader("⚽ Top Scorers")
        for scorer in top_scorers:
            st.write(f"{scorer['player']} ({scorer['team']}) - {scorer['goals']} goals")

    with col2:
        st.subheader("🩼 Injuries")
        for inj in injuries:
            st.write(f"{inj['player']} - {inj['type']} ({inj['team']})")

        st.subheader("🟨 Discipline")
        for card in cards:
            st.write(f"{card['player']} ({card['team']}) - {card['cards']} cards")

    # --- Probability Engine ---
    probabilities = predict_probabilities(
        home_stats=home_stats,
        away_stats=away_stats,
        h2h=h2h,
        injuries=injuries,
        cards=cards,
        top_scorers=top_scorers,
    )

    st.subheader("📈 Predicted Outcome")
    st.write(probabilities)
