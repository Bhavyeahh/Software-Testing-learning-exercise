"""System orchestration for StreetRace Manager."""

from streetrace_manager.registration import RegistrationModule
from streetrace_manager.crew_management import CrewManagementModule


class StreetRaceSystem:
    """Top-level facade that wires modules together."""

    def __init__(self):
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
