"""System orchestration for StreetRace Manager."""

from streetrace_manager.registration import RegistrationModule


class StreetRaceSystem:
    """Top-level facade that wires modules together."""

    def __init__(self):
        self.registration = RegistrationModule()
