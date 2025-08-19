import os, requests
from typing import Dict, Any, Optional
from .base import ProviderBase
from ..utils.cache import SimpleTTLCache

API_BASE = "https://api.football-data.org/v4"

class FootballDataProvider(ProviderBase):
    def __init__(self, api_key: Optional[str] = None, ttl_seconds: int = 900):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_TOKEN")
        self.cache = SimpleTTLCache(".cache/fd", ttl_seconds)

    def _headers(self):
        if not self.api_key:
            return {}
        return {"X-Auth-Token": self.api_key}

    def _get(self, path: str, params: dict | None = None) -> Any:
        key = path.replace("/", "_") + ("_" + str(params) if params else "")
        cached = self.cache.get(key)
        if cached:
            return cached
        url = f"{API_BASE}{path}"
        resp = requests.get(url, headers=self._headers(), params=params or {}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        self.cache.set(key, data)
        return data

    def get_match_context(self, match_id: str) -> Dict[str, Any]:
        data = self._get(f"/matches/{match_id}")
        m = data.get("match", data)  # FD returns directly at root for /v4/matches/{id}
        comp = m.get("competition", {}).get("name", "")
        season = str(m.get("season", {}).get("startDate", ""))[:4]
        return {
            "competition": comp,
            "season": season,
            "utc_kickoff": m.get("utcDate"),
            "home_team_id": str(m.get("homeTeam", {}).get("id")),
            "home_team_name": m.get("homeTeam", {}).get("name"),
            "away_team_id": str(m.get("awayTeam", {}).get("id")),
            "away_team_name": m.get("awayTeam", {}).get("name"),
            "venue": None,
        }

    def get_recent_form(self, team_id: str) -> Dict[str, Any]:
        # Use last 5 finished matches from /teams/{id}/matches?status=FINISHED&limit=5
        data = self._get(f"/teams/{team_id}/matches", params={"status": "FINISHED", "limit": 5})
        matches = data.get("matches", [])
        form = []
        for m in sorted(matches, key=lambda x: x.get("utcDate", ""))[-5:]:
            home = m.get("homeTeam", {}).get("id")
            away = m.get("awayTeam", {}).get("id")
            score = m.get("score", {}).get("winner")
            if score == "DRAW":
                form.append("D")
            elif (score == "HOME_TEAM" and str(home) == str(team_id)) or (score == "AWAY_TEAM" and str(away) == str(team_id)):
                form.append("W")
            else:
                form.append("L")
        return {"team_id": str(team_id), "last5": form}

    def get_standings_position(self, competition: str, team_id: str) -> Optional[int]:
        # competition should be code or id; FD commonly uses competition code like 'PL'
        try:
            data = self._get(f"/competitions/{competition}/standings")
        except Exception:
            return None
        for table in data.get("standings", []):
            if table.get("type") != "TOTAL":
                continue
            for row in table.get("table", []):
                if str(row.get("team", {}).get("id")) == str(team_id):
                    return int(row.get("position"))
        return None
