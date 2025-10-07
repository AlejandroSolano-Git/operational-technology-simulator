# plant/plant_core/state.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

class MachineState(Enum):
    IDLE = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAULT = auto()

@dataclass
class Transition:
    from_state: MachineState
    to_state: MachineState
    reason: str = ""

@dataclass
class Lifecycle:
    state: MachineState = MachineState.IDLE
    enter_at: float = 0.0   #last time this state was entered (plant clock seconds)
    cycles: int = 0     #count of successful RUNNING-STOPPED cycles
    last_reason: str = ""      #human note for observability

    def _enter(self, to_state: MachineState, t: float, reason: str = "") -> Transition:
        tr = Transition(self.state, to_state, reason)
        self.state = to_state
        self.entered_at = t
        self.last_reason = reason
        return tr
    
    #Intent: called when operator/HMI issues a start
    def request_start(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state in (MachineState.IDLE, MachineState.STOPPED):
            return self._enter(MachineState.STARTING, t, reason or "Start Requested")
        return None
    
    #Mechanism confirm interlocks ok -> move to RUNNING
    def confirm_started(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state == MachineState.STARTING:
            return self._enter(MachineState.RUNNING, t, reason or "Started")
        return None
    
    #Operator/HMI issues stop
    def request_stop(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state in (MachineState.RUNNING, MachineState.STARTING):
            return self._enter(MachineState.STOPPING, t, reason or "Stop Requested")
        return None
    
    #Mechanism confirms safe stop complete
    def confirm_stopped(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state == MachineState.STOPPING:
            self.cycles += 1
            return self._enter(MachineState.STOPPED, t, reason or "Stopped")
        return None
    
    #Any time a hard interlock trips
    def trip_fault(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state != MachineState.FAULT:
            return self._enter(MachineState.FAULT, t, reason or "Fault")
        return None
    
    #After fault acknoledged and safe to reset
    def clear_fault(self, t: float, reason: str = "") -> Optional[Transition]:
        if self.state == MachineState.FAULT:
            return self._enter(MachineState.IDLE, t, reason or "Fault Cleared")
        return None
    
    #Convenience
    @property
    def is_runing(self) -> bool:
        return self.state == MachineState.RUNNING