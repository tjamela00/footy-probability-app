import streamlit as st
import requests
import math
import pandas as pd
import altair as alt

# --- API-Football key ---
API_FOOTBALL_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io/"

# --- Page setup ---
st.set_page_config(page_title="⚽ Football Match Analyzer", layout="wide")
st.title("⚽ Football Match Analyzer with Probabilities & Dashboard")

# --- Sidebar ---
st.sidebar.header("🔍 Match Selector")
league_id = st.sidebar.text_input("League ID (e.g., 39 = Premier League):", "39")
season = st.sidebar.number_input("Season (year):", min_value=2000, max_value=2030, value=2024)

# --- Fetch fixtures (try upcoming first, then fallback to recent) ---
fixtures_resp = requests.get(
    f"{BASE_URL}fixtures?league={league_id}&season={season}&next=20",
    headers=HEADERS
).json()

fixtures = fixtures_resp.get("response", [])

if not fixtures:
    st.warning("⚠️ No upcoming fixtures found. Showing recent past matches instead...")
    fixtures_resp = requests.get(
        f"{BASE_URL}fixtures?league={league_id}&season={season}&last=20",
        headers=HEADERS
    ).json()
    fixtures = fixtures_resp.get("response", [])

# --- Check if fixtures exist ---
if not fixtures:
    st.error("❌ No fixtures found. Please try a different league or season.")
else:
    fixture_options = [
        {"id": f["fixture"]["id"],
         "home": f["teams"]["home"]["name"],
         "away": f["teams"]["away"]["name"],
         "home_id": f["teams"]["home"]["id"],
         "away_id": f["teams"]["away"]["id"],
         "utc": f["fixture"]["date"]}
        for f in fixtures
    ]

    fixture = st.sidebar.selectbox(
        "Select Match",
        fixture_options,
        format_func=lambda x: f"{x['home']} vs {x['away']}"
    )

    if fixture:
        st.markdown(f"### 🏟️ {fixture['home']} vs {fixture['away']}")
        st.markdown(f"**Kickoff (UTC):** {fixture['utc']}")

        home_id = fixture["home_id"]
        away_id = fixture["away_id"]

        # --- Fetch team stats ---
        def get_team_stats(team_id):
            url = f"{BASE_URL}teams/statistics?team={team_id}&league={league_id}&season={season}"
            r = requests.get(url, headers=HEADERS).json()
            data = r.get("response", {})
            data["team_id"] = team_id
            return data

        home_stats = get_team_stats(home_id)
        away_stats = get_team_stats(away_id)

        # --- Head-to-Head ---
        h2h_resp = requests.get(f"{BASE_URL}fixtures/headtohead?h2h={home_id}-{away_id}", headers=HEADERS).json()
        h2h = h2h_resp.get("response", [])

        # --- Injuries ---
        inj_home = requests.get(f"{BASE_URL}injuries?team={home_id}&season={season}", headers=HEADERS).json()
        inj_away = requests.get(f"{BASE_URL}injuries?team={away_id}&season={season}", headers=HEADERS).json()
        injuries = inj_home.get("response", []) + inj_away.get("response", [])

        # --- Cards ---
        cards = {"home": home_stats.get("cards", {}), "away": away_stats.get("cards", {})}

        # --- Top Scorers ---
        scorers_resp = requests.get(f"{BASE_URL}players/topscorers?league={league_id}&season={season}", headers=HEADERS).json()
        top_scorers = scorers_resp.get("response", [])

        # --- Last 5 Matches (Form) ---
        def get_last_matches(team_id, league_id, season, last=5):
            url = f"{BASE_URL}fixtures?team={team_id}&league={league_id}&season={season}&last={last}"
            r = requests.get(url, headers=HEADERS).json()
            matches = r.get("response", [])
            return matches

        def calculate_form(matches, team_id):
            score = 0
            for m in matches:
                winner = m["score"]["winner"]
                if winner == "Home" and m["teams"]["home"]["id"] == team_id:
                    score += 1
                elif winner == "Away" and m["teams"]["away"]["id"] == team_id:
                    score += 1
                elif winner == "Draw":
                    score += 0.5
            return score / len(matches) if matches else 0.5

        home_form_matches = get_last_matches(home_id, league_id, season, last=5)
        away_form_matches = get_last_matches(away_id, league_id, season, last=5)
        home_form = calculate_form(home_form_matches, home_id)
        away_form = calculate_form(away_form_matches, away_id)

        st.subheader("📊 Recent Form (Last 5 Matches)")
        st.markdown(f"**{fixture['home']} Form Score:** {home_form:.2f} / 1.0")
        st.markdown(f"**{fixture['away']} Form Score:** {away_form:.2f} / 1.0")

        # --- Show stats ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📊 {fixture['home']} Stats")
            st.json(home_stats)
            st.subheader("🤝 Head-to-Head")
            st.json(h2h)
            st.subheader("⚽ Top Scorers")
            st.json(top_scorers)
        with col2:
            st.subheader(f"🩼 Injuries")
            st.json(injuries)
            st.subheader("🟨 Discipline (Cards)")
            st.json(cards)

        # --- Advanced Probability Model ---
        def predict_probabilities(home_stats, away_stats, h2h=None, injuries=None, cards=None, top_scorers=None, home_form=0.5, away_form=0.5):
            home_goals_for = home_stats.get("goals", {}).get("for", {}).get("total", 1)
            home_goals_against = home_stats.get("goals", {}).get("against", {}).get("total", 1)
            away_goals_for = away_stats.get("goals", {}).get("for", {}).get("total", 1)
            away_goals_against = away_stats.get("goals", {}).get("against", {}).get("total", 1)
            home_strength = home_goals_for - home_goals_against
            away_strength = away_goals_for - away_goals_against
            score = home_strength - away_strength

            if h2h:
                home_wins = sum(1 for g in h2h if g["teams"]["home"]["id"]==home_stats["team_id"] and g["score"]["winner"]=="Home")
                away_wins = sum(1 for g in h2h if g["teams"]["away"]["id"]==away_stats["team_id"] and g["score"]["winner"]=="Away")
                score += (home_wins - away_wins) * 0.1

            home_inj = len([i for i in injuries if i["team"]["id"]==home_stats["team_id"]])
            away_inj = len([i for i in injuries if i["team"]["id"]==away_stats["team_id"]])
            score += (away_inj - home_inj) * 0.05

            home_cards = cards.get("home", {}).get("yellow", 0) + cards.get("home", {}).get("red", 0)
            away_cards = cards.get("away", {}).get("yellow", 0) + cards.get("away", {}).get("red", 0)
            score += (away_cards - home_cards) * 0.02

            for s in top_scorers:
                if s["statistics"][0]["team"]["id"] == home_stats["team_id"]:
                    score += 0.05
                elif s["statistics"][0]["team"]["id"] == away_stats["team_id"]:
                    score -= 0.05

            score += (home_form - away_form) * 0.3

            home_prob = 1 / (1 + math.exp(-score))
            away_prob = 1 - home_prob
            draw_prob = 0.25
            total = home_prob + away_prob + draw_prob
            return {
                "Home Win": round(home_prob/total, 2),
                "Draw": round(draw_prob/total, 2),
                "Away Win": round(away_prob/total, 2)
            }

        probs = predict_probabilities(home_stats, away_stats, h2h, injuries, cards, top_scorers, home_form, away_form)

        # --- Probabilities Panel ---
        st.subheader("📈 Predicted Outcome Probabilities")
        st.json(probs)

        # --- Visualization ---
        df_probs = pd.DataFrame({
            "Outcome": list(probs.keys()),
            "Probability": list(probs.values())
        })

        chart = alt.Chart(df_probs).mark_bar(color='orange').encode(
            x=alt.X("Outcome", sort=None),
            y="Probability",
            tooltip=["Outcome","Probability"]
        ).properties(
            width=500,
            height=300,
            title="Match Outcome Probabilities"
        )
        st.altair_chart(chart, use_container_width=True)

        # --- Dynamic Prediction Summary ---
        st.subheader("⚡ Match Prediction Summary")
        max_outcome = max(probs, key=probs.get)
        max_value = probs[max_outcome]

        if max_outcome == "Home Win":
            color = "green"
            emoji = "🔥"
            team = fixture["home"]
        elif max_outcome == "Away Win":
            color = "red"
            emoji = "🔥"
            team = fixture["away"]
        else:
            color = "blue"
            emoji = "⚖️"
            team = "Draw"

        st.markdown(f"<h2 style='color:{color}'>{emoji} Most Likely Outcome: {max_outcome} ({team}) – {max_value*100:.0f}%</h2>", unsafe_allow_html=True)

