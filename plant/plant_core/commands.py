# plant/plant_core/plant_commands.py

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Deque, Optional
from collections import deque

class CommandType(Enum):
    START = auto()
    STOP = auto()
    OPEN = auto()
    CLOSE = auto()
    ACK = auto()

@dataclass
class Command:
    type: CommandType
    t: float        #plant clock seconds
    source: str = "hmi"     #"hmi", "sequence", "test", etc.
    note: str = ""

class CommandQueue:
    def __init__(self, debounce_s: float = 0.0):
        self._q: Deque[Command] = deque()
        self._last_t: Optional[float] = None
        self._debounce_s = debounce_s

    def push(self, cmd: Command) -> bool:
        if self._last_t is not None and (cmd.t - self._last_t) < self._debounce_s:
            return False
        self._q.append(cmd)
        self._last_t = cmd.t
        return True
    
    def pop(self) -> Optional[Command]:
        return self._q.popleft() if self._q else None

    def peek(self) -> Optional[Command]:
        return self._q[0] if self._q else None
    
    def clear(self) -> None: 
        self._q.clear()