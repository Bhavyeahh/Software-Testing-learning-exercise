"""Registration module for crew onboarding."""

from streetrace_manager.models import CrewMember


class RegistrationModule:
    """Registers and retrieves crew members."""

    def __init__(self):
        self._members: dict[str, CrewMember] = {}

    def register_member(self, name: str, role: str = "unassigned") -> CrewMember:
        """Register a new crew member with name and optional role."""
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("Crew member name cannot be empty.")
        if normalized in self._members:
            raise ValueError(f"Crew member '{name}' is already registered.")
        member = CrewMember(name=name.strip(), role=role)
        self._members[normalized] = member
        return member

    def get_member(self, name: str) -> CrewMember | None:
        """Return a registered member or None."""
        return self._members.get(name.strip().lower())

    def list_members(self) -> list[CrewMember]:
        """List all registered members."""
        return list(self._members.values())
