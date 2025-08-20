import streamlit as st
import pandas as pd
import altair as alt

# --- Team Stats ---
st.subheader("📊 Team Stats")
stats_df = pd.DataFrame([
    {"Team": home_name, **stats_home},
    {"Team": away_name, **stats_away}
])
st.table(stats_df)

# --- Head-to-Head ---
st.subheader("🤝 Head-to-Head (Last 5 Matches)")
h2h_list = []
for m in h2h_matches[:5]:
    home_score = m["score"]["fullTime"]["home"]
    away_score = m["score"]["fullTime"]["away"]
    h2h_list.append({
        "Date": m["utcDate"][:10],
        "Home Team": m["homeTeam"]["name"],
        "Home Score": home_score if home_score is not None else "-",
        "Away Team": m["awayTeam"]["name"],
        "Away Score": away_score if away_score is not None else "-",
        "Winner": m["score"]["winner"] if m["score"]["winner"] else "-"
    })
st.table(pd.DataFrame(h2h_list))

# --- Top Scorers ---
st.subheader("⚽ Top Scorers (League)")
scorers_list = []
for s in top_scorers[:10]:  # top 10 scorers
    scorers_list.append({
        "Player": s["player"]["name"],
        "Team": s["team"]["name"],
        "Goals": s["goals"],
        "Assists": s.get("assists") or 0
    })
st.table(pd.DataFrame(scorers_list))

# --- Outcome Probabilities ---
st.subheader("📈 Predicted Outcome Probabilities")
df_probs = pd.DataFrame({
    "Outcome": list(probs.keys()),
    "Probability": list(probs.values())
})
# Bar chart
chart = alt.Chart(df_probs).mark_bar(color='orange').encode(
    x=alt.X("Outcome", sort=None),
    y=alt.Y("Probability", scale=alt.Scale(domain=[0,1])),
    tooltip=["Outcome", "Probability"]
).properties(width=500, height=300)
st.altair_chart(chart, use_container_width=True)

# --- Summary ---
st.subheader("⚡ Match Prediction Summary")
max_outcome = max(probs, key=probs.get)
max_value = probs[max_outcome]
emoji = "🔥" if max_outcome != "Draw" else "⚖️"
team = home_name if max_outcome=="Home Win" else (away_name if max_outcome=="Away Win" else "Draw")
color = "green" if max_outcome=="Home Win" else ("red" if max_outcome=="Away Win" else "blue")
st.markdown(f"<h2 style='color:{color}'>{emoji} Most Likely Outcome: {max_outcome} ({team}) – {max_value*100:.0f}%</h2>", unsafe_allow_html=True)
