from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TeamForm:
    team_id: str
    team_name: str
    last5: List[str]  # e.g., ['W','D','L','W','W']

@dataclass
class TeamDiscipline:
    team_id: str
    yellow_per_match: float = 0.0
    red_per_match: float = 0.0

@dataclass
class TeamInjuries:
    team_id: str
    injured_count: int = 0
    key_starters_out: int = 0

@dataclass
class MatchContext:
    competition: str
    season: str
    utc_kickoff: str
    home_team_id: str
    home_team_name: str
    away_team_id: str
    away_team_name: str
    home_position: Optional[int] = None
    away_position: Optional[int] = None
    venue: Optional[str] = None
    home_is_home: bool = True
