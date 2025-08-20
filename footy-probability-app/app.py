import streamlit as st
import requests

# --- Your Football-Data.org API key ---
API_KEY = "YOUR_FOOTBALL_DATA_KEY_HERE"
HEADERS = {
    "X-Auth-Token": API_KEY   # ✅ correct header for football-data.org
}
BASE_URL = "https://api.football-data.org/v4"

st.set_page_config(page_title="⚽ Football-Data.org API Test", layout="wide")
st.title("⚽ Football-Data.org Key Test")

# --- 1) Test Competitions Endpoint ---
st.subheader("🔎 Step 1: Check Competitions")
url_comp = f"{BASE_URL}/competitions"
resp_comp = requests.get(url_comp, headers=HEADERS)

if resp_comp.status_code == 200:
    st.success("✅ Connected to Football-Data.org!")
    st.json(resp_comp.json())
else:
    st.error(f"❌ Failed (HTTP {resp_comp.status_code})")
    st.text(resp_comp.text)

# --- 2) Test Fixtures (Matches) for EPL ---
st.subheader("🔎 Step 2: Check EPL Matches")
league_code = "PL"   # Premier League
url_matches = f"{BASE_URL}/competitions/{league_code}/matches"
params = {"season": 2024}
resp_matches = requests.get(url_matches, headers=HEADERS, params=params)

if resp_matches.status_code == 200:
    st.success("✅ Fixtures retrieved successfully!")
    st.json(resp_matches.json())
else:
    st.error(f"❌ Failed (HTTP {resp_matches.status_code})")
    st.text(resp_matches.text)
