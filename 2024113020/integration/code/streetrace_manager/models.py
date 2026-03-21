"""Domain models used by StreetRace Manager modules."""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class CrewMember:
    """Registered crew member with role and skill profile."""

    name: str
    role: str = "unassigned"
    skills: Dict[str, int] = field(default_factory=dict)


@dataclass
class Car:
    """Inventory car that can participate in races or missions."""

    car_id: str
    model: str
    is_available: bool = True
    is_damaged: bool = False


@dataclass
class Race:
    """Race definition and selected participants."""

    race_id: str
    name: str
    participants: List[Dict[str, str]] = field(default_factory=list)
    status: str = "planned"


@dataclass
class Mission:
    """Mission plan that requires specific roles."""

    mission_id: str
    mission_type: str
    required_roles: Set[str]
    status: str = "planned"
