import streamlit as st
import requests
import pandas as pd
import math
import altair as alt

# --- API key ---
API_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {"X-Auth-Token": API_KEY}
BASE_URL = "https://api.football-data.org/v4"

# --- Page setup ---
st.set_page_config(page_title="⚽ Football Dashboard", layout="wide")
st.title("⚽ Football-Data.org Match Analyzer with Stats & Probabilities")

# --- Sidebar ---
st.sidebar.header("🔍 Match Selector")
league_code = st.sidebar.text_input("League Code (PL = Premier League):", "PL")
season = st.sidebar.number_input("Season:", min_value=2000, max_value=2030, value=2024)

# --- Fetch fixtures ---
fixtures_url = f"{BASE_URL}/competitions/{league_code}/matches"
params = {"season": season}
fixtures_resp = requests.get(fixtures_url, headers=HEADERS, params=params).json()

if "matches" not in fixtures_resp:
    st.error("❌ No fixtures found or invalid API key/league.")
else:
    matches = fixtures_resp["matches"]
    st.success(f"✅ Found {len(matches)} matches.")

    # --- Select match ---
    fixture_options = [
        {"id": m["id"], "home": m["homeTeam"]["name"], "away": m["awayTeam"]["name"], "utc": m["utcDate"]}
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

        # --- Last 5 matches (Form) ---
        def get_last_matches(team_name):
            team_matches = [
                m for m in matches if m["homeTeam"]["name"] == team_name or m["awayTeam"]["name"] == team_name
            ]
            return sorted(team_matches, key=lambda x: x["utcDate"], reverse=True)[:5]

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

        # --- Team Stats (Overall in League) ---
        def get_team_stats(team_name):
            team_matches = [
                m for m in matches if m["homeTeam"]["name"] == team_name or m["awayTeam"]["name"] == team_name
            ]
            wins, draws, losses, goals_for, goals_against = 0, 0, 0, 0, 0
            for m in team_matches:
                home, away = m["homeTeam"]["name"], m["awayTeam"]["name"]
                score_home, score_away = m["score"]["fullTime"]["home"], m["score"]["fullTime"]["away"]
                if score_home is None or score_away is None:
                    continue
                goals_for += score_home if home == team_name else score_away
                goals_against += score_away if home == team_name else score_home
                winner = m["score"]["winner"]
                if winner == "DRAW":
                    draws += 1
                elif winner == "HOME_TEAM" and home == team_name:
                    wins += 1
                elif winner == "AWAY_TEAM" and away == team_name:
                    wins += 1
                else:
                    losses += 1
            return {"Wins": wins, "Draws": draws, "Losses": losses, "Goals For": goals_for, "Goals Against": goals_against}

        st.subheader("📊 Team Stats")
        stats_home = get_team_stats(home_name)
        stats_away = get_team_stats(away_name)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{home_name}**")
            st.json(stats_home)
        with col2:
            st.markdown(f"**{away_name}**")
            st.json(stats_away)

        # --- Head-to-Head (last 5 matches) ---
        h2h_matches = [
            m for m in matches if 
            (m["homeTeam"]["name"] == home_name and m["awayTeam"]["name"] == away_name) or
            (m["homeTeam"]["name"] == away_name and m["awayTeam"]["name"] == home_name)
        ]
        st.subheader("🤝 Head-to-Head (Last 5 Matches)")
        st.json(sorted(h2h_matches, key=lambda x: x["utcDate"], reverse=True)[:5])

        # --- Top Scorers (League) ---
        st.subheader("⚽ Top Scorers (League)")
        scorers_resp = requests.get(f"{BASE_URL}/competitions/{league_code}/scorers", headers=HEADERS, params={"season": season}).json()
        top_scorers = scorers_resp.get("scorers", [])
        st.json(top_scorers)

        # --- Simple Probability Model ---
        def predict_probabilities(home_form, away_form):
            score = home_form - away_form
            home_prob = 0.5 + score * 0.3
            away_prob = 0.5 - score * 0.3
            draw_prob = 0.25
            total = home_prob + away_prob + draw_prob
            return {"Home Win": round(home_prob/total,2), "Draw": round(draw_prob/total,2), "Away Win": round(away_prob/total,2)}

        probs = predict_probabilities(home_form, away_form)
        st.subheader("📈 Predicted Outcome Probabilities")
        st.json(probs)

        # --- Visualization ---
        df_probs = pd.DataFrame({"Outcome": list(probs.keys()), "Probability": list(probs.values())})
        chart = alt.Chart(df_probs).mark_bar(color="orange").encode(
            x=alt.X("Outcome", sort=None),
            y="Probability",
            tooltip=["Outcome","Probability"]
        ).properties(width=500, height=300, title="Match Outcome Probabilities")
        st.altair_chart(chart, use_container_width=True)

        # --- Dynamic Prediction Summary ---
        st.subheader("⚡ Match Prediction Summary")
        max_outcome = max(probs, key=probs.get)
        max_value = probs[max_outcome]
        if max_outcome == "Home Win":
            color, emoji, team = "green", "🔥", home_name
        elif max_outcome == "Away Win":
            color, emoji, team = "red", "🔥", away_name
        else:
            color, emoji, team = "blue", "⚖️", "Draw"
        st.markdown(f"<h2 style='color:{color}'>{emoji} Most Likely Outcome: {max_outcome} ({team}) – {max_value*100:.0f}%</h2>", unsafe_allow_html=True)
