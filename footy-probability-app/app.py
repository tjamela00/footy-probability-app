import streamlit as st
import requests

# --- API-Football key ---
API_FOOTBALL_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY,
    "Accept": "application/json"
}
BASE_URL = "https://v3.football.api-sports.io"  # no trailing slash

st.set_page_config(page_title="⚽ API Test", layout="wide")
st.title("⚽ API-Football Key Test")

# --- Sidebar inputs ---
league_id = st.sidebar.text_input("League ID", "39")   # 39 = EPL
season = st.sidebar.number_input("Season", min_value=2000, max_value=2030, value=2024)

# --- Test request ---
url = f"{BASE_URL}/fixtures"
params = {"league": league_id, "season": season, "next": 5}  # just 5 matches
response = requests.get(url, headers=HEADERS, params=params)

if response.status_code == 200:
    data = response.json()
    st.success("✅ API key is working!")
    st.json(data)  # show raw JSON
else:
    st.error(f"❌ Request failed with status {response.status_code}")
    st.text(response.text)
