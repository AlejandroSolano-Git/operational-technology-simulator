# plant/plant_core/alarms.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, Optional

class Severity(Enum):
    INFO = auto()
    WARN = auto()
    ALARM = auto()
    TRIP = auto()

@dataclass
class Alarm:
    key: str
    text: str
    severity: Severity = Severity.ALARM
    latching: bool = True

    active: bool = False    #current sensed condition (raw)
    latched: bool = False       #has it latched due to activation?
    acked: bool = False     #has operator acknowledged?
    first_t: Optional[float] = None
    last_t: Optional[float] = None

    def update(self, active_raw: bool, t: float) -> None:
        #Edge detection
        if active_raw and not self.active:
            self.first_t = t
        if active_raw:
            self.last_t = t
        self.active = active_raw

        #Latch policy
        if self.latching:
            if active_raw:
                self.latched = True
            #unlatch only when not active AND acked
            elif self.acked:
                self.latched = False
                self.acked = False

        else:
            #non-latching mirrors active, ack clears nothing
            self.latched = active_raw
    
    def ack(self) -> None:
        self.acked = True
        #For non-latching, ack acts as a no-op; for latching, unlatch will ocur next update when inactive

@dataclass
class AlarmPanel:
    alarms: Dict[str, Alarm] = field(default_factory=dict)

    def add(self, alarm: Alarm) -> None:
        self.alarms[alarm.key] = alarm

    def update(self, signals: Dict[str, bool], t: float) -> None:
        for key, a in self.alarms.items():
            a.update(bool(signals.get(key, False)), t)

    def any_trip(self) -> bool:
        return any(a.active and a.severity == Severity.TRIP for a in self.alarms.values())
    
    def unacked(self) -> Iterable[Alarm]:
        return (a for a in self.alarms.values() if (a.active or a.latched) and not a.acked)
    
    def ack_all(self) -> None:
        for a in self.alarms.values():
            a.ack()