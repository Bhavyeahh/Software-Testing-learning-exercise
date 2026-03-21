"""Extra module: garage maintenance for repairing damaged cars."""

from streetrace_manager.inventory import InventoryModule
from streetrace_manager.registration import RegistrationModule


class MaintenanceModule:
    """Repairs damaged cars when mechanics and resources are available."""

    def __init__(self, registration: RegistrationModule, inventory: InventoryModule):
        self.registration = registration
        self.inventory = inventory

    def repair_car(self, car_id: str, mechanic_name: str) -> None:
        """Repair a damaged car using one engine kit and one toolbox usage."""
        member = self.registration.get_member(mechanic_name)
        if member is None or member.role != "mechanic":
            raise ValueError("Repair requires a registered mechanic.")

        car = self.inventory.get_car(car_id)
        if car is None:
            raise ValueError("Unknown car ID.")
        if not car.is_damaged:
            return

        if self.inventory.part_quantity("engine_kit") < 1:
            raise ValueError("Repair requires at least one engine_kit part.")
        if self.inventory.tool_quantity("toolbox") < 1:
            raise ValueError("Repair requires a toolbox.")

        self.inventory.use_part("engine_kit", 1)
        self.inventory.repair_car(car_id)
