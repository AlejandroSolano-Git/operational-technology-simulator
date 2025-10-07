# tests/test_plant_core.py

from plant.plant_core.state import Lifecycle, MachineState

def test_state_happy_path_cycle():
    lc = Lifecycle()
    #start sequence
    tr1 = lc.request_start(t=1.0);          assert tr1 and lc.state == MachineState.STARTING
    tr2 = lc.confirm_started(t=2.0);          assert tr2 and lc.state == MachineState.RUNNING
    #stop sequence
    tr3 = lc.request_stop(t=3.0);          assert tr3 and lc.state == MachineState.STOPPING
    tr4 = lc.confirm_stopped(t=4.0);          assert tr4 and lc.state == MachineState.STOPPED
    assert lc.cycles == 1
    #timestamps recorded
    assert lc.entered_at == 4.0
    assert lc.last_reason != ""

def test_state_illegal_transitons_noop():
    lc = Lifecycle()
    #Can't confirm_started if not running
    assert lc.confirm_started(t=1.0) is None
    assert lc.state == MachineState.IDLE
    #Can't request_stop from IDLE
    assert lc.request_stop(t=2.0) is None
    assert lc.state == MachineState.IDLE

def test_state_fault_and_clear():
    lc = Lifecycle()
    lc.request_start(t=1.0); lc.confirm_started(t=2.0)
    tr_fault = lc.trip_fault(t=3.0, reason="Over Temp")
    assert tr_fault and lc.state == MachineState.FAULT
    # No effect until cleared
    assert lc.request_start(t=4.0) is None
    tr_clear = lc.clear_fault(t=5.0)
    assert tr_clear and lc.state == MachineState.IDLE
