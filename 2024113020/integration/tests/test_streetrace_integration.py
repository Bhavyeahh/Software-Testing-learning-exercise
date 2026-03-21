"""Integration tests for StreetRace Manager module interactions."""

import pytest

from streetrace_manager.system import StreetRaceSystem


@pytest.fixture
def system() -> StreetRaceSystem:
    """Provide a fresh system instance for each test."""
    return StreetRaceSystem()


def _prepare_driver(system: StreetRaceSystem, name: str = "Kai") -> None:
    system.registration.register_member(name)
    system.crew_management.assign_role(name, "driver")


def test_register_driver_then_enter_race(system: StreetRaceSystem):
    """Driver can be registered and entered in race with available car."""
    _prepare_driver(system, "Asha")
    system.inventory.add_car("C1", "Nissan Skyline")
    system.race_management.create_race("R1", "Dockside Sprint")

    system.race_management.enter_participant("R1", "Asha", "C1")

    race = system.race_management.get_race("R1")
    assert race is not None
    assert race.participants == [{"driver": "Asha", "car_id": "C1"}]


def test_enter_race_with_unregistered_driver_fails(system: StreetRaceSystem):
    """Race entry must fail for an unregistered driver."""
    system.inventory.add_car("C2", "Toyota Supra")
    system.race_management.create_race("R2", "Harbor Run")

    with pytest.raises(ValueError, match="registered"):
        system.race_management.enter_participant("R2", "Ghost", "C2")


def test_enter_race_with_non_driver_role_fails(system: StreetRaceSystem):
    """Only members with driver role can enter races."""
    system.registration.register_member("Mina")
    system.crew_management.assign_role("Mina", "mechanic")
    system.inventory.add_car("C3", "Mazda RX-7")
    system.race_management.create_race("R3", "Tunnel Dash")

    with pytest.raises(ValueError, match="driver"):
        system.race_management.enter_participant("R3", "Mina", "C3")


def test_result_updates_ranking_and_inventory_cash(system: StreetRaceSystem):
    """Recording race results must update ranking and inventory cash balance."""
    _prepare_driver(system, "Ryo")
    _prepare_driver(system, "Lena")
    system.inventory.add_car("C4", "Honda NSX")
    system.inventory.add_car("C5", "Subaru WRX")
    system.race_management.create_race("R4", "Neon Circuit")
    system.race_management.enter_participant("R4", "Ryo", "C4")
    system.race_management.enter_participant("R4", "Lena", "C5")

    system.results.record_result("R4", ["Lena", "Ryo"], prize_money=3000)

    assert system.inventory.cash_balance() == 3000
    assert system.results.leaderboard()[0][0] == "Lena"


def test_damaged_car_requires_mechanic_for_mission(system: StreetRaceSystem):
    """Mission start must fail with damaged car when no mechanic is available."""
    system.registration.register_member("Ivy")
    system.crew_management.assign_role("Ivy", "strategist")
    system.inventory.add_car("C6", "Ford Mustang")
    system.inventory.mark_car_damaged("C6")
    system.mission_planning.create_mission("M1", "delivery", {"strategist"})

    with pytest.raises(ValueError, match="mechanic"):
        system.mission_planning.start_mission("M1")


def test_mission_starts_when_required_roles_available(system: StreetRaceSystem):
    """Mission should start once required roles are assigned and available."""
    system.registration.register_member("Neo")
    system.registration.register_member("Kira")
    system.crew_management.assign_role("Neo", "strategist")
    system.crew_management.assign_role("Kira", "mechanic")
    system.inventory.add_car("C7", "BMW M3")
    system.inventory.mark_car_damaged("C7")
    system.mission_planning.create_mission("M2", "rescue", {"strategist", "mechanic"})

    system.mission_planning.start_mission("M2")

    mission = system.mission_planning.get_mission("M2")
    assert mission is not None
    assert mission.status == "active"


def test_extra_module_maintenance_repairs_car(system: StreetRaceSystem):
    """Maintenance module should repair damaged car using mechanic and parts."""
    system.registration.register_member("Bolt")
    system.crew_management.assign_role("Bolt", "mechanic")
    system.inventory.add_car("C8", "Audi R8")
    system.inventory.mark_car_damaged("C8")
    system.inventory.add_part("engine_kit", 2)
    system.inventory.add_tool("toolbox", 1)

    system.maintenance.repair_car("C8", "Bolt")

    car = system.inventory.get_car("C8")
    assert car is not None
    assert car.is_damaged is False
    assert car.is_available is True


def test_extra_module_reputation_updates_from_results(system: StreetRaceSystem):
    """Reputation module should gain points when race results are recorded."""
    _prepare_driver(system, "Ari")
    _prepare_driver(system, "Zed")
    system.inventory.add_car("C9", "Lancer Evo")
    system.inventory.add_car("C10", "Shelby GT500")
    system.race_management.create_race("R5", "Midnight Ring")
    system.race_management.enter_participant("R5", "Ari", "C9")
    system.race_management.enter_participant("R5", "Zed", "C10")

    system.results.record_result("R5", ["Ari", "Zed"], prize_money=1200)

    assert system.reputation.score("Ari") > system.reputation.score("Zed")


def test_role_assignment_requires_registration(system: StreetRaceSystem):
    """Business rule: role assignment only for registered members."""
    with pytest.raises(ValueError, match="registered"):
        system.crew_management.assign_role("Unknown", "driver")
