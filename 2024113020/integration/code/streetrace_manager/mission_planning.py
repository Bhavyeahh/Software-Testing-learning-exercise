"""Mission planning module with required-role validation."""

from streetrace_manager.inventory import InventoryModule
from streetrace_manager.models import Mission
from streetrace_manager.registration import RegistrationModule


class MissionPlanningModule:
    """Assigns missions and verifies required roles are available."""

    def __init__(self, registration: RegistrationModule, inventory: InventoryModule):
        self.registration = registration
        self.inventory = inventory
        self._missions: dict[str, Mission] = {}

    def create_mission(self, mission_id: str, mission_type: str, required_roles: set[str]) -> Mission:
        """Create a mission with explicit required roles."""
        if mission_id in self._missions:
            raise ValueError("Mission ID already exists.")
        mission = Mission(mission_id=mission_id, mission_type=mission_type, required_roles=required_roles)
        self._missions[mission_id] = mission
        return mission

    def start_mission(self, mission_id: str) -> None:
        """Start mission only if all required roles are currently available."""
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError("Unknown mission ID.")

        available_roles = {m.role for m in self.registration.list_members() if m.role != "unassigned"}
        missing_roles = [role for role in mission.required_roles if role not in available_roles]
        if missing_roles:
            raise ValueError(f"Cannot start mission; missing roles: {', '.join(sorted(missing_roles))}")

        # Business rule: damaged cars require mechanic availability for mission readiness.
        if any(car.is_damaged for car in self.inventory.list_cars()) and "mechanic" not in available_roles:
            raise ValueError("Cannot start mission while cars are damaged and no mechanic is available.")

        mission.status = "active"

    def complete_mission(self, mission_id: str) -> None:
        """Complete an active mission."""
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError("Unknown mission ID.")
        mission.status = "completed"

    def get_mission(self, mission_id: str) -> Mission | None:
        """Return mission by ID."""
        return self._missions.get(mission_id)
