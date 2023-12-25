
from dataclasses import dataclass
from enum import Enum


class CharcoalStatus(Enum):
    UNTRACKED = -1
    DISABLED = 0
    ENABLED = 1


@dataclass(eq=False, frozen=True)
class Rcon_Settings:
    enabled: bool
    port: int
    password: str