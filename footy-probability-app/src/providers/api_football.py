import os, requests
from typing import Dict, Any, Optional
from .base import ProviderBase
from ..utils.cache import SimpleTTLCache

API_BASE = "https://api-football-v1.p.rapidapi.com/v3"

class APIFootballProvider(ProviderBase):
    def __init__(self, api_key: Optional[str] = None, host: Optional[str] = None, ttl_seconds: int = 900):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        self.host = host or os.getenv("API_FOOTBALL_HOST", "api-football-v1.p.rapidapi.com")
        self.cache = SimpleTTLCache(".cache/af", ttl_seconds)

    def _headers(self):
        if not self.api_key:
            return {}
        return {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": self.host}

    def _get(self, path: str, params: dict | None = None):
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

    def get_recent_form(self, team_id: str) -> Dict[str, Any]:
        # Fallback to fixtures results for last 5
        data = self._get("/fixtures", params={"team": team_id, "last": 5, "status": "FT"})
        form = []
        for item in data.get("response", []):
            home_id = str(item.get("teams", {}).get("home", {}).get("id"))
            away_id = str(item.get("teams", {}).get("away", {}).get("id"))
            winner_home = item.get("teams", {}).get("home", {}).get("winner")
            winner_away = item.get("teams", {}).get("away", {}).get("winner")
            if winner_home is None and winner_away is None:
                form.append("D")
            elif (winner_home and home_id == str(team_id)) or (winner_away and away_id == str(team_id)):
                form.append("W")
            else:
                form.append("L")
        return {"team_id": str(team_id), "last5": form}

    def get_team_cards(self, team_id: str) -> Dict[str, float] | None:
        # Stats: cards per match this season
        data = self._get("/teams/statistics", params={"team": team_id, "season": datetime.now().year})
        try:
            cards = data["response"]["cards"]
            yellow_total = sum(v.get("total", 0) or 0 for k, v in cards.get("yellow", {}).items())
            red_total = sum(v.get("total", 0) or 0 for k, v in cards.get("red", {}).items())
            played = data["response"]["fixtures"]["played"]["total"] or 1
            return {"yellow_per_match": yellow_total / played, "red_per_match": red_total / played}
        except Exception:
            return None

    def get_injuries(self, team_id: str) -> Dict[str, int] | None:
        # Injury endpoint
        data = self._get("/injuries", params={"team": team_id, "season": datetime.now().year})
        try:
            count = len(data.get("response", []))
            # Rough heuristic: assume 30% are starters if not given
            starters = int(round(count * 0.3))
            return {"injured_count": count, "key_starters_out": starters}
        except Exception:
            return None

    def get_standings_position(self, competition: str, team_id: str) -> int | None:
        # competition should be league id
        data = self._get("/standings", params={"league": competition, "season": datetime.now().year})
        for group in data.get("response", []):
            for league in group.get("league", {}).get("standings", []):
                for row in league:
                    if str(row.get("team", {}).get("id")) == str(team_id):
                        return int(row.get("rank"))
        return None

    def get_match_context(self, match_id: str) -> Dict[str, Any]:
        data = self._get("/fixtures", params={"id": match_id})
        if not data.get("response"):
            return {}
        f = data["response"][0]
        comp = f.get("league", {}).get("name", "")
        season = str(f.get("league", {}).get("season", ""))
        return {
            "competition": comp,
            "season": season,
            "utc_kickoff": f.get("fixture", {}).get("date"),
            "home_team_id": str(f.get("teams", {}).get("home", {}).get("id")),
            "home_team_name": f.get("teams", {}).get("home", {}).get("name"),
            "away_team_id": str(f.get("teams", {}).get("away", {}).get("id")),
            "away_team_name": f.get("teams", {}).get("away", {}).get("name"),
            "venue": f.get("fixture", {}).get("venue", {}).get("name"),
        }
