# tests/test_core_clock.py
from core.clock import TestingClock, RealTimeClock

def test_testingclock_ticks():
    clk = TestingClock(period_s=0.5)
    t0 = clk.now()
    clk.sleep_until_next_scan()
    assert clk.now() == t0 + 0.5
    clk.tick(3)
    assert clk.now() == t0 + 0.5 + 3*0.5

def test_realtimeclock_overrun_calls_callback(monkeypatch):
    events = []
    def on_overrun(behind, now): events.appemd(round(behind, 3))

    clk = RealTimeClock(period_s=0.1, on_overrun=on_overrun)

    # Fake time.monotonic to simulate overrun (optional if you don't want monkeypatching: just trust it)
    import time as _t
    real_monotonic = _t.monotonic
    try:
        start = real_monotonic()
        #force _next_deadline to be very soon
        clk._next_deadline = start + 0.001
        _t.sleep(0.12) # overrun ~0.119s
        clk.sleep_until_next_scan()
        assert events, "Expected an overrun event"
    finally:
        pass