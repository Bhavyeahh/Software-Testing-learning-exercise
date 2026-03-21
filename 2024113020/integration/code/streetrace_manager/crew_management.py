"""Crew management module for roles and skills."""

from streetrace_manager.registration import RegistrationModule


class CrewManagementModule:
    """Manages crew roles and skill levels for registered members only."""

    def __init__(self, registration: RegistrationModule):
        self.registration = registration

    def assign_role(self, member_name: str, role: str) -> None:
        """Assign role to an existing registered member."""
        member = self.registration.get_member(member_name)
        if member is None:
            raise ValueError("Member must be registered before role assignment.")
        member.role = role.strip().lower()

    def set_skill(self, member_name: str, skill_name: str, level: int) -> None:
        """Set a named skill level from 1 to 10 for a registered member."""
        member = self.registration.get_member(member_name)
        if member is None:
            raise ValueError("Member must be registered before skill updates.")
        if level < 1 or level > 10:
            raise ValueError("Skill level must be between 1 and 10.")
        member.skills[skill_name.strip().lower()] = level

    def members_by_role(self, role: str) -> list[str]:
        """Return member names that currently match role."""
        target = role.strip().lower()
        return [m.name for m in self.registration.list_members() if m.role == target]
