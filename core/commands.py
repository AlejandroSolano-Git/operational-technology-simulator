# core/commands.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal

class CommandKind(str, Enum):
    START = "START"
    STOP = "STOP"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    SETPOINT = "SETPOINT"

class AckCode(str, Enum):
    OK = "OK"
    REJECTED = "REJECTED"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT" #LOCAL mode blocks RREMOTE example
    OUT_OF_RANGE = "OUT_OF_RANGE"

@dataclass
class Command:
    target: str # Device ID
    kind: CommandKind
    value: Optional[float] = None # For SETPOINT
    source: Literal["LOCAL", "REMOTE"] = "REMOTE"
    ts_mono: Optional[float] = None #Stamp with clk.now() at ingress
    request_id: Optional[str] = None #Optional for tracing

@dataclass
class Ack:
    ok: bool
    code: AckCode = AckCode.OK
    reason: Optional[str] = None

#Small, reusable validator for setpoints. 
def validate_setpoints(value: Optional[float], lo: float, hi: float) -> Ack:
    if value is None:
        return Ack(False, AckCode.INVALID, "SETPOINT requires a value")
    if not (lo <= value <= hi):
        return Ack(False, AckCode.OUT_OF_RANGE, f"value {value} not in [{lo}, {hi}]")
    return Ack(True, AckCode.OK, None)