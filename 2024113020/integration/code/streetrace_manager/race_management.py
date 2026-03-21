"""Race management module for creating races and selecting participants."""

from streetrace_manager.inventory import InventoryModule
from streetrace_manager.models import Race
from streetrace_manager.registration import RegistrationModule


class RaceManagementModule:
    """Creates races and validates crew/car selections."""

    def __init__(self, registration: RegistrationModule, inventory: InventoryModule):
        self.registration = registration
        self.inventory = inventory
        self._races: dict[str, Race] = {}

    def create_race(self, race_id: str, name: str) -> Race:
        """Create and store a race entry."""
        if race_id in self._races:
            raise ValueError("Race ID already exists.")
        race = Race(race_id=race_id, name=name)
        self._races[race_id] = race
        return race

    def get_race(self, race_id: str) -> Race | None:
        """Return race by ID."""
        return self._races.get(race_id)

    def enter_participant(self, race_id: str, driver_name: str, car_id: str) -> None:
        """Enter a driver with a specific car into a race."""
        race = self.get_race(race_id)
        if race is None:
            raise ValueError("Unknown race ID.")

        member = self.registration.get_member(driver_name)
        if member is None:
            raise ValueError("Driver must be registered before race entry.")
        if member.role != "driver":
            raise ValueError("Only crew members with role 'driver' can race.")

        car = self.inventory.get_car(car_id)
        if car is None:
            raise ValueError("Car must exist in inventory.")
        if not car.is_available or car.is_damaged:
            raise ValueError("Selected car is not race-ready.")

        race.participants.append({"driver": member.name, "car_id": car_id})
        car.is_available = False

    def close_race(self, race_id: str) -> None:
        """Mark race as completed and free cars for future usage."""
        race = self.get_race(race_id)
        if race is None:
            raise ValueError("Unknown race ID.")
        race.status = "completed"
        for entry in race.participants:
            car = self.inventory.get_car(entry["car_id"])
            if car and not car.is_damaged:
                car.is_available = True
