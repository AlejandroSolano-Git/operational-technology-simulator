# core/clock.py
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Protocol

class ScanClock(Protocol):
    """Protocol-like base for typing clarity. Not designed for methods enforcement."""
    def now(self) -> float: ...
    def wall_now(self) -> datetime: ...
    def sleep_until_next_scan(self) -> None: ...

class RealTimeClock(ScanClock):
    """
    Deterministic metronome for the scan loop.
    - Uses time.monotonic() to avoid jumping the timing
    - Uses datetime.now(timezone.utc) for the human-readable logs.
    - Overrun policy: Skipping to the next aligned tick to avoid catching up and causing spikes in CPU. Calls on_overrun().
    """

    def __init__(
            self,
            period_s: float,
            on_overrun: Optional[Callable[[float, float], None]] = None
    ) -> None: 
        if period_s <= 0:
            raise ValueError("period_s must be > 0")
        self.period_s = period_s
        self._on_overrun = on_overrun or (lambda behind_s, now_s: None)
        #We align the first deadline here for multiple periods.
        start = time.monotonic()
        remainder = start % self.period_s
        self._next_deadline = start + (self.period_s - remainder)

    def now(self) -> float:
        return time.monotonic()
    
    def wall_now(self) -> datetime:
        return datetime.now(timezone.utc)
    
    def sleep_until_next_scan(self) -> None:
        now = time.monotonic()
        #If the scan is early, we want to sleep until it is on time
        if now < self._next_deadline:
            time.sleep(self._next_deadline - now)
            self._next_deadline += self.period_s
            return
        
        #Overrun: We are now late. We need to skip forward by periods until we are ahead again.
        #For this, we report how far behind we were, the continue to the next tick.
        behind = now - self._next_deadline
        if behind > 0:
            self._on_overrun(behind, now)
            #Jump the deadline forward to the next future tick
            missed_ticks = int(behind // self.period_s) + 1
            self._next_deadline += missed_ticks * self.period_s
        #Here we don't want to sleep at all. We need to run immediately and re-check on the next call.

class SimClock(ScanClock):
    """
    Stopwatch style clock for testing and replay.
    - Time is controlled; nothing actually sleeps.
    - This keeps us deterministic and fast.
    """

    def __init__(self, period_s: float, start_s: float = 0.0) -> None:
        if period_s <= 0:
            raise ValueError("period_s must be > 0")
        self.period_s = period_s
        self._t = start_s

    def now(self) -> float:
        return self._t
        
    def wall_now(self) -> datetime:
        #For future reference, we can map fake time onto a base wall time.
        #Here we will just return a synthetic UTC time.
        base = datetime(2000, 1, 1, tzinfo=timezone.utc)
        return base + timedelta(seconds=self._t)
    
    def tick(self, n: int = 1) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        self._t += n * self.period_s
    
    def sleep_until_next_scan(self) -> None:
        #We do not want to sleep in this clock. We just need to advance time by one period.
        self.tick(1)