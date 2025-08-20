import streamlit as st
import requests
import pandas as pd
import math
import altair as alt

# --- API Key and Base URL ---
API_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {"X-Auth-Token": API_KEY}
BASE_URL = "https://api.football-data.org/v4/"

# --- Page Setup ---
st.set_page_config(page_title="⚽ Football Match Analyzer", layout="wide")
st.title("⚽ Football Match Analyzer with Probabilities & Dashboard")

# --- Sidebar: League & Season ---
st.sidebar.header("🔍 Match Selector")
league_id = st.sidebar.text_input("League ID (e.g., 2021 = Premier League):", "2021")
season_year = st.sidebar.number_input("Season Year:", min_value=2000, max_value=2030, value=2025)

# --- Fetch Fixtures (Next 5) ---
fixtures_resp = requests.get(
    f"{BASE_URL}competitions/{league_id}/matches?season={season_year}",
    headers=HEADERS
).json()

fixtures = fixtures_resp.get("matches", [])

if not fixtures:
    st.error("❌ No fixtures found. Please check league ID and season.")
else:
    # --- Build fixture options ---
    fixture_options = [
        {
            "id": f["id"],
            "home": f["homeTeam"]["name"],
            "away": f["awayTeam"]["name"],
            "utc": f["utcDate"]
        } for f in fixtures
    ]

    fixture = st.sidebar.selectbox(
        "Select Match",
        fixture_options,
        format_func=lambda x: f"{x['home']} vs {x['away']}"
    )

    if fixture:
        home_name = fixture['home']
        away_name = fixture['away']

        st.markdown(f"### 🏟️ {home_name} vs {away_name}")
        st.markdown(f"**Kickoff (UTC):** {fixture['utc']}")

        # --- Sample Stats (replace with real API stats if available) ---
        stats_home = {"Wins": 1, "Draws": 0, "Losses": 0, "Goals For": 4, "Goals Against": 2}
        stats_away = {"Wins": 0, "Draws": 0, "Losses": 1, "Goals For": 2, "Goals Against": 4}

        # --- Display Team Stats ---
        st.subheader("📊 Team Stats")
        stats_df = pd.DataFrame([
            {"Team": home_name, **stats_home},
            {"Team": away_name, **stats_away}
        ])
        st.table(stats_df)

        # --- Head-to-Head ---
        st.subheader("🤝 Head-to-Head (Last 5 Matches)")
        # Example: Replace with real H2H data
        h2h_matches = fixtures[:5]  # last 5 matches for demo
        h2h_list = []
        for m in h2h_matches:
            home_score = m["score"]["fullTime"]["home"] if m["score"]["fullTime"]["home"] is not None else "-"
            away_score = m["score"]["fullTime"]["away"] if m["score"]["fullTime"]["away"] is not None else "-"
            h2h_list.append({
                "Date": m["utcDate"][:10],
                "Home Team": m["homeTeam"]["name"],
                "Home Score": home_score,
                "Away Team": m["awayTeam"]["name"],
                "Away Score": away_score,
                "Winner": m["score"]["winner"] if m["score"]["winner"] else "-"
            })
        st.table(pd.DataFrame(h2h_list))

        # --- Top Scorers (Sample Data) ---
        st.subheader("⚽ Top Scorers (League)")
        top_scorers = [
            {"Player": "Antoine Semenyo", "Team": "AFC Bournemouth", "Goals": 2, "Assists": 0},
            {"Player": "Richarlison", "Team": "Tottenham Hotspur", "Goals": 2, "Assists": 0},
            {"Player": "Erling Haaland", "Team": "Manchester City", "Goals": 2, "Assists": 0},
        ]
        st.table(pd.DataFrame(top_scorers))

        # --- Predicted Outcome Probabilities ---
        st.subheader("📈 Predicted Outcome Probabilities")
        probs = {"Home Win": 0.4, "Draw": 0.2, "Away Win": 0.4}

        df_probs = pd.DataFrame({
            "Outcome": list(probs.keys()),
            "Probability": list(probs.values())
        })

        chart = alt.Chart(df_probs).mark_bar(color='orange').encode(
            x=alt.X("Outcome", sort=None),
            y=alt.Y("Probability", scale=alt.Scale(domain=[0,1])),
            tooltip=["Outcome", "Probability"]
        ).properties(width=500, height=300)
        st.altair_chart(chart, use_container_width=True)

        # --- Match Prediction Summary ---
        st.subheader("⚡ Match Prediction Summary")
        max_outcome = max(probs, key=probs.get)
        max_value = probs[max_outcome]
        emoji = "🔥" if max_outcome != "Draw" else "⚖️"
        team = home_name if max_outcome=="Home Win" else (away_name if max_outcome=="Away Win" else "Draw")
        color = "green" if max_outcome=="Home Win" else ("red" if max_outcome=="Away Win" else "blue")
        st.markdown(
            f"<h2 style='color:{color}'>{emoji} Most Likely Outcome: {max_outcome} ({team}) – {max_value*100:.0f}%</h2>",
            unsafe_allow_html=True
        )
