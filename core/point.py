# core/point.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime

T = TypeVar("T")

class Quality(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    STALE = "STALE"
    #This is for an operator to override
    MANUAL = "MANUAL" 

@dataclass
class Scaling:
    """Raw + engineering scaling: eng = raw * k + b"""
    k: float = 1.0
    b: float = 0.0

@dataclass
class CovRule:
    """Change of value rules for publishing/history"""
    deadband_abs: Optional[float] = None #For floats/ints
    deadband_pct: Optional[float] = None #(% of abs(prev))
    min_interval_s: float = 0.0 #Throttle publications

@dataclass
class Limits:
    """Engineering limits (display/sanity). Not alarms/policies."""
    lo: Optional[float] = None
    hi: Optional[float] = None

@dataclass
class Point(Generic[T]):
    id: str
    value: T
    ts_mono: float  #Monotonic timestamp in secs
    quality: Quality = Quality.GOOD
    eu: Optional[str] = None #Engineering units like "psi", "N"
    source: Optional[str] = None #Where the value came from: "sim", "rtu12", "tcp"
    ts_wall: Optional[datetime] = None #Optional wall clock stamp

    #Optional meta
    scaling: Optional[Scaling] = None
    cov: CovRule = field(default_factory=CovRule)
    limits: Limits = field(default_factory=Limits)

    #Internal: last publish time (monotonic)
    _last_pub_mono: float = field(default=0.0, repr=False)

    # Convenience methods
    def eng(self) -> Any:
        """Return engineering value (scaled) if scaling is defined"""
        if self.scaling and isinstance(self.value, (int,float)):
            return self.value * self.scaling.k + self.scaling.b
        return self.value
    
    def mark_stale(self) -> None:
        self.quality = Quality.STALE

    def is_stale(self, now_mono: float, max_age_s: float) -> bool:
        return (now_mono - self.ts_mono) > max_age_s
    
    def should_publish(self, prev: Optional["Point[T]"], now_mono: float) -> bool:
        """Decide if this update is worth emitting (COV + throttle + quality change)"""
        #We want to always publish on any quality change
        if prev and prev.quality != self.quality:
            self._last_pub_mono = now_mono
            return True
        
        #Repsct the min interval
        if self.cov.min_interval_s > 0 and (now_mono - self._last_pub_mono) < self.cov.min_interval_s:
            return False
        
        #For any numerical types, we apply deadband
        if isinstance(self.value, (int, float)) and prev and isinstance(prev.value, (int, float)):
            dv = abs(self.eng() - prev.eng())
            threshold = 0.0
            if self.cov.deadband_abs:
                threshold = max(threshold, self.cov.deadband_abs)
            if self.cov.deadband_pct and prev.value != 0:
                threshold = max(threshold, abs(prev.eng()) * (self.cov.deadband_pct / 100.0))
            if dv < threshold:
                return False
            
        #For non-numeric or first sample, publish
        self._last_pub_mono = now_mono
        return True

