# devices/base.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Iterable, Callable, Dict, List, Optional, Any

from core.commands import Command, Ack, AckCode
from core.policies import all_true
from core.point import Point

# Common enums and types

class Mode(str, Enum):
    REMOTE = "REMOTE"
    LOCAL = "LOCAL"
    LOCKED = "LOCKED" #Ignores writes entirely

Permissive = Callable[[], bool] #e.g. threshold_ge(pt, 20.0)
Interlock = Callable[[], bool] #must stay True while running

# Device protocols (interfaces)

class Sensor(Protocol):
    id: str
    def update(self, clk) -> None: ...
    def points (self) -> Iterable[Point]: ...   #Which tages to publish
    def status(self) -> Dict[str, Any]: ...     #Lightweight status dict

class Actuator(Protocol):
    id: str
    def update(self, clk) -> None: ...
    def command(self, cmd: Command) -> Ack: ...
    def points(self) -> Iterable[Point]: ...
    def status(self) -> Dict[str, Any]: ...

# Small helpers

def _ack(ok: bool, code: AckCode = AckCode.OK, reason: Optional[str] = None) -> Ack:
    return Ack(ok=ok, code=code, reason=reason)

# Base mixins

@dataclass(kw_only=True)
class DeviceCore:
    """Base fields common to sensors and actuators"""
    id: str 
    mode: Mode = Mode.REMOTE
    meta: Dict[str, Any] = field(default_factory=dict)  #Freeform (location, eu set, etc.)

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode

@dataclass(init=False)
class StateMachineMixin:
    """Tiny state machine helper for actuators."""
    state: str = "OFF"
    _entered_at: float = 0.0

    def _enter(self, clk, new_state: str) -> None:
        if new_state != self.state:
            self.state = new_state
            self._entered_at = clk.now()

    def time_in_state(self, clk) -> float:
        return clk.now() - self._entered_at
    
@dataclass(init=False)
class CommandMixin:
    """Standard command handling + mode arbitration."""
    _last_cmd: Optional[Command] = None

    def _accept_if_remote(self) -> Ack | None:
        if getattr(self, "mode", Mode.REMOTE) == Mode.LOCKED:
            return _ack(False, AckCode.CONFLICT, "Device is LOCKED")
        if getattr(self, "mode", Mode.REMOTE) == Mode.LOCAL:
            return _ack(False, AckCode.CONFLICT, "Device in LOCAL mode")
        return None
    
# A generic actuator base

@dataclass(kw_only=True)
class BaseActuator(DeviceCore, StateMachineMixin, CommandMixin):
    """Implements common patterns; subclass to add real behavior."""
    #Wiring of safety logic:
    permissives: List[Permissive] = field(default_factory=list)
    interlocks: List[Interlock] = field(default_factory=list)

    #Points each actuator usually owns (override in subclass if needed)
    _points: List[Point] = field(default_factory=list, repr=False)

    def add_permissive(self, p: Permissive) -> None:
        self.permissives.append(p)

    def add_interlock(self, i: Interlock) -> None:
        self.interlocks.append(i)

    def _permissives_ok(self) -> bool:
        #If no permissives, treat as ok
        return all_true(self.permissives) if self.permissives else True
    
    def _interlocks_ok(self) -> bool:
        return all_true(self.interlocks) if self.interlocks else True
    
    # API expected by the world

    def command(self, cmd: Command) -> Ack:
        #Mode arbitration
        conflict = self._accept_if_remote()
        if conflict:
            return conflict
        #Subclasses handle specifics:
        self._last_cmd = cmd
        return self._on_command(cmd)
    
    def _on_command(self, cmd: Command) -> Ack:
        """Override in subclass to implement START/STOP/SETPOINT, etc."""
        return _ack(False, AckCode.INVALID, f"Unsupported command {cmd.kind}")
    
    def update(self, clk) -> None:
        """Overide in subclass. Recommended Patterns:
        - evaluate interlocks; force safe state if violated
        - otherwise, follow _last_cmd intent gated by permissives
        - set state via self._enter(self, ...)
        - push effects (e.g., plant.inflow = ...)
        """

        raise NotImplementedError
    
    def points(self) -> Iterable[Point]:
        return tuple(self._points)
    
    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "mode": self.mode.value,
            "state": self.state,
            "permissives_ok": self._permissives_ok(),
            "interlocks_ok": self._interlocks_ok(),
        }
    
# Small sensor base

@dataclass(kw_only=True)
class BaseSensor(DeviceCore):
    _points: List[Point] = field(default_factory=list, repr=False)

    def points(self) -> Iterable[Point]:
        return tuple(self._points)
    
    def status(self) -> Dict[str, Any]:
        return {
            "id":self.id,
            "mode": self.mode.value,
        }