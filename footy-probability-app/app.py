import streamlit as st
import requests
import pandas as pd
import math
import altair as alt

# --- Your Football-Data.org API key ---
API_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {"X-Auth-Token": API_KEY}
BASE_URL = "https://api.football-data.org/v4"

# --- Page setup ---
st.set_page_config(page_title="⚽ Football Dashboard", layout="wide")
st.title("⚽ Football-Data.org Match Analyzer with Probabilities")

# --- Sidebar ---
st.sidebar.header("🔍 Match Selector")
league_code = st.sidebar.text_input("League Code (e.g., PL = Premier League):", "PL")
season = st.sidebar.number_input("Season (year):", min_value=2000, max_value=2030, value=2024)

# --- Fetch fixtures ---
st.subheader("📅 Fixtures")
fixtures_url = f"{BASE_URL}/competitions/{league_code}/matches"
params = {"season": season}
fixtures_resp = requests.get(fixtures_url, headers=HEADERS, params=params)
fixtures_data = fixtures_resp.json()

if "matches" not in fixtures_data:
    st.error("❌ No fixtures found or invalid API key/league.")
else:
    matches = fixtures_data["matches"]
    st.success(f"✅ Found {len(matches)} matches.")

    # Build a selectbox
    fixture_options = [
        {
            "id": m["id"],
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "utc": m["utcDate"]
        }
        for m in matches
    ]

    fixture = st.sidebar.selectbox(
        "Select Match",
        fixture_options,
        format_func=lambda x: f"{x['home']} vs {x['away']}"
    )

    if fixture:
        st.markdown(f"### 🏟️ {fixture['home']} vs {fixture['away']}")
        st.markdown(f"**Kickoff (UTC):** {fixture['utc']}")

        home_name = fixture["home"]
        away_name = fixture["away"]

        # --- Simple Last 5 Matches Form ---
        def get_last_matches(team_name):
            team_matches = [
                m for m in matches if m["homeTeam"]["name"] == team_name or m["awayTeam"]["name"] == team_name
            ]
            team_matches = sorted(team_matches, key=lambda x: x["utcDate"], reverse=True)
            return team_matches[:5]

        def calculate_form(team_name):
            last5 = get_last_matches(team_name)
            score = 0
            for m in last5:
                if m["score"]["winner"] == "HOME_TEAM" and m["homeTeam"]["name"] == team_name:
                    score += 1
                elif m["score"]["winner"] == "AWAY_TEAM" and m["awayTeam"]["name"] == team_name:
                    score += 1
                elif m["score"]["winner"] == "DRAW":
                    score += 0.5
            return score / 5 if last5 else 0.5

        home_form = calculate_form(home_name)
        away_form = calculate_form(away_name)

        st.subheader("📊 Recent Form (Last 5 Matches)")
        st.markdown(f"**{home_name} Form Score:** {home_form:.2f} / 1.0")
        st.markdown(f"**{away_name} Form Score:** {away_form:.2f} / 1.0")

        # --- Simple Probability Model ---
        def predict_probabilities(home_form, away_form):
            score = home_form - away_form
            home_prob = 0.5 + score * 0.3
            away_prob = 0.5 - score * 0.3
            draw_prob = 0.25
            # Normalize
            total = home_prob + away_prob + draw_prob
            return {
                "Home Win": round(home_prob / total, 2),
                "Draw": round(draw_prob / total, 2),
                "Away Win": round(away_prob / total, 2)
            }

        probs = predict_probabilities(home_form, away_form)
        st.subheader("📈 Predicted Outcome Probabilities")
        st.json(probs)

        # --- Visualization ---
        df_probs = pd.DataFrame({"Outcome": list(probs.keys()), "Probability": list(probs.values())})
        chart = alt.Chart(df_probs).mark_bar(color="orange").encode(
            x=alt.X("Outcome", sort=None),
            y="Probability",
            tooltip=["Outcome", "Probability"]
        ).properties(width=500, height=300, title="Match Outcome Probabilities")
        st.altair_chart(chart, use_container_width=True)

        # --- Dynamic Prediction Summary ---
        st.subheader("⚡ Match Prediction Summary")
        max_outcome = max(probs, key=probs.get)
        max_value = probs[max_outcome]

        if max_outcome == "Home Win":
            color = "green"
            emoji = "🔥"
            team = home_name
        elif max_outcome == "Away Win":
            color = "red"
            emoji = "🔥"
            team = away_name
        else:
            color = "blue"
            emoji = "⚖️"
            team = "Draw"

        st.markdown(
            f"<h2 style='color:{color}'>{emoji} Most Likely Outcome: {max_outcome} ({team}) – {max_value*100:.0f}%</h2>",
            unsafe_allow_html=True
        )
