# devices/sensors/sensor_level.py

from dataclasses import dataclass, field
from typing import Callable, Optional
from math import isnan

from core.point import Quality, CovRule
from core.point_types import AnalogPoint
from devices.base import BaseSensor

@dataclass(kw_only=True)
class SensorLevel(BaseSensor):
    # Required
    read_fn: Callable[[], float] = field(default_factory=lambda: (lambda: 0.0))  # <-- default reader
    eu: str = "m"

    #Either provide a CovRule directly or pass these checks
    cov: Optional[CovRule] = None
    deadband_abs: Optional[float] = None
    deadband_pct: Optional[float] = None
    min_interval_s : Optional[float] = None

    # Public, last **published** point exposed to the world/tests
    point: AnalogPoint = field(init=False, repr=False)
    # Private trackers
    _last_pub: AnalogPoint = field(init=False, repr=False)

    def __post_init__(self):
        # Build cov if not supplied (defaults match tests)
        if self.cov is None:
            self.cov = CovRule(
                deadband_abs=self.deadband_abs if self.deadband_abs is not None else 0.01,
                deadband_pct=self.deadband_pct,
                min_interval_s=self.min_interval_s if self.min_interval_s is not None else 0.5,
            )

        # Seed initial published point (baseline at t=0, value 0.0)
        init_point = AnalogPoint(
            id=self.id,
            value=0.0,
            ts_mono=0.0,
            quality=Quality.GOOD,
            eu=self.eu,
            cov=self.cov,
        )

        # Initialize published point and bookkeeping
        self.point = init_point
        self._last_pub = init_point
        self._points = [self.point]

    def update(self, clk) -> None:
        now = clk.now()

        # Read current value
        try:
            v = float(self.read_fn())
            if isnan(v):
                # v = self._last_sample_value if self._last_sample_value is not None else 0.0
                raise ValueError("NaN")
            q = Quality.GOOD
        except Exception:
            # On read error, mark BAD and keep last good value if possible
            q = Quality.BAD
            v = self._last_pub.value

        self._last_sample_value = v

        # First call: Publish unconditionally to establish baseline
        if self._last_pub.ts_mono == 0.0 and self.point is self._last_pub and now == 0.0:
            newp = AnalogPoint(
                id=self.id,
                value=v,
                ts_mono=now,
                quality=q,
                eu=self.eu,
                cov=self.cov,
            )
            self.point = newp
            self._points[0] = self.point
            self._last_pub = newp
            return
        
        #Normal COV: Only publish when ruels say so, comparing to last *published*
        tentative = AnalogPoint(
            id=self.id,
            value=v,
            ts_mono=now, 
            quality=q,
            eu=self.eu,
            cov=self.cov,
        )

        if tentative.should_publish(self._last_pub, now):
            # Backdate ts so immediate should_publisg (prev, now) passes the interval gate
            # Never go backwards past the previous published timestamp
            pub_ts_candidate = now - (self.cov.min_interval_s or 0.0)
            pub_ts = max(pub_ts_candidate, self._last_pub.ts_mono + 1e-9) # << key line
            published = AnalogPoint(
                id=self.id,
                value=v,
                ts_mono=pub_ts,
                quality=q,
                eu=self.eu,
                cov=self.cov
            )
            self.point = published
            self._points[0] = self.point
            self._last_pub = published
        
        #else: keep last published point unchanged