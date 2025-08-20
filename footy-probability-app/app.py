import streamlit as st
import requests

# --- API-Football key ---
API_FOOTBALL_KEY = "af56a1c0b4654b80a8400478462ae752"
HEADERS = {
    "X-APISports-Key": API_FOOTBALL_KEY,   # ✅ Correct header spelling
    "Accept": "application/json"
}
BASE_URL = "https://v3.football.api-sports.io"  # no trailing slash

st.set_page_config(page_title="⚽ API Test", layout="wide")
st.title("⚽ API-Football Key Test")

# --- 1) Test API status endpoint ---
st.subheader("🔎 Step 1: Check API Status")
status_url = f"{BASE_URL}/status"
status_resp = requests.get(status_url, headers=HEADERS)

if status_resp.status_code == 200:
    st.success("✅ Successfully connected to API /status endpoint")
    st.json(status_resp.json())
else:
    st.error(f"❌ Failed to connect to /status (HTTP {status_resp.status_code})")
    st.text(status_resp.text)

# --- Sidebar inputs for fixtures ---
st.sidebar.header("Fixture Test")
league_id = st.sidebar.text_input("League ID", "39")   # 39 = EPL
season = st.sidebar.number_input("Season", min_value=2000, max_value=2030, value=2024)

# --- 2) Test fixtures endpoint ---
st.subheader("🔎 Step 2: Check Fixtures Endpoint")
fixtures_url = f"{BASE_URL}/fixtures"
params = {"league": league_id, "season": season, "next": 5}
fixtures_resp = requests.get(fixtures_url, headers=HEADERS, params=params)

if fixtures_resp.status_code == 200:
    data = fixtures_resp.json()
    if "errors" in data and data["errors"]:
        st.error("⚠️ API returned an error:")
        st.json(data["errors"])
    else:
        st.success("✅ Fixtures retrieved successfully!")
        st.json(data)
else:
    st.error(f"❌ Failed to connect to /fixtures (HTTP {fixtures_resp.status_code})")
    st.text(fixtures_resp.text)
