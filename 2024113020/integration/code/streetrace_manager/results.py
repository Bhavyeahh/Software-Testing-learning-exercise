"""Results module for outcome records, rankings, and prize payout."""

from streetrace_manager.inventory import InventoryModule
from streetrace_manager.race_management import RaceManagementModule


class ResultsModule:
    """Records race outcomes and updates standings and cash."""

    def __init__(self, races: RaceManagementModule, inventory: InventoryModule):
        self.races = races
        self.inventory = inventory
        self._results: dict[str, list[dict[str, int | str]]] = {}
        self._ranking_points: dict[str, int] = {}

    def record_result(
        self,
        race_id: str,
        ordered_driver_names: list[str],
        prize_money: int,
        damaged_car_ids: list[str] | None = None,
    ) -> None:
        """Store race results, update ranking points, and add race prize money."""
        race = self.races.get_race(race_id)
        if race is None:
            raise ValueError("Unknown race ID.")
        if race.status == "completed":
            raise ValueError("Result already recorded for this race.")

        points = [10, 6, 4, 2, 1]
        normalized_order = [name.strip() for name in ordered_driver_names]
        self._results[race_id] = []

        for idx, driver in enumerate(normalized_order):
            earned = points[idx] if idx < len(points) else 0
            self._ranking_points[driver] = self._ranking_points.get(driver, 0) + earned
            self._results[race_id].append({"driver": driver, "position": idx + 1, "points": earned})

        if prize_money < 0:
            raise ValueError("Prize money cannot be negative.")
        self.inventory.add_cash(prize_money)

        for car_id in damaged_car_ids or []:
            self.inventory.mark_car_damaged(car_id)

        self.races.close_race(race_id)

    def leaderboard(self) -> list[tuple[str, int]]:
        """Return ranking sorted by points descending."""
        return sorted(self._ranking_points.items(), key=lambda item: item[1], reverse=True)

    def race_results(self, race_id: str) -> list[dict[str, int | str]]:
        """Return stored results for a race."""
        return self._results.get(race_id, [])
