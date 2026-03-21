"""System orchestration for StreetRace Manager."""

from streetrace_manager.registration import RegistrationModule
from streetrace_manager.crew_management import CrewManagementModule
from streetrace_manager.inventory import InventoryModule


class StreetRaceSystem:
    """Top-level facade that wires modules together."""

    def __init__(self):
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
        self.inventory = InventoryModule()
