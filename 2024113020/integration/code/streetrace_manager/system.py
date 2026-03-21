"""System orchestration for StreetRace Manager."""

from streetrace_manager.registration import RegistrationModule
from streetrace_manager.crew_management import CrewManagementModule
from streetrace_manager.inventory import InventoryModule
from streetrace_manager.race_management import RaceManagementModule
from streetrace_manager.results import ResultsModule
from streetrace_manager.mission_planning import MissionPlanningModule
from streetrace_manager.maintenance import MaintenanceModule


class StreetRaceSystem:
    """Top-level facade that wires modules together."""

    def __init__(self):
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
        self.inventory = InventoryModule()
        self.race_management = RaceManagementModule(self.registration, self.inventory)
        self.results = ResultsModule(self.race_management, self.inventory)
        self.mission_planning = MissionPlanningModule(self.registration, self.inventory)
        self.maintenance = MaintenanceModule(self.registration, self.inventory)
