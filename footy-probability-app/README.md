# ⚽ Footy Probability App

A Streamlit app that pulls soccer data (form, cards, injuries when available), compiles features, and outputs a match **win/draw/loss probability** with an explanation.

> Works **without API keys** in **Demo Mode** using sensible mock data, and upgrades automatically when you provide real API keys.

## 🚀 Quick Start

```bash
git clone https://github.com/<your-username>/footy-probability-app.git
cd footy-probability-app
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Optional: add provider keys
cp .env.example .env
# edit .env with your tokens

# Run the app
streamlit run app.py
```

## 🔌 Data Providers

- **Football-Data.org** — fixtures, results, standings, recent form (free tier).
- **API-Football** — injuries and card stats (paid/free tiers). Optional.

You can run with one or both; the app gracefully degrades and explains what's missing.

## 🧠 Probability Model (baseline)

A transparent, rule-based model that combines:
- Recent form (last 5 matches, weighted 3-2-1-1-1)
- Strength proxy from table position (Elo-style anchor)
- Discipline adjustment from yellow/red cards per match (if available)
- Injury impact from estimated starters missing (if available)
- Home-field advantage

Scores are converted to probabilities with a softmax and calibrated with a small draw prior.

You can swap in your own model easily—see `src/models/probability.py`.

## 🗂️ Project Structure

```
footy-probability-app/
├─ app.py
├─ requirements.txt
├─ .env.example  # copy to .env
├─ LICENSE
├─ src/
│  ├─ providers/
│  │  ├─ base.py
│  │  ├─ football_data.py
│  │  └─ api_football.py
│  ├─ models/
│  │  └─ probability.py
│  ├─ utils/
│  │  ├─ cache.py
│  │  └─ schemas.py
│  └─ demo/
│     └─ mock_payloads.json
└─ README.md
```

## 📦 Deploy

- **GitHub**: push this folder to a new repo.
- **Streamlit Cloud**: connect your repo and set `PYTHON_VERSION` (>=3.10). Add secrets or `.env` in Streamlit.
- **Docker**: create a simple Dockerfile if needed.

## ⚠️ Disclaimer

This app is for **information and education**. No guarantees are made about accuracy or fitness for betting. Use responsibly.
