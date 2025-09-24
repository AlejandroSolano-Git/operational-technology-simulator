# core/policy_points.py
from typing import Protocol, runtime_checkable, Any
from enum import Enum

@runtime_checkable
class QualityLike(Protocol):
    quality: Any # Must compare equal to "GOOD" somehow

def is_good(p: QualityLike) -> bool:
    #works with Point or any object that exposes the .quality with name "GOOD"
    q = getattr(p.quality, "name", p.quality)
    return q == "GOOD"

# Analogs (Float/int with optional eng())
@runtime_checkable
class AnalogLike(QualityLike, Protocol):
    value: float | int
    def eng(self) -> float: ... #If absent, we'll fall back to .value

def analog_value(p: AnalogLike) -> float:
    return float(p.eng() if hasattr(p, "eng") else p.value)
    
#Both threshold_ge and within_band are for permissives/interlocks, like if suction > min
def threshold_ge(p: AnalogLike, threshold: float) -> bool:
    return is_good(p) and analog_value(p) >= threshold

def within_band(p: AnalogLike, lo: float, hi: float) -> bool:
    return is_good(p) and lo <= analog_value(p) <= hi

# Binaries (bool)
@runtime_checkable
class BinaryLike(QualityLike, Protocol):
    value: bool

# For READY/RUN/Fault flags
def good_bool(p: BinaryLike) -> bool:
    return is_good(p) and bool(p.value)

# Counters (int totals)
@runtime_checkable
class CounterLike(QualityLike, Protocol):
    value: int

def counter_nondecreasing(prev: CounterLike, curr: CounterLike) -> bool:
    #Treat bad quality as failure
    return is_good(prev) and is_good(curr) and (curr.value >= prev.value)

# For flow totalizers/energy pusles wihtout double-counting during bad quality
def counter_delta(prev: CounterLike, curr: CounterLike) -> int:
    #Returns 0 if either sample isn't good
    if not(is_good(prev) and is_good(curr)):
        return 0
    return max(0, curr.value - prev.value)

# Discrete enums (multi-state)
@runtime_checkable
class DiscreteLike(QualityLike, Protocol):
    value: Enum     #Like ValueState.OPEN/CLOSED/TRAVELING

# discrete_is and discrete_in for valve/breaker state logic
def discrete_is(p: DiscreteLike, state: Enum) -> bool:
    return is_good(p) and (p.value == state)

def discrete_in(p: DiscreteLike, states: set[Enum]) -> bool:
    return is_good(p) and (p.value in states)