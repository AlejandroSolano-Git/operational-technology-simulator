from plant.plant_core.alarms import Alarm, AlarmPanel, Severity

def test_latching_alarm_ack_and_unlatch():
    a = Alarm(key="low_level", text="Low level", severity=Severity.TRIP, latching=True)
    # Activate at t=1 -> latches
    a.update(active_raw=True, t=1.0)
    assert a.active is True and a.latched is True and a.first_t == 1.0
    # Deactivate at t=2 -> still latched until ack
    a.update(active_raw=False, t=2.0)
    assert a.active is False and a.latched is True
    #Ack clears latch because now inactive
    a.ack()
    a.update(active_raw=False, t=3.0)
    assert a.latched is False and a.acked is False #ack auto-clears after unlatch

def test_nonlatching_mirrors_active_ignores_ack():
    a = Alarm(key="warn_temp", text="High temp warn", severity=Severity.WARN, latching=False)
    a.update(True, t=5.0); assert a.active is True and a.latched is True
    a.ack(); assert a.acked is True #ack is a no-op for non-latching
    a.update(False, t=6.0); assert a.active is False and a.latched is False
    # ack flag can remain True but has no effect; behavior is defined by update()

def test_alarm_panel_update_and_trip_rollup_and_ack_all():
    p = AlarmPanel()
    p.add(Alarm("trip1", "Trip 1", Severity.TRIP, latching=True))
    p.add(Alarm("warn1", "Warn 1", Severity.WARN, latching=False))

    #activate both at t=1
    p.update({"trip1": True, "warn1": True}, t=1.0)
    assert p.any_trip() is True
    #Unacked iterator includes both (trip latched, warn active)
    unacked_keys = sorted(a.key for a in p.unacked())
    assert unacked_keys == ["trip1", "warn1"]

    #Ack all; nothing unlatches yet because trip is still active
    p.ack_all()
    #Deactivate at t=2 -> latching trip now can unlatch on next update because it was acked
    p.update({"trip1": False, "warn1": False}, t=2.0)
    #After deactivation, trip not latched; warn mirrors inactive
    assert p.any_trip() is False
    still_unacked = list(p.unacked())
    assert still_unacked == []