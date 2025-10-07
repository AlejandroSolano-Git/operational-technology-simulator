# tests/test_devices_sensor_level.py

from core.clock import SimClock
from core.point import Quality, CovRule
from devices.sensors.sensor_level import SensorLevel

def test_level_sensor_updates_value_and_ts():
    val = {"h": 0.0}
    def read(): return val["h"]

    clk = SimClock(period_s=0.5)
    s = SensorLevel(id="LT_101", read_fn=read, eu="m")

    #First update should publish immediately
    val["h"] = 1.23
    s.update(clk)
    assert s.point.value == 1.23
    t0 = s.point.ts_mono

    #Next scan with a small change still publishes (no cov specified here)
    clk.sleep_until_next_scan()
    val["h"] = 1.24
    s.update(clk)
    assert s.point.ts_mono > t0
    assert s.point.quality == Quality.GOOD

def test_level_sensor_cov_deadband_and_interval():
    val = {"h": 0.0}
    def read(): return val["h"]
    
    clk = SimClock(0.5)
    s = SensorLevel(
        id="LT_102",
        read_fn=read, 
        eu="m", 
        cov=CovRule(deadband_abs=0.05, min_interval_s=0.5),
    )

    #First sample
    s.update(clk)
    prev = s.point

    #small wiggle below deadband -> should not publish
    clk.sleep_until_next_scan()
    val["h"] = 0.03
    s.update(clk)
    assert s.point is prev
    assert not s.point.should_publish(prev, clk.now())

    #Bigger change -> should publish
    clk.sleep_until_next_scan()
    val["h"] = 0.10
    prev2 = s.point
    s.update(clk)
    assert s.point is not prev2
    assert s.point.should_publish(prev2, clk.now())

def test_level_cov_uses_last_published():
    s = SensorLevel(
        id="LT_103",
        read_fn=lambda: 0.0,
        deadband_abs=0.05,
        min_interval_s=0.5
    )
    clk = SimClock(0.5)
    
    # Initial publish
    s.update(clk)           # value 0.0
    prev_pub = s.point

    # Below deadband -> no publish
    clk.sleep_until_next_scan()
    s.read_fn = lambda: 0.03
    s.update(clk)
    assert s.point is prev_pub

    # Big change -> should publish
    clk.sleep_until_next_scan()
    s.read_fn = lambda: 0.10
    s.update(clk)
    assert s.point.value == 0.10