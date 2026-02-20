"""
Data models for the triage scheduler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SkipReason(Enum):
    COOLDOWN = "cooldown"
    VACATION = "vacation"
    ALREADY_ASSIGNED = "already_assigned"


@dataclass
class Member:
    name: str
    rotation_order: int
    is_available: bool = True  # False when on vacation


@dataclass
class App:
    name: str
    id: int  # 0-based index used by the algorithm


@dataclass
class Assignment:
    member: Member
    app: App
    week: int
    is_substitute: bool = False  # True when filling in for a vacationer


@dataclass
class PointerState:
    """Tracks position of one logical pointer in the ring."""
    pointer_id: int          # 0-based (one per app slot)
    position: int            # index into sorted member list (-1 = not yet started)
    held: bool = False       # True when pointer is held due to vacation


@dataclass
class ScheduleState:
    """Full state needed to compute the next week's assignments."""
    members: list[Member]
    apps: list[App]
    pointers: list[PointerState]                # one per app slot
    week: int = 0
    last_assignments: dict[str, str] = field(default_factory=dict)  # member_name -> app_name
    label_rotation_offset: int = 0              # rotates every cycle_length weeks
    cooldown_relaxed: bool = False

    @property
    def num_apps(self) -> int:
        return len(self.apps)

    @property
    def num_members(self) -> int:
        return len(self.members)

    @property
    def cycle_length(self) -> int:
        """Weeks per label-rotation cycle: N / K."""
        return self.num_members // self.num_apps

    def app_for_pointer(self, pointer_id: int) -> App:
        """Which app a pointer is currently assigned to, after label rotation."""
        rotated_index = (pointer_id + self.label_rotation_offset) % self.num_apps
        return self.apps[rotated_index]
