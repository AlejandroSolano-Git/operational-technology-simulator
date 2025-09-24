# tests/test_core_point.py
from core.point import AnalogPoint, Quality, CovRule

def test_cov_deadband_abs():
    pt = AnalogPoint(id="A1.PT101", value=10.0, ts_mono=0.0, quality=Quality.GOOD, cov=CovRule(deadband_abs=0.2))
    prev = AnalogPoint(**pt.__dict__)
    now = 1.0
    pt.value = 10.05
    assert not pt.should_publish(prev, now)
    pt.value = 10.25
    assert pt.should_publish(prev, now)