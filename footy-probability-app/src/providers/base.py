from abc import ABC, abstractmethod
from typing import Dict, Any

class ProviderBase(ABC):
    @abstractmethod
    def get_recent_form(self, team_id: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    def get_standings_position(self, competition: str, team_id: str) -> int | None:
        ...

    @abstractmethod
    def get_match_context(self, match_id: str) -> Dict[str, Any]:
        ...

    def get_team_cards(self, team_id: str) -> Dict[str, float] | None:
        return None  # Optional

    def get_injuries(self, team_id: str) -> Dict[str, int] | None:
        return None  # Optional
