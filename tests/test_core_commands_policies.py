# tests/test_core_commands_policies.py
from core.commands import Command, CommandKind, validate_setpoint
from core.policies import dwell_ok, hysteresis_ok, LatchedTrip


def test_validate_setpoint():
    ok = validate_setpoint(5.0, lo=0.0, hi=10.0)
    assert ok.ok
    bad = validate_setpoint(11.0, lo=0.0, hi=0.0)
    assert not bad.ok and bad.code.name == "OUT_OF_RANGE"


def test_dwell_ok():
    # condition stays true for 600ms with 500ms dwell -. okay on second tick
    last = None
    MS = 1.0 / 1000.0
    ok, last = dwell_ok(True, last, now_mono=0.0, dwell_ms=500)
    assert not ok
    ok, last = dwell_ok(True, last, now_mono=600 * MS, dwell_ms=500)
    assert ok


def test_hysteresis_ok():
    # min_on=20, h_up=2, h_down=3
    ok = hysteresis_ok(False, measured=21.9, min_on=20, h_up=2, h_down=3) #below 22 -> still False
    assert not ok
    ok = hysteresis_ok(False, measured=22.0, min_on=20, h_up=2, h_down=3) # at 22 -> True
    assert ok
    #once True, it should stay True down to > 17(20 - 3)
    ok = hysteresis_ok(True, measured=17.5, min_on=20, h_up=2, h_down=3)
    assert ok
    # drop exactly at 17 or below
    ok = hysteresis_ok(True, measured=17.0, min_on=20, h_up=2, h_down=3)
    assert not ok # dropped at <= 17


def test_latched_trip():
    lt = LatchedTrip()
    assert lt.eval(False) is False
    assert lt.eval(True) is True
    assert lt.eval(False) is True #still tripped
    lt.reset()
    assert lt.eval(False) is False