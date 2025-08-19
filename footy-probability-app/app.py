import os, json
import streamlit as st
from dotenv import load_dotenv

from src.providers.football_data import FootballDataProvider
from src.providers.api_football import APIFootballProvider
from src.models.probability import predict_probabilities

load_dotenv()

st.set_page_config(page_title="⚽ Match Probability", layout="wide")
st.title("⚽ Soccer Match Probability (Form • Cards • Injuries)")

st.markdown("""
This app compiles form, standings, discipline and injury indicators to estimate the **probability of Home/Draw/Away**.
- Works in **Demo Mode** with mock data
- Add API keys in `.env` for real data:
  - `FOOTBALL_DATA_TOKEN` (Football-Data.org)
  - `API_FOOTBALL_KEY` (API-Football via RapidAPI)
""")
with st.expander("⚙️ Settings", expanded=False):
    demo_mode = st.checkbox("Run in Demo Mode (use mock data)", value=(os.getenv("FOOTBALL_DATA_TOKEN") is None and os.getenv("API_FOOTBALL_KEY") is None))
    home_adv = st.slider("Home-field advantage (model)", 0.0, 0.6, 0.25, 0.01)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Match Selection")
    match_id = st.text_input("Match ID", value="demo" if demo_mode else "")
    provider_choice = st.selectbox("Primary Provider", ["Auto", "Football-Data.org", "API-Football"])

with col2:
    st.subheader("Optional Inputs (override)")
    home_pos = st.number_input("Home league position (1=best)", min_value=1, max_value=24, value=None, placeholder="auto")
    away_pos = st.number_input("Away league position (1=best)", min_value=1, max_value=24, value=None, placeholder="auto")

def load_demo():
    with open("src/demo/mock_payloads.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    return d

def get_providers():
    fd = FootballDataProvider()
    af = APIFootballProvider()
    return fd, af

def infer(provider, match_id):
    if match_id == "demo":
        return load_demo()
    ctx = provider.get_match_context(match_id)
    # try to infer standings via provider if possible (competition id/code must be known by user)
    return ctx

if demo_mode or match_id == "demo":
    data = load_demo()
else:
    fd, af = get_providers()
    primary = provider_choice
    use = None
    if primary == "Football-Data.org":
        use = fd
    elif primary == "API-Football":
        use = af
    else:
        use = fd if os.getenv("FOOTBALL_DATA_TOKEN") else af

    ctx = infer(use, match_id)
    if not ctx:
        st.error("Could not fetch match context. Check Match ID or provider choice.")
        st.stop()

    # Fetch forms
    home_form = use.get_recent_form(ctx["home_team_id"]).get("last5", [])
    away_form = use.get_recent_form(ctx["away_team_id"]).get("last5", [])
    # Positions (if competition known)
    hpos = None
    apos = None
    if ctx.get("competition"):
        hpos = use.get_standings_position(ctx["competition"], ctx["home_team_id"])
        apos = use.get_standings_position(ctx["competition"], ctx["away_team_id"])

    # Optional enrichers from API-Football if available
    cards_home = cards_away = None
    inj_h = inj_a = 0
    if os.getenv("API_FOOTBALL_KEY"):
        try:
            cards_home_d = af.get_team_cards(ctx["home_team_id"])
            cards_away_d = af.get_team_cards(ctx["away_team_id"])
            if cards_home_d:
                cards_home = (cards_home_d.get("yellow_per_match", 0.0), cards_home_d.get("red_per_match", 0.0))
            if cards_away_d:
                cards_away = (cards_away_d.get("yellow_per_match", 0.0), cards_away_d.get("red_per_match", 0.0))
            inj_home_d = af.get_injuries(ctx["home_team_id"])
            inj_away_d = af.get_injuries(ctx["away_team_id"])
            if inj_home_d:
                inj_h = inj_home_d.get("key_starters_out", 0)
            if inj_away_d:
                inj_a = inj_away_d.get("key_starters_out", 0)
        except Exception as e:
            st.warning(f"API-Football enrichers unavailable: {e}")

    data = {
        "match_context": ctx,
        "home_form": home_form or ["D","D","D","D","D"],
        "away_form": away_form or ["D","D","D","D","D"],
        "home_cards": cards_home,
        "away_cards": cards_away,
        "home_inj_starters": inj_h,
        "away_inj_starters": inj_a,
    }

ctx = data["match_context"]
home_form = data["home_form"]
away_form = data["away_form"]
home_cards = tuple(data.get("home_cards")) if data.get("home_cards") else None
away_cards = tuple(data.get("away_cards")) if data.get("away_cards") else None
home_inj = data.get("home_inj_starters", 0)
away_inj = data.get("away_inj_starters", 0)

# Allow override positions from UI
if home_pos:
    ctx["home_position"] = int(home_pos)
if away_pos:
    ctx["away_position"] = int(away_pos)

st.markdown(f"**Match:** {ctx.get('home_team_name','?')} vs {ctx.get('away_team_name','?')}  
"
            f"**Competition:** {ctx.get('competition','?')} • **Kickoff (UTC):** {ctx.get('utc_kickoff','?')}")

colA, colB = st.columns(2)
with colA:
    st.write("### Home team recent form")
    st.write(" ".join(home_form) if home_form else "n/a")
with colB:
    st.write("### Away team recent form")
    st.write(" ".join(away_form) if away_form else "n/a")

with st.expander("🔎 Inputs used"):
    st.json({
        "positions": {"home": ctx.get("home_position"), "away": ctx.get("away_position")},
        "cards": {"home": home_cards, "away": away_cards},
        "injuries": {"home": home_inj, "away": away_inj},
        "home_advantage": home_adv,
    })

res = predict_probabilities(
    home_form=home_form,
    away_form=away_form,
    home_pos=ctx.get("home_position"),
    away_pos=ctx.get("away_position"),
    home_cards=home_cards,
    away_cards=away_cards,
    home_inj_starters=home_inj,
    away_inj_starters=away_inj,
    home_advantage=home_adv
)

st.success("Estimated probabilities")
st.metric("Home win", f"{res['home_win']*100:.1f}%")
st.metric("Draw", f"{res['draw']*100:.1f}%")
st.metric("Away win", f"{res['away_win']*100:.1f}%")

with st.expander("🧠 Why these numbers?"):
    st.write("The model blends recent form and a league-position anchor, then adjusts for discipline and injuries. Values are converted to probabilities via a softmax with a draw prior.")
    st.json(res["explain"])

st.caption("Educational use only. No guarantee of accuracy.")
