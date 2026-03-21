"""Extra module: reputation tracking based on race and mission performance."""


class ReputationModule:
    """Tracks street reputation score by crew member."""

    def __init__(self):
        self._scores: dict[str, int] = {}

    def apply_race_points(self, driver: str, points: int) -> None:
        """Increase reputation according to race points."""
        self._scores[driver] = self._scores.get(driver, 0) + points

    def apply_mission_bonus(self, member_name: str, bonus: int = 5) -> None:
        """Increase reputation for successful mission contribution."""
        self._scores[member_name] = self._scores.get(member_name, 0) + bonus

    def score(self, member_name: str) -> int:
        """Return current reputation score."""
        return self._scores.get(member_name, 0)

    def leaderboard(self) -> list[tuple[str, int]]:
        """Return reputation leaderboard sorted by score descending."""
        return sorted(self._scores.items(), key=lambda item: item[1], reverse=True)
