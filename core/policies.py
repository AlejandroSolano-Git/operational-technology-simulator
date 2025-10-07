# core/policies.py 
from __future__ import annotations
from typing import Callable, Iterable, Optional

Predicate = Callable[[], bool]

def all_true(predicates: Iterable[Predicate]) -> bool:
    return all(p() for p in predicates)

def any_true(predicates: Iterable[Predicate]) -> bool:
    return any(p() for p in predicates)

# Dwell: This condition must be true for N milliseconds to return true
def dwell_ok(is_true_now: bool, last_true_since: Optional[float], now_mono: float, dwell_ms: float):
    """
    Returns (ok_now: bool, new_last_true_since: Optional[float]).
    - If condition is true, we restart the timer
    - ok_now only becomes True after dwell_ms of continuous truth
    """
    if not is_true_now:
        return False, None
    if last_true_since is None:
        last_true_since = now_mono
    ok = (now_mono - last_true_since) * 1000.0 >= dwell_ms
    return ok, last_true_since

#Hysteresis for thresholds: Avoid chattering around a boundary
def hysteresis_ok(current_ok: bool, measured: float, min_on: float, h_up: float, h_down: float) -> bool:
    """
    Rising edge requires measured >= (min_on + h_up)
    Falling edge drops when measured <= (min_on - h_down)
    """

    if current_ok:
        return measured > (min_on - h_down)
    else: 
        return measured >= (min_on + h_up)

#Once tripped, stays tripped until reset()  

class LatchedTrip:
    def __init__(self) -> False:
        self._tripped = False
    
    def eval(self, trip_condition_now: bool) -> bool:
        if trip_condition_now:
            self._tripped = True
        return self._tripped
    
    def reset(self) -> None:
        self._tripped = False